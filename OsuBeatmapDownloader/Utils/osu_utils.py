from time import sleep
from re import search
from requests.utils import unquote_header_value
from zipfile import is_zipfile

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Referer": "https://osu.ppy.sh/"
}

def extract_id(link):
    link = link.strip()
    if not link:
        raise ValueError("Empty link.")
    if m := search(r"/beatmapsets/(\d+)", link):
        return m.group(1)
    raise ValueError(f"Could not extract beatmapset_id from: {link}")


def get_filename(header):
    if not header:
        raise ValueError("Empty header.")
    if m := search(r"filename\*=.*''(?P<f>[^;\r\n]+)", header):
        return unquote_header_value(m.group("f"))
    if m := search(r'filename="?([^";]+)"?', header):
        return m.group(1)
    return None


def download_songs(session, url, out_path):
    attempt = 0
    wait = 1.0
    final_path = None
    max_retries = 3

    while attempt < max_retries:
        attempt += 1

        try:
            with session.get(url, headers=DEFAULT_HEADERS, stream=True, allow_redirects=True, timeout=30) as res:
                if res.status_code != 200:
                    raise RuntimeError(f"HTTP {res.status_code} while requesting {url}")

                cd = res.headers.get("content-disposition") or res.headers.get("Content-Disposition")
                filename = get_filename(cd)

                if filename:
                    out_path = out_path.with_name(filename)

                tmp_path = out_path.with_suffix(out_path.suffix + ".downloading")
                downloaded = 0

                with open(tmp_path, "wb") as f:
                    for chunk in res.iter_content(8192):  # 8192 <- CHUNK_SIZE
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                tmp_path.replace(out_path)
                final_path = out_path
                break
        except Exception as e:
            print(f"\n  - Attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                sleep(wait)
                wait *= 1.5  # <- BACKOFF_FACTOR

    if not final_path:
        raise RuntimeError(f"All retries failed for: {url}")

    return final_path


def try_sources(session, beatmap_id, output_folder):
    url = f"https://osu.ppy.sh/beatmapsets/{beatmap_id}/download"

    try:
        try:
            head = session.head(url, headers=DEFAULT_HEADERS, allow_redirects=True, timeout=15)
        except Exception as e:
            print(f"HEAD request error: {e}")
            head = None

        if head and head.status_code == 200:
            name = get_filename(head.headers.get("content-disposition") or head.headers.get("Content-Disposition"))
        else:
            name = f"{beatmap_id}.osz"

        out_path = output_folder / name
        final_path = download_songs(session, url, out_path)

        if is_zipfile(final_path):
            print(f"✔ {final_path.name} downloaded successfully")
            return final_path
        else:
            final_path.unlink(missing_ok=True)
            raise RuntimeError("Invalid ZIP file")
    except Exception as e:
        raise RuntimeError(f"Could not download a valid .osz for {beatmap_id}: {e}")
