from os import path, makedirs, fsync
from json import load, dump

PROJECT_ROOT = path.abspath(path.join(path.dirname(__file__), ".."))
RESOURCES_DIR = path.join(PROJECT_ROOT, "Resources")

def load_config(config_file):
    config_path = path.join(RESOURCES_DIR, config_file)
    print(config_path)

    if path.exists(config_path):
        try:
            print("Loading config file...")
            with open(config_path, "r", encoding="utf-8") as f:
                data = load(f)
                print(f"Data: {data}")
                return data
        except Exception as e:
            print("Error loading config file:", e)
            return {}
    else:
        print("Config file not found:", config_file)
        return {}

def save_config(data, config_file):
    config_path = path.join(RESOURCES_DIR, config_file)
    makedirs(path.dirname(config_path), exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        dump(data, f, indent=4)
        f.flush()
        fsync(f.fileno())
    print("Config saved at:", config_file)
