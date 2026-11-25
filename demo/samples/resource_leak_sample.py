def load_config_file(filepath):
    try:
        f = open(filepath, 'r')
        data = f.read()
        return data
    except Exception:
        pass
    return None
