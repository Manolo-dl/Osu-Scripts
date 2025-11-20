# Written by ItsCollector
# Search your songs directory for maps based on tags to export as download links

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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

 # ----------------- HP Entry Validation -----------------
def validate_hp_entry(P):
    """
    Tkinter validatecommand for HP entries.
    P = proposed string value in the entry
    Returns True if valid input (float between 0-10 or empty string), False otherwise.
    """
    if P == "":
        return True
    try:
        val = float(P)
        return 0.0 <= val <= 10.0
    except ValueError:
        return False
        
class OsuScannerUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("osu! Tag Scanner")
        self.root.geometry("650x600")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Tab 1: Setup ---
        self.tab_setup = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_setup, text="Setup")
        self.create_setup_tab()

        # --- Tab 2: Filters ---
        self.tab_filters = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_filters, text="Filters")
        self.create_filters_tab()

        # --- Status Box ---
        self.status_box = scrolledtext.ScrolledText(self.root, height=15)
        self.status_box.pack(fill='both', expand=True, pady=5)
        self.status_box.config(state=tk.DISABLED)

        self.songs_dir = None
        self.output_file = None

        self.root.mainloop()

    # ----------------- Tabs Creation -----------------
    def create_setup_tab(self):
        tk.Label(self.tab_setup, text="Select your osu! Songs folder:").pack(pady=5)
        tk.Button(self.tab_setup, text="Browse", command=self.select_songs_folder).pack(pady=5)
        self.folder_label = tk.Label(self.tab_setup, text="No folder selected")
        self.folder_label.pack(pady=5)

        tk.Label(self.tab_setup, text="Select output file:").pack(pady=10)
        tk.Button(self.tab_setup, text="Browse", command=self.select_output_file).pack(pady=5)
        self.output_label = tk.Label(self.tab_setup, text="No file selected")
        self.output_label.pack(pady=5)

    def create_filters_tab(self):
        # Tags
        tk.Label(self.tab_filters, text="Enter tags to search (comma-separated):").pack(pady=10)
        self.tags_entry = tk.Entry(self.tab_filters, width=50)
        self.tags_entry.pack(pady=5)

        # Game mode
        tk.Label(self.tab_filters, text="Select Game Mode:").pack(pady=10)
        self.mode_var = tk.StringVar(value="Mania")
        self.mode_dropdown = ttk.Combobox(
            self.tab_filters,
            textvariable=self.mode_var,
            state="readonly",
            values=["Osu", "Taiko", "Catch", "Mania"]
        )
        self.mode_dropdown.pack(pady=5)

        # HP range
        tk.Label(self.tab_filters, text="Min HP:").pack(pady=5)
        self.min_hp = tk.DoubleVar(value=2.0)
        self.max_hp = tk.DoubleVar(value=8.0)

        vcmd = (self.tab_filters.register(validate_hp_entry), "%P")

        self.min_entry = tk.Entry(self.tab_filters, textvariable=self.min_hp, validate="key", validatecommand=vcmd)
        self.min_entry.pack(pady=5)

        tk.Label(self.tab_filters, text="Max HP:").pack(pady=5)
        self.max_entry = tk.Entry(self.tab_filters, textvariable=self.max_hp, validate="key", validatecommand=vcmd)
        self.max_entry.pack(pady=5)

        tk.Button(self.tab_filters, text="Print HP Range", command=self.show_hp_range).pack(pady=10)

        # Scan button
        self.scan_button = tk.Button(self.tab_filters, text="Start Scan", command=self.start_scan)
        self.scan_button.pack(pady=15)

    # ----------------- Event Handlers -----------------
    def show_hp_range(self):
        try:
            min_val = round(float(self.min_entry.get()), 1)
            max_val = round(float(self.max_entry.get()), 1)

            if min_val > max_val:
                messagebox.showwarning("Invalid Range", "Min HP cannot be greater than Max HP.")
                return

            messagebox.showinfo("HP Range", f"HP range: {min_val:.1f} - {max_val:.1f}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")

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

    def log(self, text):
        self.status_box.config(state=tk.NORMAL)
        self.status_box.insert(tk.END, text + "\n")
        self.status_box.see(tk.END)
        self.status_box.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def start_scan(self):
        if not self.songs_dir or not self.output_file:
            messagebox.showwarning("Missing info", "Please select Songs folder and output file")
            return

        tags_input = self.tags_entry.get().strip()
        if not tags_input:
            messagebox.showwarning("Missing info", "Please enter at least one tag")
            return

        target_tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        selected_mode = self.mode_var.get().lower()

        self.scan_button.config(state=tk.DISABLED)
        self.log(f"Starting scan...\nTags: {target_tags}\nMode: {selected_mode}\nHP: {self.min_hp.get():.1f} - {self.max_hp.get():.1f}")

        threading.Thread(target=self.run_scan, args=(target_tags, selected_mode), daemon=True).start()

    def run_scan(self, target_tags, selected_mode):
        # Run SongScanner
        scanner = SongScanner(self.songs_dir, target_tags)
        scanner.scan()

        filtered_matches = [m for m in scanner.matches if m["mode"].lower() == selected_mode]

        self.log(f"Mapsets scanned: {scanner.mapsets_scanned}")
        self.log(f"Matches found (mode={selected_mode}): {len(filtered_matches)}")

        with open(self.output_file, "w", encoding="utf-8") as f:
            for m in filtered_matches:
                link = f"https://osu.ppy.sh/beatmapsets/{m['mapset_id']}"
                f.write(link + "\n")

        self.log(f"Exported {len(filtered_matches)} links to: {self.output_file}")
        self.scan_button.config(state=tk.NORMAL)
        messagebox.showinfo("Done", "Scan and export complete!")

    def show_range(self):
        try:
            min_val = round(float(self.min_entry.get()), 1)
            max_val = round(float(self.max_entry.get()), 1)
            print(f"HP range: {min_val:.1f} - {max_val:.1f}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")


# ------------------- Run the GUI -------------------
if __name__ == "__main__":
    OsuScannerUI()


