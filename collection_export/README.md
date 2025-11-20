# osu! Collection Exporter (Offline)

Export your osu! collections to `.txt` files with download links for each beatmap, completely offline. No osu! API or internet connection is required.

---

## Features

- GUI-based, easy to use.  
- Automatically detects your `collection.db` and `Songs` folder.  
- Displays all your collections for selection.  
- Allows selecting multiple collections to export.  
- Exports `.txt` files containing valid osu! beatmap links (one link per beatmapset).  
- Shows a progress bar during export.  
- Reports the number of missing songs (songs not found locally).  
- Automatically clears selection after export.  

---

## Requirements

- Python 3.8 or higher  
- Tkinter (usually included in standard Python installation)

---

## How to Use

1. **Download or clone this repository**:

```bash
git clone https://github.com/yourusername/osu-collection-exporter.git
cd osu-collection-exporter
```
2. Run the program

```bash
python collection_export.py
```

## Usage

1. Select your osu! folder
Click the Select osu! Folder button. The folder must contain collection.db and a Songs folder.

2. Select collections to export
The program will display all collections with the number of beatmaps. Select the collections you want to export.

3. Export
Click Export Selected Collections and choose an output folder. The program will generate one .txt file per collection with valid osu! beatmap links.

4. After export


