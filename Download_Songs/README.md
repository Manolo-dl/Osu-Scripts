# osu! Beatmap Downloader GUI

![osu! logo](https://assets.ppy.sh/media/osu-logo.png)

## Description

This script allows you to automatically download osu! beatmaps using a graphical interface (GUI). It provides a three-step workflow:

1. Select a file containing beatmap links.
2. Choose the folder where beatmaps will be downloaded.
3. Log in with SeleniumBase and download the beatmaps.

The GUI includes a dashboard showing download progress and completed beatmaps.

## Requirements

* Python 3.9 or higher
* Python libraries:

  ```bash
  pip install seleniumbase requests
  ```
* Browser compatible with SeleniumBase (Chrome, Firefox, Edge, Brave, etc.)
* osu! account for downloading private beatmaps if necessary.

## Usage

1. Clone or download this repository.
2. Prepare a `.txt` file with the beatmap links, one per line.
3. Run the script:

   ```bash
   python osu_beatmap_downloader.py
   ```
4. In the GUI:

   * Select the links file.
   * Choose the download folder.
   * Manually log in when the browser opens.
5. Monitor progress and completed beatmaps on the dashboard.

## Example links file (`links.txt`)

```
https://osu.ppy.sh/beatmapsets/12345
https://beatconnect.io/b/67890
```

## License

This project is released under the MIT License.

---

**Note:** This script respects osu!'s policies and should only be used for personal and educational purposes. Do not distribute content in ways that violate osu!'s terms of service.

