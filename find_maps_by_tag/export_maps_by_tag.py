# Written by ItsCollector
# Search your songs directory for maps based on tags to export as download links

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
import threading

MODE_MAP = {
    0: "osu",
    1: "taiko",
    2: "catch",
    3: "mania"
}

class OsuFileParser:
    #Parses a .osu file and extracts header fields such as tags, IDs, and mode

    def __init__(self, osu_path: Path):
        self.osu_path = osu_path
        self.tags = None
        self.mapset_id = None
        self.map_id = None
        self.mode = None

    def parse(self):
        # Reads the .osu file until all needed fields are found
        with self.osu_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("Tags:"):
                    self.tags = line.split(":", 1)[1].strip()

                elif line.startswith("BeatmapSetID:"):
                    self.mapset_id = line.split(":")[1].strip()

                elif line.startswith("BeatmapID:"):
                    self.map_id = line.split(":")[1].strip()

                elif line.startswith("Mode:"):
                    mode_num = int(line.split(":")[1].strip())
                    self.mode = MODE_MAP.get(mode_num, "osu")

                # Stop early if everything found
                if (
                    self.tags is not None and
                    self.mapset_id and
                    self.map_id and
                    self.mode
                ):
                    break

        return self  # allows chaining


class SongScanner:
    # Scans the Songs directory for .osu files and finds maps that contain matching tags
    def __init__(self, songs_dir: Path, target_tags: list[str]):
        self.songs_dir = Path(songs_dir)
        self.target_tags = [t.lower() for t in target_tags]
        self.matches = []
        self.mapsets_scanned = 0

    def _tags_match(self, tags: str):
        """Check if any target tag is inside the Tags line."""
        if not tags:
            return False
        
        tags_lower = tags.lower()

        return any(tag in tags_lower for tag in self.target_tags)

    def scan(self):
        last_folder = None

        for osu_file in self.songs_dir.rglob("*.osu"):
            folder = osu_file.parent

            # Only scan the first .osu in each mapset folder
            if folder == last_folder:
                continue

            last_folder = folder
            self.mapsets_scanned += 1

            parser = OsuFileParser(osu_file).parse()

            if self._tags_match(parser.tags):
                self.matches.append({
                    "path": str(osu_file),
                    "tags": parser.tags,
                    "mapset_id": parser.mapset_id,
                    "map_id": parser.map_id,
                    "mode": parser.mode
                })

    def print_results(self):
        print("\n=== Scan Results ===")
        print("Mapsets scanned:", self.mapsets_scanned)
        print("Matches found:", len(self.matches))
        print()

    def export_links(self, output_path):
        # Export all matched beatmapset links to a text file.
        with open(output_path, "w", encoding="utf-8") as f:
            for m in self.matches:
                link = f"https://osu.ppy.sh/beatmapsets/{m['mapset_id']}"
                f.write(link + "\n")

        print(f"\nExported {len(self.matches)} links to {output_path}")


class OsuScannerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("osu! Tag Scanner")
        self.root.geometry("600x500")

        # Folder selection
        tk.Label(self.root, text="Step 1: Select your osu! Songs folder").pack(pady=5)
        tk.Button(self.root, text="Select Songs Folder", command=self.select_songs_folder).pack(pady=5)
        self.folder_label = tk.Label(self.root, text="No folder selected")
        self.folder_label.pack(pady=5)

        # Tags input
        tk.Label(self.root, text="Step 2: Enter tags to search (comma-separated)").pack(pady=10)
        self.tags_entry = tk.Entry(self.root, width=50)
        self.tags_entry.pack(pady=5)

        # Output file selection
        tk.Label(self.root, text="Step 3: Select output file").pack(pady=10)
        tk.Button(self.root, text="Select Output File", command=self.select_output_file).pack(pady=5)
        self.output_label = tk.Label(self.root, text="No file selected")
        self.output_label.pack(pady=5)

        # Scan button
        self.scan_button = tk.Button(self.root, text="Start Scan", command=self.start_scan)
        self.scan_button.pack(pady=10)

        # Progress / status
        self.status_box = scrolledtext.ScrolledText(self.root, height=15, width=70)
        self.status_box.pack(pady=10)
        self.status_box.config(state=tk.DISABLED)

        # Internal state
        self.songs_dir = None
        self.output_file = None

        self.root.mainloop()

    def log(self, text):
        self.status_box.config(state=tk.NORMAL)
        self.status_box.insert(tk.END, text + "\n")
        self.status_box.see(tk.END)
        self.status_box.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def select_songs_folder(self):
        folder = filedialog.askdirectory(title="Select osu! Songs folder")
        if folder:
            self.songs_dir = Path(folder)
            self.folder_label.config(text=str(folder))

    def select_output_file(self):
        file = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if file:
            self.output_file = file
            self.output_label.config(text=file)

    def start_scan(self):
        if not self.songs_dir or not self.output_file:
            messagebox.showwarning("Missing info", "Please select Songs folder and output file")
            return

        tags_input = self.tags_entry.get().strip()
        if not tags_input:
            messagebox.showwarning("Missing info", "Please enter at least one tag")
            return

        target_tags = [t.strip() for t in tags_input.split(",") if t.strip()]

        self.scan_button.config(state=tk.DISABLED)
        self.log("Starting scan...")

        # Run scan in separate thread so GUI doesn't freeze
        threading.Thread(target=self.run_scan, args=(target_tags,), daemon=True).start()

    def run_scan(self, target_tags):
        scanner = SongScanner(self.songs_dir, target_tags)
        scanner.scan()

        self.log(f"Mapsets scanned: {scanner.mapsets_scanned}")
        self.log(f"Matches found: {len(scanner.matches)}")

        scanner.export_links(self.output_file)
        self.log(f"Exported links to: {self.output_file}")

        self.scan_button.config(state=tk.NORMAL)
        messagebox.showinfo("Done", "Scan and export complete!")

# ------------------- Run the GUI -------------------

if __name__ == "__main__":
    OsuScannerUI()

