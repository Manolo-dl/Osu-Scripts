import struct
import os
import tkinter as tk
from tkinter import filedialog, messagebox

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

# -------------------- EXPORT FUNCTION --------------------

def export_collections(selected_indices, collections):
    folder = filedialog.askdirectory(title="Select output folder")
    if not folder:
        return

    for i in selected_indices:
        name, md5_list = collections[i]
        safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
        out_path = os.path.join(folder, f"{safe_name}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            for md5 in md5_list:
                f.write(md5 + "\n")
    messagebox.showinfo("Done", f"Exported {len(selected_indices)} collections to {folder}")

# -------------------- GUI --------------------

def main_gui(collections):
    root = tk.Tk()
    root.title("osu! Collection Exporter (Offline)")
    root.geometry("500x500")

    tk.Label(root, text="Select collections to export:").pack(padx=10, pady=10)

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set)
    for name, beatmaps in collections:
        listbox.insert(tk.END, f"{name} ({len(beatmaps)} maps)")
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    def on_export():
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("No selection", "Please select at least one collection")
            return
        export_collections(selected, collections)

    tk.Button(root, text="Export Selected", command=on_export).pack(pady=10)

    root.mainloop()

# -------------------- INITIAL INSTRUCTION WINDOW --------------------

def instruction_window():
    win = tk.Tk()
    win.title("osu! Collection Exporter Instructions")
    win.geometry("400x200")

    instruction_text = (
        "Welcome to the osu! Collection Exporter (Offline).\n\n"
        "Instructions:\n"
        "1. Click 'Select osu! Folder' to choose your osu! installation folder.\n"
        "2. The program will read your collections.\n"
        "3. Select which collections you want to export.\n"
        "4. Export will generate .txt files containing MD5s of the beatmaps."
    )

    tk.Label(win, text=instruction_text, justify="left", wraplength=380).pack(padx=10, pady=20)

    def on_continue():
        win.destroy()
        select_osu_folder()

    tk.Button(win, text="Select osu! Folder", command=on_continue).pack(pady=10)
    win.mainloop()

# -------------------- FOLDER SELECTION --------------------

def select_osu_folder():
    root = tk.Tk()
    root.withdraw()  # hide main window
    osu_folder = filedialog.askdirectory(title="Select your osu! folder")
    if not osu_folder:
        messagebox.showerror("Error", "No folder selected")
        return

    collection_path = os.path.join(osu_folder, "collection.db")
    if not os.path.exists(collection_path):
        messagebox.showerror("Error", f"No collection.db found in {osu_folder}")
        return

    collections = load_collection_db(collection_path)
    if not collections:
        messagebox.showinfo("Info", "No collections found in collection.db")
        return

    main_gui(collections)

# -------------------- MAIN --------------------

if __name__ == "__main__":
    instruction_window()
