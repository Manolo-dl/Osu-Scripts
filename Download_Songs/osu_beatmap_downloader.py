#!/usr/bin/env python3
"""
osu_beatmap_downloader_gui_final.py
Three-step GUI workflow:
1. Select links file
2. Select download folder
3. Login with SeleniumBase (only if needed) and download
Features:
- Saves download folder and osu_session in JSON for next run
- Step 3 disabled until previous steps are completed
- Dashboard shows only final beatmap names
- Counter matches total beatmaps
"""

import os
import re
import time
import json
import requests
import zipfile
from pathlib import Path
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

CONFIG_FILE = "osu_downloader_config.json"
CHUNK_SIZE = 8192
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Referer": "https://osu.ppy.sh/"
}


# ---------------------------
# Config utils
# ---------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ---------------------------
# SeleniumBase login
# ---------------------------
def get_osu_session():
    config = load_config()
    if "osu_session" in config:
        print("✅ Using saved osu_session from config.")
        return config["osu_session"]

    driver = Driver(uc=True)
    url = "https://osu.ppy.sh/"
    driver.uc_open_with_reconnect(url, 4)
    print("\n🔵 Please log in manually in the opened browser.")
    print("🔵 Complete Cloudflare, CAPTCHA, 2FA, etc.\n")

    try:
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a.js-current-user-avatar.js-user-login--menu")
            )
        )
        print("✅ Avatar detected! Login complete.")
    except Exception:
        print("⚠ Timeout waiting for avatar element.")

    cookies = driver.get_cookies()
    osu_session = None
    for c in cookies:
        if c['name'] == 'osu_session':
            osu_session = c['value']
            break
    driver.quit()
    if osu_session:
        print("\n✅ osu_session cookie found. Saving to config...")
        config["osu_session"] = osu_session
        if hasattr(MainApp, "download_folder") and MainApp.download_folder:
            config["download_folder"] = str(MainApp.download_folder)
        save_config(config)
        return osu_session
    else:
        print("\n❌ osu_session cookie NOT found.")
        return None


# ---------------------------
# Dashboard
# ---------------------------
class DownloadDashboard:
    def __init__(self, total_count):
        self.root = tk.Tk()
        self.root.title("osu! Beatmap Downloader")
        self.root.geometry("550x350")
        self.root.attributes("-topmost", True)

        self.label = tk.Label(self.root, text="Waiting to start...", wraplength=520, font=("Arial", 12, "bold"))
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, length=500)
        self.progress.pack(pady=10)

        self.status = tk.Text(self.root, height=12, width=65, font=("Arial", 10))
        self.status.pack(pady=10)
        self.status.config(state=tk.DISABLED)

        self.total_count = total_count
        self.current_index = 0
        self.lock = threading.Lock()

    def update_download(self, beatmap_name, percent):
        with self.lock:
            self.label.config(text=f"Downloading: {beatmap_name}")
            self.progress['value'] = percent
            self.root.update_idletasks()

    def add_completed(self, beatmap_name):
        with self.lock:
            self.current_index += 1
            self.status.config(state=tk.NORMAL)
            self.status.insert(tk.END, f"{self.current_index}/{self.total_count} ✔ {beatmap_name}\n")
            self.status.see(tk.END)
            self.status.config(state=tk.DISABLED)
            self.progress['value'] = 0
            self.root.update_idletasks()

    def finish(self):
        with self.lock:
            self.label.config(text="All downloads completed!")
            self.progress['value'] = 100
            self.root.update_idletasks()
            messagebox.showinfo("Download Complete", "All beatmaps have been downloaded successfully!")


# ---------------------------
# Utils
# ---------------------------
def extract_id(link):
    link = link.strip()
    if not link:
        raise ValueError("Empty link.")
    if link.isdigit():
        return link
    if "beatconnect.io" in link:
        return link.rstrip("/").split("/")[-1]
    m = re.search(r"/beatmapsets/(\d+)", link)
    if m:
        return m.group(1)
    m2 = re.search(r"/b/(\d+)", link)
    if m2:
        return m2.group(1)
    raise ValueError(f"Could not extract beatmapset_id from: {link}")


def filename_from_cd(header):
    if not header:
        return None
    m = re.search(r"filename\*=.*''(?P<f>[^;\r\n]+)", header)
    if m:
        return requests.utils.unquote(m.group("f"))
    m2 = re.search(r'filename="?([^";]+)"?', header)
    if m2:
        return m2.group(1)
    return None


def is_valid_zip(path):
    try:
        return zipfile.is_zipfile(path)
    except Exception:
        return False


def download_with_progress(session, url, out_path, gui_window=None):
    attempt = 0
    wait = 1.0
    final_path = None
    while attempt < MAX_RETRIES:
        attempt += 1
        try:
            with session.get(url, headers=DEFAULT_HEADERS, stream=True, allow_redirects=True, timeout=30) as resp:
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code} while requesting {url}")

                cd = resp.headers.get("content-disposition") or resp.headers.get("Content-Disposition")
                server_name = filename_from_cd(cd)
                if server_name:
                    out_path = out_path.with_name(server_name)

                tmp_path = out_path.with_suffix(out_path.suffix + ".downloading")
                total_size = int(resp.headers.get('Content-Length', 0))
                downloaded = 0

                with open(tmp_path, "wb") as f:
                    for chunk in resp.iter_content(CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size and gui_window:
                                percent = downloaded / total_size * 100
                                gui_window.root.after(0, gui_window.update_download, out_path.name, percent)

                tmp_path.replace(out_path)
                final_path = out_path
                break
        except Exception as e:
            print(f"\n  - Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(wait)
                wait *= BACKOFF_FACTOR

    if not final_path:
        raise RuntimeError(f"All retries failed for: {url}")

    return final_path


def try_sources(session, beatmap_id, output_folder, gui_window=None):
    sources = [
        f"https://beatconnect.io/b/{beatmap_id}",
        f"https://osu.ppy.sh/beatmapsets/{beatmap_id}/download"
    ]
    last_error = None
    for url in sources:
        try:
            head = None
            try:
                head = session.head(url, headers=DEFAULT_HEADERS, allow_redirects=True, timeout=15)
            except Exception:
                head = None
            name = None
            if head and head.status_code == 200:
                name = filename_from_cd(head.headers.get("content-disposition") or head.headers.get("Content-Disposition"))
            name = name or f"{beatmap_id}.osz"
            out_path = output_folder / name

            final_path = download_with_progress(session, url, out_path, gui_window)
            if is_valid_zip(final_path):
                print(f"✔ {final_path.name} downloaded successfully")
                if gui_window:
                    gui_window.root.after(0, gui_window.add_completed, final_path.name)
                return final_path
            else:
                final_path.unlink(missing_ok=True)
                last_error = RuntimeError("Invalid ZIP file")
        except Exception as e:
            last_error = e
    raise RuntimeError(f"Could not download a valid .osz for {beatmap_id}: {last_error}")


# ---------------------------
# Main GUI
# ---------------------------
class MainApp:
    download_folder = None  # class-level reference for config saving

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("osu! Downloader Setup")
        self.root.geometry("500x300")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.links_file = None
        self.download_folder = None
        self.osu_cookie = None

        big_font = ("Arial", 12, "bold")

        # Load saved config
        config = load_config()
        if "download_folder" in config:
            self.download_folder = Path(config["download_folder"])
            MainApp.download_folder = self.download_folder

        self.label_file = tk.Label(self.root, text="Step 1: Select links file", font=big_font)
        self.label_file.pack(pady=10)
        self.btn_file = tk.Button(self.root, text="Select File", command=self.select_file)
        self.btn_file.pack(pady=5)

        self.label_folder = tk.Label(self.root, text=f"Folder: {self.download_folder}" if self.download_folder else "Step 2: Select download folder", font=big_font)
        self.label_folder.pack(pady=10)
        self.btn_folder = tk.Button(self.root, text="Select Folder", command=self.select_folder)
        self.btn_folder.pack(pady=5)

        self.label_login = tk.Label(self.root, text="Step 3: Login and start download", font=big_font)
        self.label_login.pack(pady=10)
        self.btn_login = tk.Button(self.root, text="Login & Start", command=self.start_download)
        self.btn_login.pack(pady=5)
        self.btn_login.config(state=tk.DISABLED)

        self.update_login_button_state()

    def select_file(self):
        path = filedialog.askopenfilename(title="Select links file", filetypes=[("Text files", "*.txt")])
        if path:
            self.links_file = path
            self.label_file.config(text=f"File: {os.path.basename(path)}")
        self.update_login_button_state()

    def select_folder(self):
        path = filedialog.askdirectory(title="Select download folder")
        if path:
            self.download_folder = Path(path)
            MainApp.download_folder = self.download_folder
            self.label_folder.config(text=f"Folder: {path}")
        self.update_login_button_state()

    def update_login_button_state(self):
        if self.links_file and self.download_folder:
            self.btn_login.config(state=tk.NORMAL)
        else:
            self.btn_login.config(state=tk.DISABLED)

    def start_download(self):
        self.root.destroy()

        # Save folder to config before login
        config = load_config()
        if self.download_folder:
            config["download_folder"] = str(self.download_folder)
            save_config(config)

        self.osu_cookie = get_osu_session()
        if not self.osu_cookie:
            messagebox.showerror("Error", "Could not obtain osu_session cookie.")
            return

        with open(self.links_file, "r", encoding="utf-8") as f:
            links = [l.strip() for l in f if l.strip()]
        dashboard = DownloadDashboard(total_count=len(links))

        session = requests.Session()
        session.cookies.set("osu_session", self.osu_cookie)

        def download_all():
            for link in links:
                print(f"\n➡ Processing: {link}")
                try:
                    beatmap_id = extract_id(link)
                    try_sources(session, beatmap_id, self.download_folder, dashboard)
                except Exception as e:
                    print(f"✖ Error: {e}")
            dashboard.root.after(0, dashboard.finish)

        threading.Thread(target=download_all, daemon=True).start()
        dashboard.root.mainloop()


if __name__ == "__main__":
    app = MainApp()
    app.root.mainloop()
