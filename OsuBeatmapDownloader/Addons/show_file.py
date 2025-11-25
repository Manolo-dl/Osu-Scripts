import os
from shutil import which
from subprocess import Popen, run

def show_file(path, os_name):
    path = os.path.abspath(path)

    match os_name:
        case "Windows":
            if os.path.isfile(path):
                run(["explorer", "/select,", path.replace("/", "\\")])
            else:
                run(["explorer", path.replace("/", "\\")])
        case "Darwin":
            if os.path.isfile(path):
                run(["open", "-R", path])
            else:
                run(["open", path])
        case "Linux":
            file_managers = [
                ("nautilus", ["nautilus", "--select"]),
                ("nemo", ["nemo", "--select"]),
                ("dolphin", ["dolphin", "--select"]),
                ("thunar", ["thunar"]),
            ]

            if os.path.isfile(path):
                for fm, cmd in file_managers:
                    if which(fm):
                        if "--select" in cmd:
                            Popen(cmd + [path])
                        else:
                            Popen([fm, os.path.dirname(path)])
                    return
                Popen(["xdg-open", os.path.dirname(path)])
            else:
                Popen(["xdg-open", path])
        case _:
            raise RuntimeError(f"Unsupported OS: {os_name}")