from typing import List, Tuple, Dict
from PIL import ImageFont
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont
import os
import copy

from VideoInfo import VideoInfo
from ConfigManager import ConfigManager

class TextDrawer:
    """
    A class to manage and draw text within a grid layout on an image. The class supports two modes of 
    handling long text (truncation or wrapping). It also manages the structure and organization of text data 
    for the grid.
    
    Params:
        Style:
            shade_offset (Tuple): A tuple representing the offset for the shadow, typically in (x, y) format.
            text_color (Tuple): A tuple representing the color of the text in RGB format.
            shade_color (Tuple): A tuple representing the color of the shadow in RGB format.
            font_list (List[FreeTypeFont]): Font list(font size inside).
        
        Layout:
            horizontal_spacing (float): Horizontal spacing between columns
            vertical_spacing (float): Vertical spacing between rows
            title_margin_left (float): Adjust its distance from the left edge.
            title_margin_top (float): Adjust its distance from the top edge.
            content_margin_left (float): Adjust its distance from the left edge.
            content_margin_top (float): Adjust its distance from the top edge.
        
        Hardcode:
            scan_image_width (float): 3200, associated with `canvas_width` in `create_scan_image`, need change in later update.
            logo_width (float): 405, also associated with someone, make it variable in later update.
            post_list (List): Only used by the old method.
    """ 

    def __init__(self, video_info: VideoInfo, draw: ImageDrawType, config_manager: ConfigManager, use_new_method: bool) -> None:
        """
        Initializes a TextDrawer object with the given title, content, and grid shape.

        Args:
            video_info (VideoInfo): Metadata about the video, including file, video, audio, and subtitle information.
            draw (ImageDrawType): The ImageDraw object used to draw the text.
            config_manager (ConfigManager): Manage the settings about text rendering.
            use_new_method (bool): True for use new method to draw text, and False for old method.
        """
        config_manager.activate_config("info_layout")
        layout = config_manager.config
        
        # associated with `canvas_width` in `create_scan_image`, need change in later update
        self.scan_image_width = 3200
        # also associated with someone, make it variable in later update
        self.logo_width = 405

        # used by new method, overwrite
        self.shade_offset = tuple(layout["shade_offset"])
        self.text_color = tuple(layout["text_color"])
        self.shade_color = tuple(layout["shade_color"])
        self.vertical_spacing = layout["vertical_spacing"]
        self.horizontal_spacing = layout["horizontal_spacing"]    # Vertical spacing between rows
        self.content_margin_left = layout["content_margin_left"]
        self.content_margin_top = layout["content_margin_top"]
        self.title_margin_left = layout["title_margin_left"]
        self.title_margin_top = layout["title_margin_top"]
        
        # only used by old method
        self.pos_list = layout["pos_list"]
        
        available_font_list: List[FreeTypeFont] = []
        available_font_list = self._get_fonts(layout)
        # output by `self.get_time_font()`
        self.time_font = available_font_list[layout["time_font"]]

        # Parsing the `text_list` and setting it back to the config
        self.old_content: List[List[str]] = self._parse_text_list(layout["text_list"], video_info)
        self.title: str = self.old_content[0][0]
        self.content: List[List[str]] = copy.deepcopy(self.old_content[1:])

        # 验证index
        self.font_list: List[FreeTypeFont] = self._parse_font_list(layout["font_list"], available_font_list)
        if len(self.font_list) != len(self.content) + 1:
            raise IndexError(f"The length of font_list({len(self.font_list)}) does not match the number of coloum({len(self.content) + 1})")
        
        self.draw: ImageDrawType = draw
        self.use_new_method: bool = use_new_method
        
        # The size of the limit for the entire text rendering area
        self.max_text_width: float = self.scan_image_width - self.logo_width - self.content_margin_left
        self.max_text_height: float = 450 - self.content_margin_top - self.vertical_spacing 
        # TODO: the inline number 450, associated with `y_offset` in `creat_scan_image`
        
        # update by `self.calculate_content_width_height()`
        # same shape as `self.content`
        self.content_width: List[List[float]] = []
        self.content_height: List[List[float]] = []
        self._calculate_content_width_height()
        self.chinese_char_height: List[float] = [draw.textbbox((0, 0), "田", font=font)[3] for font in self.font_list]
        self.ellipsis_width: List[float] = [self.horizontal_spacing + draw.textbbox((0, 0), "...", font=font)[2] for font in self.font_list]
        self.max_rows_each_column: List[int] = [self.max_text_height // (chinese_height + self.vertical_spacing) for chinese_height in self.chinese_char_height]
        
        self.column_widths: List[float] = [0] * len(self.content)
        self._allocate_column_widths()
        
        # Store start positions for text drawing
        self.content_start: List[List[Tuple[int, int]]] = []
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
                bbox = self.draw.textbbox((0, 0), text, font=self.font_list[col_idx+1])
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
            # horizontal_spacing / 2 是期望标题列与对应信息列的间距稍小一点
            self.column_widths[col_idx] = max(self.content_width[col_idx][1:]) + self.horizontal_spacing / 2

        while True:
            required_width = sum(max(self.content_width[i]) for i in range(1, number_of_column, 2))
            remaining_width = self.max_text_width - sum(self.column_widths)
            
            if required_width + self.horizontal_spacing * number_of_column / 2 < remaining_width:
                for col_idx in range(1, number_of_column, 2):
                    self.column_widths[col_idx] = max(self.content_width[col_idx]) + (remaining_width - required_width) / number_of_column * 2 
                break
            else:
                text_lengths = []
                for col_idx in range(1, number_of_column, 2):
                    for row_idx, text in enumerate(self.content[col_idx]):
                        text_lengths.append((col_idx, row_idx, self.content_width[col_idx][row_idx]))  # store (col_idx, row_idx, width)
                
                # Sort text_lengths by width in descending order and pick top 2 longest (not in the same column)
                text_lengths.sort(key=lambda x: x[2], reverse=True)
                longest_texts: List[Tuple[int, int, float]] = []
                longest_texts.append(text_lengths[0])
                i = 1
                while text_lengths[i][0] == text_lengths[0][0]:
                    i += 1
                longest_texts.append(text_lengths[i])
                
                sum_ellipsis_width = 0
                for col_idx, row_idx, width in longest_texts:
                    # 0 is for title, so +1
                    sum_ellipsis_width += self.ellipsis_width[col_idx+1]
                excess_width = required_width - remaining_width + sum_ellipsis_width + self.horizontal_spacing * number_of_column / 2
                # 尝试将最长的2个文本长度降低到此值
                shorten_target = (sum(width for _, _, width in longest_texts) - excess_width) / 2
                
                for col_idx, row_idx, _ in longest_texts:
                    str_to_change: str = self.content[col_idx][row_idx]
                    # 提取每一个字符
                    str_every_char: List[str] = [i for i in str_to_change]
                    font = self.font_list[col_idx+1]
                    # 每个字符分别计算一次宽度
                    width_every_char: List[float] = [self.draw.textbbox((0, 0), str_, font=font)[2] for str_ in str_every_char]
                    # 依次从头累加，得到到某一个字符为止的宽度
                    width_to_idx: List[float] = [sum(width_every_char[:i+1]) for i in range(len(width_every_char))]
                    # 这是另一种方法计算的长度，他们的结果有差异但是不大，时间开销差异无法感知到
                    # width_to_idx_other: List[float] = [self.draw.textbbox((0, 0), str_to_change[:i+1], font=font)[2] for i in range(len(str_to_change))]
                    # 剩余多少行可供挥霍
                    extra_lines: int = self.max_rows_each_column[col_idx] - len(self.content[col_idx]) 
                    if extra_lines <= 0:
                        # can't creat a new line, just truncate
                        original_text = self.content[col_idx][row_idx]
                        shorten_index = max((i for i, num in enumerate(width_to_idx) if num < shorten_target), default=0)
                        truncated_text = original_text[:shorten_index] + "..."
                        self.content[col_idx][row_idx] = truncated_text
                    else:
                        # attemp to warp
                        last_shorten_index = 0
                        last_idx_extra = 0
                        for idx_extra in range(extra_lines - 1):
                            original_text = self.content[col_idx][row_idx + idx_extra]
                            shorten_index = 1 + max((i for i, num in enumerate(width_to_idx) if num < shorten_target), default=0)
                            # 换行后，这一行的长度
                            width_this_row = width_to_idx[shorten_index-1]
                            truncated_text = original_text[last_shorten_index: shorten_index]
                            self.content[col_idx].insert(row_idx + idx_extra, truncated_text)
                            # 这是前面的信息栏，需要空一行
                            self.content[col_idx-1].insert(row_idx + idx_extra + 1, "")
                            last_shorten_index = shorten_index
                            width_to_idx[:] = [num - width_this_row for num in width_to_idx]
                            
                            # 外面还有一次写入，用于处理最后一行（省略或无需省略）
                            if ((width_to_idx[-1] < shorten_target) | (idx_extra == extra_lines - 2)):
                                last_idx_extra = idx_extra + 1
                                break
                        
                        # 前面idx_extra的最后一次未完成的处理
                        idx_extra = last_idx_extra
                        if width_to_idx[-1] >= shorten_target:
                            # 还是要省略
                            original_text = self.content[col_idx][row_idx + idx_extra]
                            shorten_index = max((i for i, num in enumerate(width_to_idx) if num < shorten_target), default=0)
                            truncated_text = original_text[last_shorten_index: shorten_index] + "..."
                            self.content[col_idx][row_idx + idx_extra] = truncated_text
                            
                        else:
                            original_text = self.content[col_idx][row_idx + idx_extra]
                            truncated_text = original_text[last_shorten_index:]
                            self.content[col_idx][row_idx + idx_extra] = truncated_text
                    # if extra_lines <= 0
                self._calculate_content_width_height()
            # if required_width + self.horizontal_spacing * number_of_column / 2 < remaining_width
            # * In the 'else', we don't(can't) change column_widths because of `required_widths`.
        # while True, break 

    def _calculate_content_start(self) -> None:
        # Origin of content is (Ox, Oy) and it will change
        Ox = self.content_margin_left
        for col_idx, col in enumerate(self.content):
            Oy = self.content_margin_top
            self.content_start.append([])
            for row_idx, text in enumerate(col):
                self.content_start[col_idx].append((int(Ox), int(Oy)))
                Oy += self.chinese_char_height[col_idx+1] + self.vertical_spacing
                
            Ox += self.column_widths[col_idx]

    # TODO: 分离读取、转换和验证步骤
    @staticmethod
    def _parse_text_list(text_list: List[List[str | Dict[str, str]]], video_info: VideoInfo) -> List[List[str]]:
        parsed_list: List[List[str]] = []
        for row in text_list:
            parsed_row: List[str] = []
            for item in row:
                if isinstance(item, dict) and "field" in item and "key" in item:
                    parsed_row.append(video_info[item["field"]][item["key"]])
                elif isinstance(item, str):
                    parsed_row.append(item)
                else:
                    raise ValueError(f"Not support text_list item:{item}")
            parsed_list.append(parsed_row)
        return parsed_list

    @staticmethod
    def _parse_font_list(font_idx_list: List[str], font_list: List[FreeTypeFont]) -> List[FreeTypeFont]:
        parsed_list: List[FreeTypeFont] = []
        for idx in font_idx_list:
            if isinstance(idx, int):
                parsed_list.append(font_list[idx])
        return parsed_list

    @staticmethod
    def _get_fonts(layout) -> List[FreeTypeFont]:
        available_font_list: List[FreeTypeFont] = []
        for font in layout["fonts"]:
            if isinstance(font, dict) and "path" in font and "size" in font \
                    and os.path.exists(font["path"]) and isinstance(font["size"], int):
                available_font_list.append(ImageFont.truetype(font["path"], font["size"]))
            else:
                raise ValueError(f"{font} is not support")
        return available_font_list
    
    def get_time_font(self) -> FreeTypeFont:
        """
        This font is used outside, by parsed in this class.
        """
        return self.time_font

    def draw_text(self) -> None:
        if self.use_new_method:
            self._draw_text_with_shadow((self.title_margin_left, self.title_margin_top), self.title, self.font_list[0])
            for col_idx, col in enumerate(self.content):
                for row_idx, text in enumerate(col):
                    self._draw_text_with_shadow(self.content_start[col_idx][row_idx], text, self.font_list[col_idx+1])
        else:
            for i, j, k in zip(self.old_content, self.pos_list, self.font_list):
                self._multiline_text_with_shade(self.draw, "\n".join(i), j, self.shade_offset, self.vertical_spacing, k, self.text_color, self.shade_color)

    def _draw_text_with_shadow(self, pos: Tuple[int, int], text: str, font: FreeTypeFont) -> None:
        dx, dy = self.shade_offset
        x, y = pos
        self.draw.text((x+dx, y+dy), text, fill=self.shade_color, font=font)
        self.draw.text((x, y), text, fill=self.text_color, font=font)
        
    @staticmethod
    def _multiline_text_with_shade(
        draw_obj: ImageDrawType, text: str,
        pos: Tuple[int, int], offset: Tuple[int, int], spacing: int,
        font: FreeTypeFont, text_color: Tuple[int, int, int], shade_color: Tuple[int, int, int]
    ) -> None:
        """
        Draw multiline text with a shaded background on the image.
        The old method to draw multitext, without change.

        Args:
            draw_obj (ImageDrawType): The ImageDraw object used to draw the text.
            text (str): The text to be drawn.
            pos (Tuple[int, int]): The starting position (x, y) for the text.
            offset (Tuple[int, int]): The offset for drawing the shaded background behind the text.
            spacing (int): The spacing between lines of text.
            font (FreeTypeFont): The font to be used for drawing the text.
            text_color (Tuple[int, int, int]): The color of the text.
            shade_color (Tuple[int, int, int]): The color of the shaded background.

        Returns:
            None: This function does not return any value; it directly modifies the `draw_obj`.
        """

        x, y = pos
        dx, dy = offset
        draw_obj.multiline_text((x+dx, y+dy), text, fill=shade_color, font=font, spacing=spacing)
        draw_obj.multiline_text((x, y), text, fill=text_color, font=font, spacing=spacing)

        return None
