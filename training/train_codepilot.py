# CodePilot Local: Unsloth QLoRA Fine-tuning Script for Qwen2.5-Coder-1.5B-Instruct
# Designed for Google Colab (T4 GPU) or Kaggle GPU

import os
import sys
import torch
from pathlib import Path
from unsloth import FastLanguageModel
from trl import SFTTrainer, SFTConfig
from datasets import Dataset
import json

MODEL_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
MAX_SEQ_LENGTH = 1024
LORA_RANK = 16
LORA_ALPHA = 32
LEARNING_RATE = 2e-4
EPOCHS = 3
BATCH_SIZE = 2
GRAD_ACCUM = 4

def load_data(file_path):
    rows = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def main():
    print(f"Loading model {MODEL_ID} in 4-bit QLoRA...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_ID,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=True,
    )

    # Attach LoRA adapters
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_ALPHA,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )
    model.print_trainable_parameters()

    # Apply chat template
    prefix = '{% set enable_thinking = false %}\n'
    if isinstance(tokenizer.chat_template, str) and not tokenizer.chat_template.startswith(prefix):
        tokenizer.chat_template = prefix + tokenizer.chat_template

    # Load dataset splits
    train_raw = load_data("data/processed/train.jsonl")
    val_raw = load_data("data/processed/val.jsonl")

    def render_chat(example):
        return {"text": tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False, enable_thinking=False)}

    train_ds = Dataset.from_list(train_raw).map(render_chat, remove_columns=["messages"])
    val_ds = Dataset.from_list(val_raw).map(render_chat, remove_columns=["messages"])

    output_dir = Path("outputs/codepilot-1.5b-adapter")
    output_dir.mkdir(parents=True, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        args=SFTConfig(
            output_dir=str(output_dir),
            dataset_text_field="text",
            max_seq_length=MAX_SEQ_LENGTH,
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            learning_rate=LEARNING_RATE,
            num_train_epochs=EPOCHS,
            warmup_ratio=0.05,
            optim="adamw_8bit",
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=10,
            save_strategy="epoch",
            eval_strategy="epoch",
            report_to="none",
            seed=3407
        ),
    )

    print("Starting fine-tuning...")
    trainer.train()

    # Save adapter
    print(f"Saving LoRA adapter to {output_dir}")
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    # Export GGUF
    gguf_dir = Path("outputs/codepilot-1.5b-gguf")
    print(f"Exporting Q4_K_M GGUF to {gguf_dir}...")
    model.save_pretrained_gguf(str(gguf_dir), tokenizer, quantization_method="q4_k_m")
    print("Fine-tuning and export complete!")

if __name__ == "__main__":
    from unsloth import is_bfloat16_supported
    main()
