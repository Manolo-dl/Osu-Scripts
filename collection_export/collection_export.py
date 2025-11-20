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

# -------------------- MD5 FUNCTIONS --------------------

def md5_file(path):
    """Return MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_osu_files_map(songs_folder):
    """Return list of all .osu files with their absolute paths"""
    osu_files = []
    for root, dirs, files in os.walk(songs_folder):
        for file in files:
            if file.endswith(".osu"):
                osu_files.append(os.path.join(root, file))
    return osu_files

# -------------------- EXPORT FUNCTION --------------------

def export_selected_collections(selected_indices, collections, songs_folder):
    folder = filedialog.askdirectory(title="Select output folder")
    if not folder:
        return

    # Get list of all .osu files in Songs folder
    osu_files = find_osu_files_map(songs_folder)

    for i in selected_indices:
        name, md5_list = collections[i]
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        out_path = os.path.join(folder, f"{safe_name}.txt")

        with open(out_path, "w", encoding="utf-8") as f:
            for md5 in md5_list:
                found = False
                for osu_file in osu_files:
                    try:
                        if md5_file(osu_file) == md5:
                            f.write(f"file://{osu_file}\n")
                            found = True
                            break
                    except:
                        continue
                if not found:
                    f.write(f"# Not found locally: {md5}\n")

    messagebox.showinfo("Done", f"Exported {len(selected_indices)} collections to {folder}")

# -------------------- GUI --------------------

class OsuCollectionExporter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("osu! Collection Exporter (Offline)")
        self.root.geometry("500x500")

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
        export_selected_collections(selected, self.collections, self.songs_folder)

# -------------------- MAIN --------------------

if __name__ == "__main__":
    OsuCollectionExporter()
