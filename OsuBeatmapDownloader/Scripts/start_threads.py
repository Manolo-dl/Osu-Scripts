from platform import system

from Addons.find_folder import find_folder

results = {}

def thread_get_folder():
    results["osu_path"] = find_folder(
        "osu!",
        "Songs",
        system(),
        "osu_path",
        "config.json"
    )