import copy
import io
import json
import math
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps
from PIL.Image import Image as ImageType
from PIL.Image import Resampling
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont

from ConfigManager import ConfigManager
from VideoInfo import VideoInfo
from TextDrawer import TextDrawer


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
        - Video stream: codec, color, frame size, frame rate, and language.
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
        "color": "",
        "frame_size": "",
        "framerate": 0.0,
        "lang": "",
        "pix_fmt": "",
        "color_range": "",
        "color_space": "",
        "codec_name": "",
        "profile": "",
        "pix_depth": 0,
        "pix_channels": 0,
        "width": 0,
        "height": 0,
        "sar": "",
        "dar": "",
    }

    audio_info = {
        "codec": "",
        "lang": "",
        "title": "",
        "sampleRate": "",
        "channels": "",
        "channelLayout": "",
    }

    subtitle_info = {
        "codec": "",
        "lang": "",
        "title": ""
    }

    with open("pix_fmt.json", mode='r', encoding="utf-8") as fp:
        fmt_info = json.load(fp)

    # For files with multiple video streams, each item in this list is a dictionary
    # containing video information (video_info) as described above.
    video_info_ld: List[Dict] = []

    audio_codec_l: List[str] = []
    audio_lang_l: List[str] = []
    audio_title_l: List[str] = []
    audio_sampleRate_l: List[str] = []
    audio_channels_l: List[str] = []
    audio_channelLO_l: List[str] = []

    sub_codec_l: List[str] = []
    sub_lang_l: List[str] = []
    sub_title_l: List[str] = []

    for stream in info.get("streams", []):
        if not isinstance(stream, dict):
            continue

        if stream.get("codec_type") == "video":
            # Cross-property concat should done within class init.
            # Video lang is not considered since most video donot have this tag.
            if stream.get("codec_name") not in ['png', 'jpeg', 'mjpeg']:

                video_info["pix_fmt"] = pix_fmt = stream.get('pix_fmt', 'N/A')
                video_info["color_range"] = stream.get('color_range', 'N/A')
                video_info["color_space"] = stream.get('color_space', 'N/A')
                # video_info["color"] = f"{pix_fmt} ({color_range}, {color_space})"

                video_info["codec_name"] = stream.get('codec_name', '')
                video_info["profile"] = stream.get('profile', '')
                video_info["pix_depth"] = fmt_info[pix_fmt]["TYPICAL_DEPTH"]
                video_info["pix_channels"] = fmt_info[pix_fmt]["CHANNELS"]
                # video_info["codec"] = f"{codec_name} ({profile}) ({pix_depth}bit x {pix_channels})"

                video_info["width"] = stream.get("width", 0)
                video_info["height"] = stream.get("height", 0)
                video_info["sar"] = stream.get("sample_aspect_ratio", "")
                video_info["dar"] = stream.get("display_aspect_ratio", "")
                # video_info["frame_size"] = f"{width}x{height} ({sar}/{dar})"

                avg_frame_rate = stream.get("avg_frame_rate", "0/1")
                video_info["framerate"] = eval(avg_frame_rate) if avg_frame_rate != "0/1" else 0.0

                # if isinstance(tags := stream.get("tags", {}), dict):
                #     video_info["lang"] = tags.get("language", "N/A")

                video_info_ld.append(copy.deepcopy(video_info))
                # In the case of other video streams, the other keys are overwritten,
                # but not necessarily for the "lang" item
                # video_info["lang"] = ""

        elif stream.get("codec_type") == "audio":
            audio_codec_l.append(stream.get("codec_name", "N/A"))
            if (sample_rate := stream.get("sample_rate", "N/A")) != "N/A":
                sample_rate = f"{int(sample_rate)//1000} kHz"
            audio_sampleRate_l.append(sample_rate)
            audio_channels_l.append(str(stream.get("channels", "N/A")))
            audio_channelLO_l.append(str(stream.get("channel_layout", "N/A")))

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
    audio_info["channelLayout"] = parse_list(audio_channelLO_l)

    subtitle_info["codec"] = parse_list(sub_codec_l)
    subtitle_info["lang"] = parse_list(sub_lang_l)
    subtitle_info["title"] = parse_list(sub_title_l)

    return VideoInfo(file_info, video_info_ld, audio_info, subtitle_info)


def calculate_snapshot_times(video_info: VideoInfo, avoid_leading: bool = True, avoid_ending: bool = True, snapshot_count=4, skip_seconds_from_head=0, discard_seconds_from_end=1) -> List[int]:
    """
    Calculate evenly spaced snapshot times for a video based on its duration, taking into account the specified parameters for skipping time at the beginning, 
    avoiding snapshots at the beginning and/or end, and the total number of snapshots to capture.

    The function adjusts the snapshot times to ensure that the desired number of snapshots are spaced as evenly as possible, 
    while allowing for some flexibility in the starting and ending points of the video.

    Args:
        video_info (VideoInfo): An object containing metadata about the video, including its total duration in seconds. 
                                 It must have a `duration` attribute representing the video length in seconds.
        snapshot_count (int, optional): The number of snapshots to capture. Defaults to 4.
        avoid_leading (bool, optional): Whether to skip the first snapshot (leading snapshot). Defaults to True.
        avoid_ending (bool, optional): Whether to skip the last snapshot (ending snapshot). Defaults to True.
        skip_seconds_from_head (int, optional): The number of seconds to skip from the beginning of the video before taking the first snapshot. Defaults to 0.
        discard_seconds_from_end (int, optional): The number of seconds to disregard from the end of the video when calculating snapshot intervals. Defaults to 0.

    Returns:
        List[int]: A list of integers representing the times (in seconds) at which to capture each snapshot, spaced evenly throughout the adjusted video duration.
    """

    duration = video_info.duration
    start_time = skip_seconds_from_head
    end_time = duration - discard_seconds_from_end
    interval_count = (snapshot_count - 1 + int(avoid_leading) + int(avoid_ending))
    snapshot_interval = math.floor((end_time - start_time) / interval_count)
    snapshot_times: List[int] = [start_time + i *
                                 snapshot_interval for i in range(int(avoid_leading), interval_count+int(not avoid_ending))]
    # print(duration, snapshot_times)

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

    width, height = video_info.width, video_info.height
    aspect_ratio = width / height

    if target_width and not target_height:
        target_height = int(target_width / aspect_ratio)
    elif target_height and not target_width:
        target_width = int(target_height * aspect_ratio)
    elif not target_height and not target_width:
        target_height = height
        target_width = width

    def _get_snapshot(snap_at: int, video_info: VideoInfo) -> ImageType:
        hhmmss = f"{snap_at // 3600:02}:{(snap_at % 3600) // 60:02}:{snap_at % 60:02}"

        output = subprocess.Popen(
            ["ffmpeg", "-ss", hhmmss,
             "-i", video_info.file_path,
             "-map", f"0:v:{video_info.current_video_stream_index}",
             "-skip_frame", "nokey", "-frames:v", "1", "-q:v", "2", "-f", "image2pipe", "-vcodec", "png", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # print(f"[{idx+1}/{len(snapshot_times)}] snapshot(s) taken.")
        stdout, _ = output.communicate()
        image = Image.open(io.BytesIO(stdout))
        return image

    def _get_snapshots(snapshot_times: List[int], video_info: VideoInfo) -> List[ImageType]:
        with ThreadPoolExecutor() as executor:
            images = list(executor.map(lambda time: _get_snapshot(time, video_info), snapshot_times))
        return images

    snapshots = _get_snapshots(snapshot_times, video_info)
    snapshots_copy = []

    if target_height != height and target_width != width:
        for image in snapshots:
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

            snapshots_copy.append(image)
        snapshots = snapshots_copy

    return snapshots


def _image_histogram(image: ImageType) -> ImageType: ...


def _image_complexity(image: ImageType): ...


def create_scan_image(images: List[ImageType], grid: Tuple[int, int], snapshottimes: List[int], video_info: VideoInfo, logofile: str, config_manager: ConfigManager, use_new_method: bool) -> ImageType:
    """
    Create a composite scan image by arranging snapshots in a grid format with metadata and a logo overlay.

    Args:
        images (List[ImageType]): List of snapshot images to arrange in the scan image.
        grid (Tuple[int, int]): Number of columns and rows for arranging images in the scan image.
        snapshottimes (List[int]): List of snapshot times (in seconds) for each image to display as timestamps.
        video_info (VideoInfo): Metadata about the video, including file, video, audio, and subtitle information.
        logofile (str): Path to the logo image file to place in the top-right corner.
        config_manager (ConfigManager): Manage the settings about text rendering.
        use_new_method (bool): True for use new method in class `TextDrawer` to draw text, and False for old method.

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

    # font_1 = ImageFont.truetype(fontfile_1, 45)
    # font_2 = ImageFont.truetype(fontfile_2, 40)

    if len(images) != total_images:
        raise ValueError(
            f"Image count ({len(images)}) does not match the grid count ({total_images}).")

    # The width is directly associated with drawing information,
    # should not be variable before the info grid become flexible.
    
    canvas_width = 3200

    scan_width, scan_height = images[0].size
    image_width = canvas_width // col
    image_height = math.floor(scan_height / scan_width * image_width)
    canvas_height = image_height * row + 450

    scan_image = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(scan_image)
    
    text_drawer = TextDrawer(video_info=video_info, draw=draw, config_manager=config_manager, use_new_method=use_new_method)
    text_drawer.draw_text()

    time_font = text_drawer.get_time_font()
    y_offset = 450
    for idx, image in enumerate(images):

        grid_x = (idx % col) * image_width
        grid_y = (idx // col) * image_height + y_offset

        image_resized = image.resize((image_width, image_height), Resampling.LANCZOS)
        scan_image.paste(image_resized, (grid_x, grid_y))

        snapshot_time = str(timedelta(seconds=snapshottimes[idx]))
        text_bbox = draw.textbbox((0, 0), snapshot_time, font=time_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        timestamp_x = grid_x + (image_width - text_width) // 2
        timestamp_y = grid_y - (text_height // 2) + 10

        background = Image.new(
            "RGBA", (text_width, text_height), (0, 0, 0, int(255 * 0.6)))
        scan_image.paste(background, (timestamp_x, timestamp_y+14), background)
        draw.text((timestamp_x, timestamp_y), snapshot_time,
                  fill=(255, 255, 255, int(255 * 0.6)), font=time_font)

    logo = Image.open(logofile).resize((405, 405), Resampling.LANCZOS)

    logo_x = scan_image.width - logo.width - 22
    logo_y = 22

    scan_image.paste(logo, (logo_x, logo_y), logo.convert("RGBA"))

    return scan_image


def main():
    """
    Main script execution for generating a video scan image with snapshots and metadata overlay.

    This function guides the user through the following process:
        1. Prompts the user for the video file path and checks the existence of required files (video, fonts, and logo).
        2. Retrieves detailed video information, such as duration and resolution, and calculates the appropriate snapshot times.
        3. Captures snapshots from the video at evenly spaced intervals, resizing each snapshot to 800x450 colorels.
        4. Creates a scan image consisting of a 4x4 grid of snapshots with metadata and a logo overlay.
        5. Optionally resizes the final scan image to a smaller resolution (scaled by a configurable factor) before saving.

    Inputs:
        - file_path (str): Path to the video file provided by the user.
        - font_file (str): Path to a serif font file for metadata text.
        - font_file_2 (str): Path to a sans-serif font file for secondary text.
        - logo_file (str): Path to the logo image file to overlay on the scan.
        - resize_scale (int): Scaling factor for resizing the final scan image (e.g., 2 to reduce by half).
        - avoid_leading (bool): Flag to avoid including the very beginning of the video for snapshots.
        - avoid_ending (bool): Flag to avoid including the very end of the video for snapshots.
        - grid_shape (tuple): Grid size for the snapshot arrangement, typically a 4x4 grid.

    Outputs:
        - Saves the final scan image to a "scans" directory with a timestamped filename.
        - The image is saved as a PNG file, containing the arranged snapshots and metadata.

    Raises:
        - FileNotFoundError: If any required file (video, fonts, or logo) does not exist.
        - ValueError: If there are issues retrieving video information, taking snapshots, or creating the scan image.
        - IOError: If there are errors when saving the final scan image.

    Example:
        The user provides a path to a video, and the script outputs a scan image file named with the current time and video filename.
    """

    # chcp 65001
    try:
        config_manager: ConfigManager = ConfigManager()
        config_manager.activate_config("basic")

        font_file: str = config_manager["font_file"]
        font_file_2: str = config_manager["font_file_2"]
        logo_file: str = config_manager["logo_file"]
        resize_scale: int = config_manager["resize_scale"]
        avoid_leading: bool = config_manager["avoid_leading"]
        avoid_ending: bool = config_manager["avoid_ending"]
        grid_shape: tuple[int, int] = tuple(config_manager["grid_shape"])
        use_new_method: bool = True

        file_path: str = input("File Path :")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"input file: {file_path} no found")

    except (FileNotFoundError, ValueError) as e:
        # 此处的 Exception 均为预定触发
        print(e)
        exit(1)

    try:
        video_info = get_video_info(file_path)
        print(video_info)

        if video_info:

            # 多视频流处理
            if (video_stream_count := len(video_info.video_streams)) > 1:
                print(f"\nThere are {video_stream_count} video streams available.")
                while True:
                    try:
                        selected_stream_index = int(input(f"Enter a number between 0 and {video_stream_count - 1}: "))
                        video_info.set_active_video_stream(selected_stream_index)
                        print(f"Video stream {selected_stream_index} activated.")
                        break
                    except (ValueError, IndexError):
                        print(f"Invalid input. Please enter a valid integer between 0 and {video_stream_count - 1}.")
                        continue

            snapshot_times = calculate_snapshot_times(
                video_info, avoid_leading, avoid_ending,
                snapshot_count=grid_shape[0] * grid_shape[1]
            )

            # 默认情况下，返回原始截图，缩放工作由`reate_scan_image`进行
            snapshots = take_snapshots(video_info, snapshot_times)

            scan = create_scan_image(snapshots, grid_shape, snapshot_times,
                                     video_info, logo_file, config_manager, use_new_method)

            w, h = scan.size
            scan = scan.resize((w//resize_scale, h//resize_scale), Resampling.LANCZOS)
            scan.save(f"scans/{datetime.now().strftime('%H%M%S')}.scan.{video_info.file_name}.png")

        else:
            print("Failed to retrieve video information.")

    except IndexError as e:
        print(e)
        exit(1)

    except (FileNotFoundError, ValueError, IndexError) as e:
        print(e)
        exit(1)


if __name__ == '__main__':
    main()
