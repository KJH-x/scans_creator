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
        spacing = 10
        shade_offset = (2, 2)
        text_color = (0, 0, 0)
        shade_color = (49, 49, 49)
        content_margin_left = 30
        content_margin_top = 100
        title_margin_left = 30
        title_margin_top = 10
        

    def __init__(self, video_info: VideoInfo, draw: ImageDrawType, font: FreeTypeFont) -> None:
        """
        Initializes a TextDrawer object with the given title, content, and grid shape.

        Args:
        """
        
        self.draw: ImageDrawType = draw
        self.font: FreeTypeFont = font
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
        
        # update by `self.calculate_content_width_height()`
        self.content_width: List[List[float]] = []
        self.content_height: List[List[float]] = []
        self._calculate_content_width_height()
        
        # Store start positions for text drawing
        self.content_start: List[List[Tuple[float, float]]] = [] 
        self.calculate_content_start() 
        

    def _calculate_content_width_height(self) -> None:
        """
        Calculate the width and height of text in the content.
        """
        for col_idx, col in enumerate(self.content):
            self.content_width.append([])
            self.content_height.append([])
            for _, text in enumerate(col):
                bbox = self.draw.textbbox((0, 0), text, font=self.font)
                self.content_width[col_idx].append(bbox[2])
                self.content_height[col_idx].append(bbox[3])
                
    def calculate_content_start(self) -> None:
        # Origin of content is (Ox, Oy)
        Ox = self.Defaults.content_margin_left
        for col_idx, col in enumerate(self.content):
            Oy = self.Defaults.content_margin_top
            self.content_start.append([])
            for row_idx, text in enumerate(col):
                self.content_start[col_idx].append((Ox, Oy))
                # Oy += self.content_height[col_idx][row_idx] + self.Defaults.spacing
                Oy += 50
                
            if col_idx % 2 == 0:
                Ox += min(self.content_width[col_idx]) + 10
            else:
                Ox += max(self.content_width[col_idx]) + 40
            
    
    def draw_text(self) -> None:
        self._draw_text_with_shadow((self.Defaults.title_margin_left, self.Defaults.title_margin_top), self.title)
        for col_idx, col in enumerate(self.content):
            for row_idx, text in enumerate(col):
                self._draw_text_with_shadow(self.content_start[col_idx][row_idx], text)

    def _draw_text_with_shadow(self, pos: Tuple[int, int], text: str) -> None:
        dx, dy = self.Defaults.shade_offset
        x, y = pos
        self.draw.text((x+dx, y+dy), text, fill=self.Defaults.shade_color, font=self.font)
        self.draw.text((x, y), text, fill=self.Defaults.text_color, font=self.font)
