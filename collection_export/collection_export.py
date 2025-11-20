import struct
import os
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# -------------------- COLLECTION.DB FUNCTIONS --------------------

def read_7bit_int(f):
    result = 0
    shift = 0
    while True:
        b = f.read(1)
        if not b:
            break
        b = b[0]
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result

def read_osu_string(f):
    start = f.read(1)
    if start == b'\x00':
        return ""
    if start != b'\x0b':
        raise ValueError("Invalid string format")
    length = read_7bit_int(f)
    return f.read(length).decode("utf-8", errors="replace")

def load_collection_db(path):
    with open(path, "rb") as f:
        version = struct.unpack("<i", f.read(4))[0]
        collection_count = struct.unpack("<i", f.read(4))[0]

        collections = []
        for _ in range(collection_count):
            name = read_osu_string(f)
            beatmap_count = struct.unpack("<i", f.read(4))[0]
            beatmaps = [read_osu_string(f) for _ in range(beatmap_count)]
            collections.append((name, beatmaps))
    return collections

# -------------------- OSU FILE PARSING --------------------

MODE_MAP = {0: "osu", 1: "taiko", 2: "fruits", 3: "mania"}

def parse_osu_file(osu_file):
    beatmap_id = None
    mode = None
    with open(osu_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("BeatmapID:"):
                beatmap_id = line.split(":")[1].strip()
            if line.startswith("Mode:"):
                mode_num = int(line.split(":")[1].strip())
                mode = MODE_MAP.get(mode_num, "osu")
            if beatmap_id and mode is not None:
                break
    return beatmap_id, mode

def md5_file(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# -------------------- EXPORT FUNCTION --------------------

def export_selected_collections(selected_indices, collections, songs_folder, progress_var, root, listbox):
    total_collections = len(selected_indices)
    exported_count = 0
    total_missing = 0

    folder = filedialog.askdirectory(title="Select output folder")
    if not folder:
        return

    for idx, i in enumerate(selected_indices):
        name, md5_list = collections[i]
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        out_path = os.path.join(folder, f"{safe_name}.txt")

        md5_set = set(md5_list)
        beatmapset_links = {}

        # Walk Songs folder to find MD5 matches
        for root_dir, dirs, files in os.walk(songs_folder):
            folder_name = os.path.basename(root_dir)
            if not folder_name or not folder_name[0].isdigit():
                continue
            beatmapset_id = folder_name.split(" ")[0]

            for file in files:
                if not file.endswith(".osu"):
                    continue
                osu_path = os.path.join(root_dir, file)
                try:
                    file_md5 = md5_file(osu_path)
                except:
                    continue

                if file_md5 in md5_set and beatmapset_id not in beatmapset_links:
                    beatmap_id, mode = parse_osu_file(osu_path)
                    if beatmap_id and mode:
                        link = f"https://osu.ppy.sh/beatmapsets/{beatmapset_id}#{mode}/{beatmap_id}"
                        beatmapset_links[beatmapset_id] = link

            # Remove found MD5s from the set
            md5_set -= set(beatmapset_links.keys())
            if not md5_set:
                break

        # Write only actual links
        with open(out_path, "w", encoding="utf-8") as f:
            for link in beatmapset_links.values():
                f.write(link + "\n")

        # Count missing songs
        missing_count = len(md5_list) - len(beatmapset_links)
        total_missing += missing_count

        exported_count += 1
        progress_var.set(int((idx + 1) / total_collections * 100))
        root.update_idletasks()

    # Clear selection using the passed Listbox
    listbox.selection_clear(0, tk.END)

    messagebox.showinfo(
        "Export Complete",
        f"Exported {exported_count} collections.\nTotal missing songs: {total_missing}"
    )

# -------------------- GUI --------------------

class OsuCollectionExporter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("osu! Collection Exporter (Offline)")
        self.root.geometry("550x550")

        self.collections = []
        self.songs_folder = ""
        self.collection_path = ""

        self.create_widgets()
        self.root.mainloop()

    def create_widgets(self):
        tk.Label(self.root, text="Step 1: Select your osu! folder").pack(pady=5)
        tk.Button(self.root, text="Select osu! Folder", command=self.select_osu_folder).pack(pady=5)

        tk.Label(self.root, text="Step 2: Select collections to export").pack(pady=10)

        self.frame = tk.Frame(self.root)
        self.frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(self.frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(self.frame, selectmode=tk.MULTIPLE, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        tk.Label(self.root, text="Export progress:").pack(pady=5)
        self.progress_var = tk.IntVar()
        self.progressbar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progressbar.pack(fill=tk.X, padx=20, pady=5)

        tk.Button(self.root, text="Export Selected Collections", command=self.export_collections).pack(pady=10)

    def select_osu_folder(self):
        osu_folder = filedialog.askdirectory(title="Select your osu! folder")
        if not osu_folder:
            return

        collection_path = os.path.join(osu_folder, "collection.db")
        songs_folder = os.path.join(osu_folder, "Songs")

        if not os.path.exists(collection_path):
            messagebox.showerror("Error", f"No collection.db found in {osu_folder}")
            return
        if not os.path.exists(songs_folder):
            messagebox.showerror("Error", f"No Songs folder found in {osu_folder}")
            return

        self.songs_folder = songs_folder
        self.collection_path = collection_path
        self.collections = load_collection_db(collection_path)
        self.populate_listbox()

    def populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for name, beatmaps in self.collections:
            self.listbox.insert(tk.END, f"{name} ({len(beatmaps)} maps)")

    def export_collections(self):
        selected = self.listbox.curselection()
        if not selected:
            messagebox.showwarning("No selection", "Please select at least one collection")
            return
        export_selected_collections(
            selected, self.collections, self.songs_folder, self.progress_var, self.root, self.listbox
        )

# -------------------- MAIN --------------------

if __name__ == "__main__":
    OsuCollectionExporter()
