from requests import Session
from pathlib import Path
from Utils.osu_utils import extract_id, try_sources

def start_download(osu_session, osu_path, links):
    print("Starting download...")
    if not osu_session or not osu_path or not links:
        raise RuntimeError("Error some arguments are missing to start download.")

    session = Session()
    session.cookies.set("osu_session", osu_session)

    for link in links:
        try:
            beatmap_id = extract_id(link)
            try_sources(session, beatmap_id, Path(osu_path) / "Exports")
        except Exception as e:
            print(f"Error with the start of the download: {e}")