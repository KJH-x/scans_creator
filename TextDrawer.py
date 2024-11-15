from typing import List, Tuple
from PIL import ImageFont
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont

from VideoInfo import VideoInfo

class TextDrawer:
    """
    A class to manage and draw text within a grid layout on an image. The class supports two types of grid layouts and
    two modes of handling long text (truncation or wrapping). It also manages the structure and organization of text data 
    for the grid.
    """
    
    class Defaults:
        """
        A nested class to store various default settings for text rendering and grid layout.
        """
        horizontal_spacing = 10.0  # Horizontal spacing between columns
        vertical_spacing = 10.0    # Vertical spacing between rows
        shade_offset = (2, 2)
        text_color = (0, 0, 0)
        shade_color = (49, 49, 49)
        content_margin_left = 30
        content_margin_top = 100
        title_margin_left = 30
        title_margin_top = 10
        
        # associated with `canvas_width` in `create_scan_image`, need change in later update
        scan_image_width = 3200
        # also associated with someone, make it variable in later update
        logo_width = 405
        

    def __init__(self, video_info: VideoInfo, draw: ImageDrawType, font_1: FreeTypeFont, font_2: FreeTypeFont) -> None:
        """
        Initializes a TextDrawer object with the given title, content, and grid shape.

        Args:
        """
        
        self.draw: ImageDrawType = draw
        self.font_title: FreeTypeFont = font_1
        self.font_content: FreeTypeFont = font_2
        self.title: str = video_info["F"]["name"]
        self.content: List[List[str]] = [
            [
                "　　　　【文件信息】",
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
                "　　　　【视频信息】",
                "编　　码：",
                "色　　彩：",
                "尺　　寸：",
                "帧　　率：",
            ],
            [
                "",
                video_info["V"]["codec"],
                video_info["V"]["color"],
                video_info["V"]["frameSize"],
                video_info["V"]["frameRate"],
            ],
            [
                "　　　　【音频信息】",
                "编　　码：",
                "音频语言：",
                "音频标题：",
                "声　　道：",
            ],
            [
                "",
                video_info["A"]["codec"],
                video_info["A"]["lang"],
                video_info["A"]["title"],
                video_info["A"]["channel"],
            ],
            [
                "　　　【字幕信息】",
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
        
        # The size of the limit for the entire text rendering area
        self.max_text_width: float = self.Defaults.scan_image_width - self.Defaults.logo_width - self.Defaults.content_margin_left
        self.max_text_height: float = 450 - self.Defaults.content_margin_top - self.Defaults.vertical_spacing # TODO: the inline number 450
        
        # update by `self.calculate_content_width_height()`
        # same shape as `self.content`
        self.content_width: List[List[float]] = []
        self.content_height: List[List[float]] = []
        self._calculate_content_width_height()
        self.chinese_char_height: float = draw.textbbox((0, 0), "田", font=self.font_content)[3]
        self.ellipsis_width: float = self.Defaults.horizontal_spacing + draw.textbbox((0, 0), "...", font=self.font_content)[2]
        
        self.column_widths: List[float] = [0] * len(self.content)
        self._allocate_column_widths()
        
        # Store start positions for text drawing
        self.content_start: List[List[Tuple[float, float]]] = []
        self._calculate_content_start() 

    def _calculate_content_width_height(self) -> None:
        """
        Calculate the width and height of text in the content.
        """
        self.content_width: List[List[float]] = []
        self.content_height: List[List[float]] = []
        for col_idx, col in enumerate(self.content):
            self.content_width.append([])
            self.content_height.append([])
            for _, text in enumerate(col):
                bbox = self.draw.textbbox((0, 0), text, font=self.font_content)
                self.content_width[col_idx].append(bbox[2])
                self.content_height[col_idx].append(bbox[3])

    def _allocate_column_widths(self) -> None:
        """
        Allocate the width for each column in the grid based on the maximum width of each column's text.
        
        The maximum width for each column is determined by the longest text in that column.
        The width is then stored in the member variable `column_widths`.
        """
        number_of_column = len(self.content)
        for col_idx in range(0, number_of_column, 2):
            # These cols are usually 5 characters wide (except the first row)
            self.column_widths[col_idx] = max(self.content_width[col_idx][1:]) + self.Defaults.horizontal_spacing

        while True:
            required_width = sum(max(self.content_width[i]) for i in range(1, number_of_column, 2))
            remaining_width = self.max_text_width - sum(self.column_widths)
            
            if required_width + self.Defaults.horizontal_spacing * number_of_column / 2 < remaining_width:
                for col_idx in range(1, number_of_column, 2):
                    self.column_widths[col_idx] = max(self.content_width[col_idx]) + (remaining_width - required_width) / number_of_column * 2 
                break
            else:
                n = 2
                text_lengths = []
                for col_idx in range(1, number_of_column, 2):
                    for row_idx, text in enumerate(self.content[col_idx]):
                        text_lengths.append((col_idx, row_idx, self.content_width[col_idx][row_idx]))  # store (col_idx, row_idx, width)
                
                # Sort text_lengths by width in descending order and pick top n longest
                text_lengths.sort(key=lambda x: x[2], reverse=True)
                longest_texts = text_lengths[:n]
                
                # Now calculate how much we need to shorten these texts
                # * the `3 * ()` is magic number to avoid endless loop temporarily
                excess_width = required_width - remaining_width + 3 * (self.ellipsis_width * n + self.Defaults.horizontal_spacing * number_of_column / 2)
                # TODO: If they are in the same column?
                shorten_factor = excess_width / sum(width for _, _, width in longest_texts) 
                
                # Replace the longest n texts with shortened versions
                for col_idx, row_idx, _ in longest_texts:
                    original_text = self.content[col_idx][row_idx]
                    # ! Sometimes there may be an endless loop here and needs to be optimized
                    # * It is based on lenth, but a chinese char is wider than an english char
                    truncated_text = original_text[:int(len(original_text) * (1 - shorten_factor))] + "..."
                    self.content[col_idx][row_idx] = truncated_text
                self._calculate_content_width_height()
                    
                # * In the 'else', we don't(can't) change column_widths because of `required_widths`.

    def _calculate_content_start(self) -> None:
        # Origin of content is (Ox, Oy) and it will change
        Ox = self.Defaults.content_margin_left
        for col_idx, col in enumerate(self.content):
            Oy = self.Defaults.content_margin_top
            self.content_start.append([])
            for row_idx, text in enumerate(col):
                self.content_start[col_idx].append((Ox, Oy))
                Oy += self.chinese_char_height + self.Defaults.vertical_spacing
                
            Ox += self.column_widths[col_idx]

    def draw_text(self) -> None:
        self._draw_text_with_shadow((self.Defaults.title_margin_left, self.Defaults.title_margin_top), self.title, self.font_title)
        for col_idx, col in enumerate(self.content):
            for row_idx, text in enumerate(col):
                self._draw_text_with_shadow(self.content_start[col_idx][row_idx], text, self.font_content)

    def _draw_text_with_shadow(self, pos: Tuple[int, int], text: str, font: FreeTypeFont) -> None:
        dx, dy = self.Defaults.shade_offset
        x, y = pos
        self.draw.text((x+dx, y+dy), text, fill=self.Defaults.shade_color, font=font)
        self.draw.text((x, y), text, fill=self.Defaults.text_color, font=font)
