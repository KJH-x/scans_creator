import copy
import math
from datetime import timedelta
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ImageType
from PIL.Image import Resampling
from PIL.ImageFont import FreeTypeFont

from ..core.config_manager import config_manager
from ..core.video_info import VideoInfo
from ..models.info_layout import TextField
from .container import FlexContainer
from .element_base import ElementMargin, ImageElement, TextElement


def render_scan_image(
    images: List[ImageType], grid: Tuple[int, int], snapshottimes: List[int], video_info: VideoInfo
) -> ImageType:
    """
    Create a composite scan image by arranging snapshots in a grid format with metadata and a logo overlay.

    Args:
        images (List[ImageType]): List of snapshot images to arrange in the scan image.
        grid (Tuple[int, int]): Number of columns and rows for arranging images in the scan image.
        snapshottimes (List[int]): List of snapshot times (in seconds) for each image to display as timestamps.
        video_info (VideoInfo): Metadata about the video, including file, video, audio, and subtitle information.

    Raises:
        ValueError: If the number of `images` does not match the required number based on `grid`.

    Returns:
        ImageType: A PIL Image object of the completed scan image, with:
            - A metadata section for video, audio, and subtitle details.
            - Snapshot images arranged in a grid with timestamps.
            - A logo in the top-right corner.
    """
    canvas_width = config_manager.layout.canvas_width

    col, row = grid
    total_images = col * row
    if len(images) != total_images:
        raise ValueError(f"Image count ({len(images)}) does not match the grid count ({total_images}).")

    # * Define header layout
    shade_offset = config_manager.layout.shade_offset
    text_color = tuple(config_manager.layout.text_color)
    shade_color = tuple(config_manager.layout.shade_color)

    available_font_list: List[FreeTypeFont] = [
        ImageFont.truetype(font.path, font.size) for font in config_manager.config.fonts
    ]

    time_font = available_font_list[config_manager.layout.time_font]

    full_contents: List[List[str]] = _parse_text_list(config_manager.layout.text_list, video_info)
    title: str = full_contents[0][0]
    contents: List[List[str]] = copy.deepcopy(full_contents[1:])

    root = FlexContainer(
        direction="row",
        align="start",
        spacing=10,
        margin=ElementMargin(22, 22, 100, 22),
    )

    container_main = FlexContainer(direction="column", spacing=22, flex_grow=1)
    root.add(container_main)
    root.add(ImageElement(Image.open(config_manager.config.logo_file).resize((405, 405), Resampling.LANCZOS)))

    container_main.add(
        TextElement(
            title,
            available_font_list[config_manager.layout.font_list[0]],
            line_spacing=4,
            color=text_color,
            shadow_color=shade_color,
            shadow_offset=shade_offset,
        )
    )

    container_metadata = FlexContainer(direction="row", align="justify", spacing=25)
    for i in range(len(contents) // 2):
        container_column = FlexContainer(direction="column", spacing=10)
        for label, content in zip(contents[2 * i], contents[2 * i + 1]):
            label_element = TextElement(
                label,
                font=available_font_list[config_manager.layout.font_list[2 * i + 1]],
                color=text_color,
                shadow_color=shade_color,
                shadow_offset=shade_offset,
                no_flex_shrink=True,
            )
            content_element = TextElement(
                content,
                font=available_font_list[config_manager.layout.font_list[2 * i + 2]],
                color=text_color,
                shadow_color=shade_color,
                shadow_offset=shade_offset,
            )
            container_column.add(FlexContainer([label_element, content_element], direction="row", spacing=6))
        container_metadata.add(container_column)
    container_main.add(container_metadata)

    # * Calculate layout and canvas size
    root.layout(max_width=canvas_width)
    root.measure()  # Update all child element sizes manually before calculating flex-grow
    root.width = canvas_width  # Set the target size for the root element (IMPORTANT)
    root.calc_flex_grow()

    scan_width, scan_height = images[0].size
    image_width = canvas_width // col
    image_height = math.floor(scan_height / scan_width * image_width)
    canvas_height = image_height * row + root.height + root.margin.y

    # * Render
    scan_image = Image.new("RGB", (canvas_width, canvas_height), "white")
    root.render(scan_image)
    draw = ImageDraw.Draw(scan_image)

    y_offset = root.height + root.margin.y
    for idx, image in enumerate(images):

        grid_x = (idx % col) * image_width
        grid_y = (idx // col) * image_height + y_offset

        image_resized = image.resize((image_width, image_height), Resampling.LANCZOS)
        scan_image.paste(image_resized, (grid_x, grid_y))

        snapshot_time = str(timedelta(seconds=snapshottimes[idx]))
        text_bbox = draw.textbbox((0, 0), snapshot_time, font=time_font)
        text_width = int(text_bbox[2] - text_bbox[0])
        text_height = int(text_bbox[3] - text_bbox[1])
        timestamp_x = grid_x + (image_width - text_width) // 2
        timestamp_y = grid_y - (text_height // 2) + 10

        background = Image.new("RGBA", (text_width, text_height), (0, 0, 0, int(255 * 0.6)))
        scan_image.paste(background, (timestamp_x, timestamp_y + 14), background)
        draw.text((timestamp_x, timestamp_y), snapshot_time, fill=(255, 255, 255, int(255 * 0.6)), font=time_font)

    return scan_image


# TODO: 分离读取、转换和验证步骤
def _parse_text_list(text_list: List[List[str | TextField]], video_info: VideoInfo) -> List[List[str]]:
    parsed_list: List[List[str]] = []
    video_info_dict = video_info.to_dict()

    for row in text_list:
        parsed_row: List[str] = []
        for item in row:
            if isinstance(item, TextField):
                parsed_row.append(video_info_dict[item.field][item.key])
            elif isinstance(item, str):
                parsed_row.append(item)
            else:
                raise ValueError(f"Unsupported item in text_list: {item!r}")
        parsed_list.append(parsed_row)
    return parsed_list
