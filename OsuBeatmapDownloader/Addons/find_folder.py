import os
import string
from pathlib import Path
from Addons.config import save_config, load_config


def find_folder(folder_name, subfolder_name, os_name, json_index, config_file):
    configuration = load_config(config_file)

    if json_index in configuration:
        print(f"✅ Using saved osu_path from {config_file}")
        return configuration[json_index]

    if os_name == "Windows":
        start_paths = [f"{u}:/" for u in string.ascii_uppercase if os.path.exists(f"{u}:/")]
        print("Detected Windows drives:", start_paths)

    else:
        home = str(Path.home())
        start_paths = [home, "/"]
        print("Scanning:", start_paths)

    for base_path in start_paths:
        for root, dirs, _ in os.walk(base_path):
            if folder_name in dirs:
                parent_path = os.path.join(root, folder_name)
                child_path = os.path.join(parent_path, subfolder_name)

                if os.path.isdir(child_path):
                    print(f"Found folder: {os.path.abspath(parent_path)}")

                    configuration[json_index] = os.path.abspath(parent_path)
                    save_config(configuration, "config.json")
                    return os.path.abspath(parent_path)
    return None
