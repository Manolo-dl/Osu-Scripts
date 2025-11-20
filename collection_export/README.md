# osu! Collection Exporter (Offline)

A simple offline tool to export your osu! collections into text files with download links for each beatmap. Fully offline — no API or internet connection required.

---

## Features

- GUI-based, easy to use.  
- Automatically reads your `collection.db` and Songs folder.  
- Select which collections to export.  
- Exports `.txt` files containing valid osu! beatmap links.  
- Handles multiple beatmaps from the same beatmapset (one link per set).  
- Shows a progress bar during export.  
- Automatically clears selection after export.  
- Reports the number of missing beatmaps.

---

## Requirements

- Python 3.8+  
- No additional dependencies (uses only standard library and Tkinter)

---

## Usage

1. Download or clone the repository.  

```bash
git clone https://github.com/yourusername/osu-collection-exporter.git
cd osu-collection-exporter
Run the program:

bash
Copiar código
python collection_export.py
Steps in the GUI:

Select your osu! folder — the folder containing collection.db and the Songs folder.

Select collections from the list to export.

Export — choose an output folder for your .txt files.

After export:

.txt files will be generated for each selected collection with download links.

Missing beatmaps are counted but no link is written for them.

Notes
The program works completely offline.

Only beatmaps present in your local Songs folder will have valid links in the exported .txt.

Export links use the official osu! beatmapset URLs, automatically selecting the correct mode (osu!, taiko, fruits, mania).

If a beatmap is missing locally, it will be reported in the summary popup.

Screenshots
(Optional: include screenshots of your GUI here)

License
MIT License

Contributing
Feel free to open issues or submit pull requests to improve the program.

pgsql
Copiar código

---

If you want, I can also **write a shorter “user-friendly” version** suitable for GitHub with screenshots and step-by-step usage tips, ready to paste directly into your repo.  

Do you want me to do that?
