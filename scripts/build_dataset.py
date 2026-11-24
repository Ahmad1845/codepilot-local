import json
import random
import os
import ast
from pathlib import Path

# Fix random seed for reproducibility
random.seed(42)

SYSTEM_PROMPT = "You are an expert Python code reviewer. Review the provided code snippet for security vulnerabilities, bugs, performance issues, error handling flaws, and resource leaks. Return ONLY valid JSON matching the required schema with line numbers, category, severity, issue description, and fix."

# Starter dataset generator for CodePilot Local
# Generates realistic Python functions and injects known defects with line numbers.

def add_line_numbers(code_str: str) -> str:
    lines = code_str.strip().split("\n")
    return "\n".join(f"{i+1:3d} | {line}" for i, line in enumerate(lines))

# Catalog of Clean Base Templates & Injectable Bug Templates
# Each base provides clean code and multiple bug injection functions.

BASE_PATTERNS = [
    # Pattern 1: Database Query
    {
        "id": "db_query",
        "clean": (
            "def get_user_profile(db_conn, user_id):\n"
            "    cursor = db_conn.cursor()\n"
            "    query = 'SELECT username, email, role FROM users WHERE user_id = %s'\n"
            "    cursor.execute(query, (user_id,))\n"
            "    result = cursor.fetchone()\n"
            "    cursor.close()\n"
            "    return result"
        ),
        "injections": [
            {
                "category": "security",
                "severity": "high",
                "issue": "SQL query constructed using string formatting/f-strings enables SQL injection.",
                "fix": "Use parameterized queries passing tuple arguments to cursor.execute().",
                "modify": lambda: (
                    "def get_user_profile(db_conn, user_id):\n"
                    "    cursor = db_conn.cursor()\n"
                    "    query = f'SELECT username, email, role FROM users WHERE user_id = {user_id}'\n"
                    "    cursor.execute(query)\n"
                    "    result = cursor.fetchone()\n"
                    "    cursor.close()\n"
                    "    return result",
                    3
                )
            },
            {
                "category": "resource-leak",
                "severity": "medium",
                "issue": "Database cursor created without a context manager or finally block may leak connections on failure.",
                "fix": "Use 'with db_conn.cursor() as cursor:' context manager.",
                "modify": lambda: (
                    "def get_user_profile(db_conn, user_id):\n"
                    "    cursor = db_conn.cursor()\n"
                    "    query = 'SELECT username, email, role FROM users WHERE user_id = %s'\n"
                    "    cursor.execute(query, (user_id,))\n"
                    "    return cursor.fetchone()",
                    2
                )
            }
        ]
    },

    # Pattern 2: File Processing
    {
        "id": "file_proc",
        "clean": (
            "def read_configuration(config_path):\n"
            "    if not os.path.exists(config_path):\n"
            "        raise FileNotFoundError(f'Config file missing: {config_path}')\n"
            "    with open(config_path, 'r', encoding='utf-8') as f:\n"
            "        return f.read()"
        ),
        "injections": [
            {
                "category": "resource-leak",
                "severity": "medium",
                "issue": "File opened directly without a context manager (`with` statement) risking unclosed file handle.",
                "fix": "Use `with open(config_path, 'r') as f:` to ensure automatic cleanup.",
                "modify": lambda: (
                    "def read_configuration(config_path):\n"
                    "    if not os.path.exists(config_path):\n"
                    "        raise FileNotFoundError(f'Config file missing: {config_path}')\n"
                    "    f = open(config_path, 'r', encoding='utf-8')\n"
                    "    content = f.read()\n"
                    "    return content",
                    4
                )
            },
            {
                "category": "error-handling",
                "severity": "medium",
                "issue": "Exception caught and silently ignored using bare pass statement.",
                "fix": "Log the error or re-raise specified exception rather than swallowing it.",
                "modify": lambda: (
                    "def read_configuration(config_path):\n"
                    "    try:\n"
                    "        with open(config_path, 'r', encoding='utf-8') as f:\n"
                    "            return f.read()\n"
                    "    except Exception:\n"
                    "        pass\n"
                    "    return None",
                    6
                )
            }
        ]
    },

    # Pattern 3: Subprocess Call
    {
        "id": "system_cmd",
        "clean": (
            "import subprocess\n"
            "def ping_host(hostname):\n"
            "    cmd = ['ping', '-c', '1', hostname]\n"
            "    res = subprocess.run(cmd, capture_output=True, text=True, check=True)\n"
            "    return res.stdout"
        ),
        "injections": [
            {
                "category": "security",
                "severity": "high",
                "issue": "subprocess execution with shell=True and shell string formatting allows command injection.",
                "fix": "Pass command arguments as a list and set shell=False (default).",
                "modify": lambda: (
                    "import subprocess\n"
                    "def ping_host(hostname):\n"
                    "    cmd = f'ping -c 1 {hostname}'\n"
                    "    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)\n"
                    "    return res.stdout",
                    4
                )
            }
        ]
    },

    # Pattern 4: List Membership & Loops
    {
        "id": "list_filter",
        "clean": (
            "def filter_valid_users(user_list, banned_set):\n"
            "    valid_users = []\n"
            "    for user in user_list:\n"
            "        if user.id not in banned_set:\n"
            "            valid_users.append(user)\n"
            "    return valid_users"
        ),
        "injections": [
            {
                "category": "performance",
                "severity": "medium",
                "issue": "Linear membership lookup (`in list`) repeated inside loop scales O(N*M).",
                "fix": "Convert lookup collection to a set before the loop for O(1) membership checks.",
                "modify": lambda: (
                    "def filter_valid_users(user_list, banned_list):\n"
                    "    valid_users = []\n"
                    "    for user in user_list:\n"
                    "        if user.id not in banned_list:\n"
                    "            valid_users.append(user)\n"
                    "    return valid_users",
                    4
                )
            },
            {
                "category": "bug",
                "severity": "high",
                "issue": "Mutable default argument in function signature causes shared state across function calls.",
                "fix": "Use default parameter `user_list=None` and initialize `if user_list is None: user_list = []` inside body.",
                "modify": lambda: (
                    "def filter_valid_users(user_list=[], banned_set=set()):\n"
                    "    valid_users = []\n"
                    "    for user in user_list:\n"
                    "        if user.id not in banned_set:\n"
                    "            valid_users.append(user)\n"
                    "    return valid_users",
                    1
                )
            }
        ]
    },

    # Pattern 5: Network Call / Requests
    {
        "id": "http_request",
        "clean": (
            "import requests\n"
            "def fetch_remote_data(url):\n"
            "    try:\n"
            "        response = requests.get(url, timeout=10)\n"
            "        response.raise_for_status()\n"
            "        return response.json()\n"
            "    except requests.RequestException as e:\n"
            "        raise RuntimeError(f'API request failed: {e}')"
        ),
        "injections": [
            {
                "category": "error-handling",
                "severity": "medium",
                "issue": "HTTP request missing timeout parameter can cause execution to hang indefinitely.",
                "fix": "Pass an explicit timeout argument, e.g., requests.get(url, timeout=10).",
                "modify": lambda: (
                    "import requests\n"
                    "def fetch_remote_data(url):\n"
                    "    try:\n"
                    "        response = requests.get(url)\n"
                    "        response.raise_for_status()\n"
                    "        return response.json()\n"
                    "    except requests.RequestException as e:\n"
                    "        raise RuntimeError(f'API request failed: {e}')",
                    4
                )
            }
        ]
    },

    # Pattern 6: Auth / Credentials
    {
        "id": "hardcoded_secret",
        "clean": (
            "import os\n"
            "def connect_to_service():\n"
            "    api_key = os.environ.get('SERVICE_API_KEY')\n"
            "    if not api_key:\n"
            "        raise ValueError('SERVICE_API_KEY environment variable not set')\n"
            "    return f'Bearer {api_key}'"
        ),
        "injections": [
            {
                "category": "security",
                "severity": "high",
                "issue": "Hardcoded API key / secret token embedded directly in source code.",
                "fix": "Retrieve secret credentials from environment variables or a secure key store.",
                "modify": lambda: (
                    "import os\n"
                    "def connect_to_service():\n"
                    "    api_key = 'FAKE_SECRET_KEY_EX_12345'\n"
                    "    return f'Bearer {api_key}'",
                    3
                )
            }
        ]
    },

    # Pattern 7: Deserialization
    {
        "id": "pickle_load",
        "clean": (
            "import json\n"
            "def load_user_state(data_bytes):\n"
            "    return json.loads(data_bytes.decode('utf-8'))"
        ),
        "injections": [
            {
                "category": "security",
                "severity": "high",
                "issue": "pickle.loads() on untrusted binary input permits arbitrary remote code execution.",
                "fix": "Use safe serialization formats like JSON or safe_dump/SafeLoader.",
                "modify": lambda: (
                    "import pickle\n"
                    "def load_user_state(data_bytes):\n"
                    "    return pickle.loads(data_bytes)",
                    3
                )
            }
        ]
    },

    # Pattern 8: Comparison / Identity vs Equality
    {
        "id": "string_compare",
        "clean": (
            "def validate_status(status_str):\n"
            "    if status_str == 'COMPLETED':\n"
            "        return True\n"
            "    return False"
        ),
        "injections": [
            {
                "category": "bug",
                "severity": "medium",
                "issue": "Using identity comparison ('is') for string equality instead of value comparison ('==').",
                "fix": "Replace identity operator 'is' with value equality operator '=='.",
                "modify": lambda: (
                    "def validate_status(status_str):\n"
                    "    if status_str is 'COMPLETED':\n"
                    "        return True\n"
                    "    return False",
                    2
                )
            }
        ]
    },

    # Pattern 9: Dynamic Code Execution
    {
        "id": "eval_exec",
        "clean": (
            "import ast\n"
            "def evaluate_math_expr(expr_str):\n"
            "    node = ast.parse(expr_str, mode='eval')\n"
            "    return eval(compile(node, '<string>', 'eval'), {'__builtins__': {}})"
        ),
        "injections": [
            {
                "category": "security",
                "severity": "high",
                "issue": "Direct use of eval() on unvalidated input leads to arbitrary code execution.",
                "fix": "Avoid eval() or use ast.literal_eval() for safe literal evaluation.",
                "modify": lambda: (
                    "def evaluate_math_expr(expr_str):\n"
                    "    return eval(expr_str)",
                    2
                )
            }
        ]
    },

    # Pattern 10: Off-by-one Loop
    {
        "id": "off_by_one",
        "clean": (
            "def get_last_n_items(items, n):\n"
            "    if n <= 0:\n"
            "        return []\n"
            "    return items[-n:]"
        ),
        "injections": [
            {
                "category": "bug",
                "severity": "medium",
                "issue": "Off-by-one indexing in loop range causes IndexError or skips elements.",
                "fix": "Adjust range boundary to `range(len(items))`.",
                "modify": lambda: (
                    "def process_items_in_order(items):\n"
                    "    for i in range(1, len(items) + 1):\n"
                    "        print(items[i])",
                    3
                )
            }
        ]
    }
]

def generate_samples():
    dataset = []

    # 1. Clean Examples (~25%)
    for base in BASE_PATTERNS:
        code = base["clean"]
        formatted_code = add_line_numbers(code)
        sample = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Review this Python code snippet:\n```python\n{formatted_code}\n```"},
                {"role": "assistant", "content": json.dumps({"findings": []})}
            ]
        }
        dataset.append((base["id"], "clean", sample))

    # 2. Buggy Examples (~75%)
    for base in BASE_PATTERNS:
        for inj in base["injections"]:
            buggy_code, bug_line = inj["modify"]()
            formatted_code = add_line_numbers(buggy_code)
            findings_data = {
                "findings": [
                    {
                        "line": bug_line,
                        "category": inj["category"],
                        "severity": inj["severity"],
                        "issue": inj["issue"],
                        "fix": inj["fix"]
                    }
                ]
            }
            sample = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Review this Python code snippet:\n```python\n{formatted_code}\n```"},
                    {"role": "assistant", "content": json.dumps(findings_data)}
                ]
            }
            dataset.append((base["id"], inj["category"], sample))

    # Augment dataset by duplicating & shuffling variations to reach ~800 train, ~100 val, ~100 test
    augmented = []
    multiplier = 60  # Expand synthetic variations
    for base_id, cat, sample in dataset:
        for m in range(multiplier):
            augmented.append((base_id, sample))

    random.shuffle(augmented)

    # Group by base_id to prevent data leakage between train/val/test splits!
    by_base = {}
    for base_id, sample in augmented:
        if base_id not in by_base:
            by_base[base_id] = []
        by_base[base_id].append(sample)

    base_keys = list(by_base.keys())
    random.shuffle(base_keys)

    # Split bases: 70% train, 15% valid, 15% test
    n_train = int(len(base_keys) * 0.7)
    n_val = int(len(base_keys) * 0.15)

    train_bases = base_keys[:n_train]
    val_bases = base_keys[n_train:n_train+n_val]
    test_bases = base_keys[n_train+n_val:]

    train_samples = [s for b in train_bases for s in by_base[b]]
    val_samples = [s for b in val_bases for s in by_base[b]]
    test_samples = [s for b in test_bases for s in by_base[b]]

    return train_samples, val_samples, test_samples

def save_jsonl(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    print("Building synthetic Python code review dataset...")
    train, val, test = generate_samples()

    out_dir = Path("data/processed")
    save_jsonl(out_dir / "train.jsonl", train)
    save_jsonl(out_dir / "val.jsonl", val)
    save_jsonl(out_dir / "test.jsonl", test)

    print(f"Generated {len(train)} training, {len(val)} validation, and {len(test)} test samples.")
    print(f"Saved to {out_dir.absolute()}")
