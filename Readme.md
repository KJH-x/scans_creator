# Scan Creator

This project is a **video snapshot and metadata scanner** that captures snapshots at specified intervals from a video, formats them into a grid, and overlays essential metadata such as codec, resolution, bitrate, and language information. Additionally, it includes custom fonts and logo integration. **Please note: This project is in its early stages and may experience critical bugs.**

## Features

- **Snapshot Extraction**: Captures and resizes snapshots at set intervals across the video.
- **Metadata Display**: Displays video, audio, and subtitle details within the final scan image.
- **Customizable Layout**: Configurable grid layout for arranging snapshots.
- **Image Resizing & Logo Overlay**: Optional resizing for the final image and support for logo integration.

## Requirements

- **Python 3.8+**
- **FFmpeg** (for extracting frames from the video)
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

2. Enter the **file path** to the video when prompted.

3. The script will:
   - Verify necessary files (fonts and logo).
   - Extract video information, including file size, duration, and bitrate.
   - Capture snapshots at evenly spaced intervals.
   - Generate a composite image of snapshots with metadata and save it to the `scans/` directory.

4. The final scan image is saved as a PNG file in the format:

   ``` bash
   scans/<timestamp>.scan.<video_filename>.png
   ```

## Example Output

The output will be a composite image arranged in a 4x4 grid, displaying snapshots and video metadata with a custom logo.

![img](./scans/example/000000.scan.Dune.Part.Two.2024.2160p.BluRay.DoVi.x265.10bit.Atmos.TrueHD7.1-WiKi.mkv.png)

## Notes

- **Grid Layout**: Adjust the grid layout in the `create_scan_image` function by modifying the grid tuple `(4, 4)` for different rows and columns.
- **Snapshot Count**: Adjust the `snapshot_count` in the `calculate_snapshot_times` function to capture more or fewer snapshots.

## Limitations & Known Issues

- **Early Development**: This is an early-stage project, and bugs may result in crashes or incomplete image generation.
- **Error Handling**: Error handling is limited, especially for issues related to FFmpeg processing or missing metadata fields.

## License

MIT License

---

For any issues, please open an issue on the repository or contribute with a pull request.
