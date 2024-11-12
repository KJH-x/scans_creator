import io
import json
import math
import os
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps
from PIL.Image import Image as ImageType
from PIL.Image import Resampling
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont

from VideoInfo import VideoInfo


def ffprobe_get_info(filename: str) -> Dict[Any, Any] | None:
    """
    Retrieve media file information using `ffprobe` and return it as a dictionary.

    Args:
        filename (str): The path to the media file for which metadata information is required.

    Returns:
        Dict[Any, Any] | None: A dictionary containing metadata and stream information about the file 
        if successful, or `None` if an error occurs during JSON decoding.

    Raises:
        JSONDecodeError: Logs an error message if the JSON output from `ffprobe` cannot be decoded.
    """

    result = subprocess.Popen(
        ["ffprobe", "-i", filename, '-v', 'error', '-print_format', 'json', '-show_format', '-show_streams'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, _ = result.communicate()
    try:
        info = dict(json.loads(stdout.decode("utf-8")))
        return info
    except json.JSONDecodeError:
        print("Failed to decode JSON from stdout")
        return None


def parse_list(input_list: List[str], exclude: str = "N/A", separator: str = '/') -> str:
    """
    Parse a list of strings by removing specified excluded values and joining the remaining unique elements.

    Args:
        input_list (List[str]): The list of strings to be parsed.
        exclude (str, optional): A value to be excluded from the result (if present). Defaults to "N/A".
        separator (str, optional): The separator to use when joining elements in the output. Defaults to '/'.

    Returns:
        str: A single string with unique elements from `input_list`, separated by `separator`, or an empty string if all elements were excluded.
    """

    hash_table = set(input_list)
    hash_table.discard(exclude)
    if hash_table:
        return separator.join(list(hash_table))
    else:
        return ""


def _get_with_type(dict_obj: Dict[str, int | str], property: str, default_value: str | int | float): ...


def get_video_info(file_path: str) -> Optional[VideoInfo]:
    """
    Extract detailed video, audio, and subtitle metadata from a specified media file.

    Args:
        file_path (str): The path to the media file to be analyzed.

    Returns:
        Optional[VideoInfo]: A `VideoInfo` object containing detailed metadata about the video,
        audio, and subtitle streams, or `None` if the metadata could not be obtained or parsed.

    Raises:
        FileNotFoundError: If the specified `file_path` does not exist.

    Metadata Includes:
        - File information: name, path, size, duration, and bitrate.
        - Video stream: codec, colorspace, frame size, frame rate, and language.
        - Audio stream: codec, language, title, sample rate, and channel count.
        - Subtitle stream: codec, language, and title.
    """

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    info = ffprobe_get_info(file_path)
    if not info:
        return None

    if not isinstance(info, dict):
        return None

    format_info = info.get("format", {})
    duration = int(float(format_info.get("duration", 0)))
    bitrate = int(format_info.get("bit_rate", 0))

    file_info = {
        "name": file_name,
        "path": file_path,
        "size": file_size,
        "duration": duration,
        "bitrate": bitrate,
    }

    video_info = {
        "codec": "",
        "colorspace": "",
        "frame_size": "",
        "framerate": 0.0,
        "lang": ""
    }

    audio_info = {
        "codec": "",
        "lang": "",
        "title": "",
        "sampleRate": "",
        "channels": "",
    }

    subtitle_info = {
        "codec": "",
        "lang": "",
        "title": ""
    }

    audio_codec_l: List[str] = []
    audio_lang_l: List[str] = []
    audio_title_l: List[str] = []
    audio_sampleRate_l: List[str] = []
    audio_channels_l: List[str] = []

    sub_codec_l: List[str] = []
    sub_lang_l: List[str] = []
    sub_title_l: List[str] = []

    for stream in info.get("streams", []):
        if not isinstance(stream, dict):
            continue

        if stream.get("codec_type") == "video":
            if stream.get("codec_name") not in ['png', 'jpeg', 'mjpeg']:
                video_info["codec"] = stream.get("codec_name", "")
                video_info["colorspace"] = stream.get("color_space", "")
                width = stream.get("width", 0)
                height = stream.get("height", 0)
                video_info["frame_size"] = f"{width}x{height}"
                avg_frame_rate = stream.get("avg_frame_rate", "0/1")
                video_info["framerate"] = eval(avg_frame_rate) if avg_frame_rate != "0/1" else 0.0

                if not isinstance(tags := stream.get("tags", {}), dict):
                    continue
                video_info["lang"] = tags.get("language", "N/A")

        elif stream.get("codec_type") == "audio":
            audio_codec_l.append(stream.get("codec_name", "N/A"))
            audio_sampleRate_l.append(stream.get("sample_rate", "N/A"))
            audio_channels_l.append(str(stream.get("channels", "N/A")))

            if not isinstance(tags := stream.get("tags", {}), dict):
                continue
            audio_lang_l.append(tags.get("language", "N/A"))
            audio_title_l.append(tags.get("title", "N/A"))

        elif stream.get("codec_type") == "subtitle":
            sub_codec_l.append(stream.get("codec_name", "N/A"))

            if not isinstance(tags := stream.get("tags", {}), dict):
                continue
            sub_lang_l.append(tags.get("language", "N/A"))
            sub_title_l.append(tags.get("title", "N/A"))

    audio_info["codec"] = parse_list(audio_codec_l)
    audio_info["lang"] = parse_list(audio_lang_l)
    audio_info["title"] = parse_list(audio_title_l)
    audio_info["sampleRate"] = parse_list(audio_sampleRate_l)
    audio_info["channels"] = parse_list(audio_channels_l)

    subtitle_info["codec"] = parse_list(sub_codec_l)
    subtitle_info["lang"] = parse_list(sub_lang_l)
    subtitle_info["title"] = parse_list(sub_title_l)

    return VideoInfo(file_info, video_info, audio_info, subtitle_info)


def calculate_snapshot_times(video_info: VideoInfo, snapshot_count=4, skip_seconds_from_head=0, discard_seconds_from_end=0) -> List[int]:
    """
    Calculate evenly spaced snapshot times for a video based on its duration and specified parameters.

    Args:
        video_info (VideoInfo): An object containing metadata about the video, including its total duration in seconds.
        snapshot_count (int, optional): The number of snapshots to capture. Defaults to 4.
        skip_seconds_from_head (int, optional): The number of seconds to skip from the beginning of the video before taking the first snapshot. Defaults to 0.
        discard_seconds_from_end (int, optional): The number of seconds to disregard from the end of the video when calculating snapshot intervals. Defaults to 0.

    Returns:
        List[int]: A list of integers representing the times (in seconds) at which to capture each snapshot, spaced evenly throughout the adjusted video duration.
    """

    duration = video_info.duration
    start_time = skip_seconds_from_head
    end_time = duration - discard_seconds_from_end
    snapshot_interval = math.floor((end_time - start_time) / snapshot_count)
    snapshot_times: List[int] = [start_time + i *
                                 snapshot_interval for i in range(snapshot_count)]

    return snapshot_times


def take_snapshots(video_info: VideoInfo, snapshot_times, target_width=0, target_height=0, scale_method="fit") -> List[ImageType]:
    """
    Capture snapshots from a video at specified times, scaling each snapshot to the desired target dimensions.

    Args:
        video_info (VideoInfo): Metadata about the video, including the file path and frame dimensions.
        snapshot_times (list[int]): List of times (in seconds) to capture each snapshot from the video.
        target_width (int, optional): The width to scale each snapshot to. If only width is provided, 
                                      the height will adjust based on the aspect ratio. Defaults to 0.
        target_height (int, optional): The height to scale each snapshot to. If only height is provided, 
                                       the width will adjust based on the aspect ratio. Defaults to 0.
        scale_method (str, optional): The scaling method to apply, which can be:
            - "fit": Scale to fit within target dimensions, adding black padding as needed.
            - "stretch": Stretch to exactly match target dimensions.
            - "crop": Scale and crop to fill target dimensions, cropping excess area.
            Defaults to "fit".

    Returns:
        list[ImageType]: A list of PIL Image objects representing the captured snapshots.

    Prints:
        Progress messages indicating the count of snapshots taken.
    """

    snapshots: List[ImageType] = []

    width, height = map(int, video_info.frame_size.split('x'))
    aspect_ratio = width / height

    if target_width and not target_height:
        target_height = int(target_width / aspect_ratio)
    elif target_height and not target_width:
        target_width = int(target_height * aspect_ratio)
    elif not target_height and not target_width:
        target_height = 450
        target_width = 800

    for idx, time in enumerate(snapshot_times):
        hhmmss = f"{time // 3600:02}:{(time % 3600) // 60:02}:{time % 60:02}"
        output = subprocess.Popen(
            ["ffmpeg", "-ss", hhmmss, "-i", video_info.file_path, "-skip_frame", "nokey", "-frames:v",
             "1", "-q:v", "2", "-f", "image2pipe", "-vcodec", "png", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, _ = output.communicate()
        image = Image.open(io.BytesIO(stdout))

        if scale_method == "fit":
            scale_factor = min(target_width/width, target_height/height)
            scale_width, scale_height = (math.floor(
                scale_factor*width), math.floor(scale_factor*height))

            image = image.resize(
                (scale_width, scale_height), Resampling.LANCZOS)

            left = int((target_width - scale_width) // 2)
            top = int((target_height - scale_height) // 2)
            right = int(target_width - scale_width - left)
            bottom = int(target_height - scale_height - top)
            image = ImageOps.expand(
                image, (left, top, right, bottom), fill='black')

        elif scale_method == "stretch":
            image = image.resize(
                (target_width, target_height), Resampling.LANCZOS)

        elif scale_method == "crop":
            scale_factor = max(target_width/width, target_height/height)
            scale_width, scale_height = (
                math.ceil(scale_factor*width), math.ceil(scale_factor*height))

            image = image.resize(
                (scale_width, scale_height), Resampling.LANCZOS)

            left = int((target_width - scale_width) // 2)
            top = int((target_height - scale_height) // 2)
            right = int(target_width - scale_width - left)
            bottom = int(target_height - scale_height - top)
            image = image.crop((left, top, right, bottom))

        print(f"[{idx+1}/{len(snapshot_times)}] snapshot(s) taken.")
        snapshots.append(image)

    return snapshots


def _image_histogram(image: ImageType) -> ImageType: ...


def _image_complexity(image: ImageType): ...


def multiline_text_with_shade(
    draw_obj: ImageDrawType, text: str,
    pos: Tuple[int, int], offset: Tuple[int, int], spacing: int,
    font: FreeTypeFont, text_color: Tuple[int, int, int], shade_color: Tuple[int, int, int]
) -> None:

    x, y = pos
    dx, dy = offset
    draw_obj.multiline_text((x+dx, y+dy), text, fill=shade_color, font=font, spacing=spacing)
    draw_obj.multiline_text((x, y), text, fill=text_color, font=font, spacing=spacing)

    return None


def create_scan_image(images: List[ImageType], grid: Tuple[int, int], snapshottimes: List[int], video_info: VideoInfo, fontfile_1: str, fontfile_2: str, logofile: str) -> ImageType:
    """
    Create a composite scan image by arranging snapshots in a grid format with metadata and a logo overlay.

    Args:
        images (List[ImageType]): List of snapshot images to arrange in the scan image.
        grid (Tuple[int, int]): Number of columns and rows for arranging images in the scan image.
        snapshottimes (List[int]): List of snapshot times (in seconds) for each image to display as timestamps.
        video_info (VideoInfo): Metadata about the video, including file, video, audio, and subtitle information.
        fontfile_1 (str): Path to the font file for primary headings.
        fontfile_2 (str): Path to the font file for subheadings and timestamps.
        logofile (str): Path to the logo image file to place in the top-right corner.

    Raises:
        ValueError: If the number of `images` does not match the required number based on `grid`.

    Returns:
        ImageType: A PIL Image object of the completed scan image, with:
            - A metadata section for video, audio, and subtitle details.
            - Snapshot images arranged in a grid with timestamps.
            - A logo in the top-right corner.

    Additional Information:
        - The canvas is created to fit all images in the specified grid layout with padding.
        - Timestamps are displayed on each snapshot with a shaded background.
        - Video information (size, duration, codec, etc.) is displayed at the top.
    """

    col, row = grid
    total_images = col * row

    font_1 = ImageFont.truetype(fontfile_1, 45)
    font_2 = ImageFont.truetype(fontfile_2, 40)

    if len(images) != total_images:
        raise ValueError(
            f"Image count ({len(images)}) does not match the grid count ({total_images}).")

    canvas_width = col * 800
    canvas_height = (row + 1) * 450

    scan_image = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(scan_image)

    spacing = 10
    offset = (2, 2)
    text_color = (0, 0, 0)
    shade_color = (49, 49, 49)
    text_list = [
        [
            video_info["F"]["name"],
        ],
        [
            "文件信息：",
            "大　　小：",
            "时　　长：",
            "总比特率：",
        ],
        [
            "",
            video_info["F"]["size"],
            video_info["F"]["duration"],
            video_info["F"]["bitrate"],
        ],
        [
            "视频信息：",
            "编　　码：",
            "色彩空间：",
            "尺　　寸：",
            "帧　　率：",
        ],
        [
            "",
            video_info["V"]["codec"],
            video_info["V"]["colorspace"],
            video_info["V"]["frameSize"],
            video_info["V"]["frameRate"],
        ],
        [
            "音频信息：",
            "编　　码：",
            "音频语言：",
            "音频标题：",
        ],
        [
            "",
            video_info["A"]["codec"],
            video_info["A"]["lang"],
            video_info["A"]["title"],
        ],
        [
            "字幕信息：",
            "编　　码：",
            "字幕语言：",
            "字幕标题：",
        ],
        [
            "",
            video_info["S"]["codec"],
            video_info["S"]["lang"],
            video_info["S"]["title"],
        ],
    ]
    pos_list = [
        (30, 10),
        (30, 100), (230, 100),
        (630, 100), (830, 100),
        (1230, 100), (1430, 100),
        (1830, 100), (2030, 100),
    ]
    font_list = [font_1, font_2, font_2, font_2, font_2, font_2, font_2, font_2, font_2]

    for i, j, k in zip(text_list, pos_list, font_list):
        multiline_text_with_shade(draw, "\n".join(i), j, offset, spacing, k, text_color, shade_color)

    y_offset = 450
    for idx, image in enumerate(images):

        grid_x = (idx % col) * 800
        grid_y = (idx // col) * 450 + y_offset

        image_resized = image.resize((800, 450), Resampling.LANCZOS)

        scan_image.paste(image_resized, (grid_x, grid_y))

        snapshot_time = str(timedelta(seconds=snapshottimes[idx]))

        text_bbox = draw.textbbox((0, 0), snapshot_time, font=font_2)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        timestamp_x = grid_x + (800 - text_width) // 2

        timestamp_y = grid_y - (text_height // 2) + 10

        background = Image.new(
            "RGBA", (text_width, text_height), (0, 0, 0, int(255 * 0.6)))
        scan_image.paste(background, (timestamp_x, timestamp_y+14), background)

        draw.text((timestamp_x, timestamp_y), snapshot_time,
                  fill=(255, 255, 255, int(255 * 0.6)), font=font_2)

    logo = Image.open(logofile).resize((405, 405), Resampling.LANCZOS)

    logo_x = scan_image.width - logo.width - 22
    logo_y = 22

    scan_image.paste(logo, (logo_x, logo_y), logo.convert("RGBA"))

    return scan_image


if __name__ == '__main__':
    """
    Main script execution for generating a video scan image with snapshots and metadata overlay.

    Steps:
        1. Prompts the user for the video file path and verifies the existence of required resources.
        2. Retrieves video information and calculates evenly spaced snapshot times.
        3. Captures snapshots at the calculated times, resizing each to 800x450 pixels.
        4. Creates a scan image with snapshots arranged in a 4x4 grid, metadata details, and a logo overlay.
        5. Optionally resizes the final scan image to 1600x1125 pixels before saving.

    Inputs:
        - file_path (str): Path to the video file provided by the user.
        - font_file (str): Path to a recommended serif font file.
        - font_file_2 (str): Path to a recommended sans-serif font file.
        - logo_file (str): Path to the logo image file.

    Outputs:
        - Saves the final scan image with a timestamped filename to the "scans" directory.

    Raises:
        FileNotFoundError: If any required file (video, fonts, or logo) does not exist.
        ValueError: If unable to retrieve video information or if other issues occur during processing.
    """

    # chcp 65001

    file_path = input("File Path :")
    # 推荐 serif
    font_file = "fonts/..."
    # 推荐 sans
    font_file_2 = "fonts/..."
    logo_file = "logo/logo.png"
    for _ in [file_path, font_file, font_file_2, logo_file]:
        if not os.path.exists(_):
            print(f"file {_} no found")
            exit(1)

    resize = True

    try:
        video_info = get_video_info(file_path)
        print(video_info)
        if video_info:
            snapshot_times = calculate_snapshot_times(
                video_info, snapshot_count=16)
            snapshots = take_snapshots(video_info, snapshot_times, 800, 450)

            scan = create_scan_image(snapshots, (4, 4), snapshot_times,
                                     video_info, font_file, font_file_2, logo_file)
            if resize:
                scan = scan.resize((1600, 1125), Resampling.LANCZOS)
            scan.save(f"scans/{datetime.now().strftime('%H%M%S')}.scan.{video_info.file_name}.png")

        else:
            print("Failed to retrieve video information.")
    except FileNotFoundError as e:
        print(e)
