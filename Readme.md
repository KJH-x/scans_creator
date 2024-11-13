# Scan Creator

This project is a **video snapshot and metadata scanner** that captures snapshots at specified intervals from a video, formats them into a grid, and overlays essential metadata such as codec, resolution, bitrate, and language information. Additionally, it includes custom fonts and logo integration. **Please note: This project is in its early stages and may experience critical bugs.**

## Features

- **Snapshot Extraction**: Captures and resizes snapshots at set intervals across the video.
- **Metadata Display**: Displays video, audio, and subtitle details within the final scan image.
- **Customizable Layout**: Configurable grid layout for arranging snapshots.
- **Image Resizing & Logo Overlay**: Optional resizing for the final image and support for logo integration.

## Requirements

- **Python 3.10+**

> No python 3.8 supports. You can manully remove incompatible codes (type annotations) to run in python 3.8 (tested), but this repo will not offer directly.

- **FFmpeg** (for extracting frames from the video, type 'ffmpeg -version` in terminal to check)
- **Pillow** (PIL library for image manipulation)

## Setup

0. **Download Repo**:

   ```bash
   git clone https://github.com/KJH-x/scans_creator.git
   ```

1. **Install dependencies**:

   ```bash
   pip install pillow
   ```

2. **Download FFmpeg**:
   Ensure FFmpeg is installed and accessible from the command line. You can download FFmpeg [here](https://ffmpeg.org/download.html).

3. **Fonts and Logo**:
   Place your chosen fonts (`font_file` and `font_file_2`) in the `fonts/` directories.

## Usage

1. Run the script:

   ```bash
   python main.py
   ```

2. The script will automatically load configuration settings from the `config.json` file. If the file does not exist, it will be created with default values.

3. Enter the **file path** to the video when prompted.

4. The script will:
   - Verify necessary files (fonts and logo) based on the paths provided in the `config.json` file.
   - Extract video information, including file size, duration, and bitrate.
   - Capture snapshots at evenly spaced intervals based on the grid size defined in the configuration.
   - Generate a composite image of snapshots with metadata and save it to the `scans/` directory.

5. The final scan image is saved as a PNG file in the format:

   ```bash
   scans/<timestamp>.scan.<video_filename>.png
   ```

## Example Output

The output will be a composite image arranged in a grid layout, displaying snapshots and video metadata with a custom logo.

![img](./scans/example/000000.scan.Dune.Part.Two.2024.2160p.BluRay.DoVi.x265.10bit.Atmos.TrueHD7.1-WiKi.mkv.png)

## Notes

- **Grid Layout**: The grid layout can be customized by adjusting the `grid_size` tuple in the `config.json` file. For instance, setting the grid to `(4, 4)` will create a 4x4 grid of snapshots (16 snapshots in total). You can change the grid size to any other desired configuration, such as `(3, 3)` for 9 snapshots, or `(5, 5)` for 25 snapshots, based on your needs.
  
- **Configuration File**: All customizable parameters, such as file paths for fonts, logo, and snapshot grid size, are managed via the `config.json` file. The default values are already provided, but you can modify them according to your project requirements.
  
### Default Configuration (`config.json`)

The default `config.json` looks like this:

```json
{
   "font_file": "fonts/serif.ttf",
   "font_file_2": "fonts/sans.ttf",
   "logo_file": "logo/logo.png",
   "resize_scale": 2,
   "avoid_leading": true,
   "avoid_ending": true,
   "grid_size": [
         4,
         4
   ]
}
```

- `font_file`: Path to the serif font file used for metadata text.
- `font_file_2`: Path to the sans-serif font file used for secondary text.
- `logo_file`: Path to the logo image file to overlay on the scan.
- `resize_scale`: Scaling factor for resizing the final scan image (e.g., `2` means resize to half size).
- `avoid_leading`: If `true`, avoids taking snapshots from the very beginning of the video.
- `avoid_ending`: If `true`, avoids taking snapshots from the very end of the video.
- `grid_size`: A tuple defining the grid size for snapshot arrangement (e.g., `[4, 4]` for a 4x4 grid).

You can update these values to suit your project needs. For example, if you'd prefer a smaller grid (or  bigger snapshots), change `"grid_size": [4, 4]` to `"grid_size": [3, 3]` for a 3x3 grid (9 snapshots).

## Limitations & Known Issues

- **Early Development**: This is an early-stage project, and bugs may result in crashes or incomplete image generation.
- **Error Handling**: Error handling is limited, especially for issues related to FFmpeg processing or missing metadata fields.

## License

MIT License

---

For any issues, please open an issue on the repository or contribute with a pull request.
