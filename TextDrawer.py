import copy
from typing import List, Tuple

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont

from ConfigManager import ConfigManager
from GridBase import ImageCellBase, TextCellBase, TextColumnBase
from models.info_layout import TextField
from VideoInfo import VideoInfo


class TextCell_text(TextCellBase):
    def __init__(
        self,
        draw: ImageDrawType,
        font: FreeTypeFont,
        h_spacing: float,
        v_spacing: float,
        content: str,
        text_color: Tuple[int, int, int],
        shade_color: Tuple[int, int, int],
        shade_offset: Tuple[float, float],
    ) -> None:
        super(TextCell_text, self).__init__(draw, font, h_spacing, v_spacing, content)

        self.text_color = text_color
        self.shade_color = shade_color
        self.shade_offset = shade_offset

    def draw_content(self, pos: Tuple[int, int]) -> None:
        x, y = pos
        dx, dy = self.shade_offset
        self.draw.text((x + dx, y + dy), self.content, fill=self.shade_color, font=self.font)
        self.draw.text((x, y), self.content, fill=self.text_color, font=self.font)


class TextCell_labelText(TextCell_text):
    def __init__(
        self,
        draw: ImageDrawType,
        font: FreeTypeFont,
        h_spacing: float,
        v_spacing: float,
        content: str,
        text_color: Tuple[int, int, int],
        shade_color: Tuple[int, int, int],
        shade_offset: Tuple[float, float],
    ) -> None:
        super(TextCell_labelText, self).__init__(
            draw,
            font,
            h_spacing,
            v_spacing,
            content,
            text_color,
            shade_color,
            shade_offset,
        )

    def cal_width(self) -> None:
        bbox = self.draw.textbbox((0, 0), self.content, font=self.font)
        # 希望这里的间距更小点
        self.width = bbox[2] + self.h_spacing * 0


class TextColumn_labelAndValue(TextColumnBase):
    def __init__(
        self,
        draw: ImageDrawType,
        font: FreeTypeFont,
        h_spacing: float,
        v_spacing: float,
        max_height: float,
    ) -> None:
        super(TextColumn_labelAndValue, self).__init__(draw, font, h_spacing, v_spacing, max_height)

        self.label_cells: List[TextCellBase | ImageCellBase] = []
        # 每一个 label 对应着多少行 value
        self.label_value_map: List[int] = []

    def add_cell(self, new_cell: List[TextCellBase]) -> None:
        self.label_cells.append(new_cell[0])
        if len(new_cell) == 2:
            self.cells.append(new_cell[1])
        elif len(new_cell) > 2:
            self.cells.extend(new_cell[1:])
        else:
            raise IndexError("TextColumnBase.add_cell(): The length of new_cell is too short.")
        self.extra_lines = self.extra_lines - len(new_cell) + 1
        self.label_value_map.append(len(new_cell) - 1)
        self.cal_size()

    def insert_cell(self, origin_cell: TextCellBase, new_cell: TextCellBase) -> None:
        label_idx = 0
        sum_map_value = self.label_value_map[0]
        for idx, cell in enumerate(self.cells):
            if idx >= sum_map_value:
                label_idx += 1
                if label_idx < len(self.label_value_map):
                    sum_map_value += self.label_value_map[label_idx]
                else:
                    sum_map_value += 0

            if cell == origin_cell:
                self.cells.insert(idx + 1, new_cell)
                self.label_value_map[label_idx] += 1

    def cal_width(self) -> None:
        self.value_width = max([cell.width for cell in self.cells])
        self.label_width = max([cell.width for cell in self.label_cells])
        self.width = self.value_width + self.label_width

    def cal_height(self) -> None:
        self.height = sum([cell.height for cell in self.cells])

        for idx, label_cell in enumerate(self.label_cells):
            label_height: float = 0
            for idx_map in range(self.label_value_map[idx]):
                label_height += self.cells[idx + idx_map].height
            # 对于一个label匹配多个value的情况，令其高度对齐
            label_cell.set_height(label_height)


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

    def __init__(
        self,
        video_info: VideoInfo,
        draw: ImageDrawType,
        config_manager: ConfigManager,
        use_new_method: bool,
    ) -> None:
        """
        Initializes a TextDrawer object with the given title, content, and grid shape.

        Args:
            video_info (VideoInfo): Metadata about the video, including file, video, audio, and subtitle information.
            draw (ImageDrawType): The ImageDraw object used to draw the text.
            config_manager (ConfigManager): Manage the settings about text rendering.
            use_new_method (bool): True for use new method to draw text, and False for old method.
        """
        layout = config_manager.layout

        # associated with `canvas_width` in `create_scan_image`, need change in later update
        self.scan_image_width = 3200
        # also associated with someone, make it variable in later update
        self.logo_width = 405

        # used by new method, overwrite
        self.shade_offset = config_manager.layout.shade_offset
        self.text_color = tuple(config_manager.layout.text_color)
        self.shade_color = tuple(config_manager.layout.shade_color)
        self.vertical_spacing = config_manager.layout.vertical_spacing
        self.horizontal_spacing = config_manager.layout.horizontal_spacing  # Vertical spacing between rows
        self.content_margin_left = config_manager.layout.content_margin_left
        self.content_margin_top = config_manager.layout.content_margin_top
        self.title_margin_left = config_manager.layout.title_margin_left
        self.title_margin_top = config_manager.layout.title_margin_top

        # only used by old method
        self.pos_list = config_manager.layout.pos_list
        available_font_list: List[FreeTypeFont] = [
            ImageFont.truetype(font.path, font.size) for font in config_manager.config.fonts
        ]

        # output by `self.get_time_font()`
        self.time_font = available_font_list[config_manager.layout.time_font]

        # Parsing the `text_list` and setting it back to the config
        self.old_content: List[List[str]] = self._parse_text_list(config_manager.layout.text_list, video_info)
        self.title: str = self.old_content[0][0]
        self.content: List[List[str]] = copy.deepcopy(self.old_content[1:])

        # 验证index
        self.font_list: List[FreeTypeFont] = self._parse_font_list(config_manager.layout.font_list, available_font_list)
        if len(self.font_list) != len(self.content) + 1:
            raise IndexError(
                f"The length of font_list({len(self.font_list)}) does not match the number of coloum({len(self.content) + 1})"
            )

        self.draw: ImageDrawType = draw
        self.use_new_method: bool = use_new_method

        # The size of the limit for the entire text rendering area
        self.max_text_width: float = self.scan_image_width - self.logo_width - self.content_margin_left
        self.max_text_height: float = 450 - self.content_margin_top - self.vertical_spacing
        # TODO: the inline number 450, associated with `y_offset` in `creat_scan_image`

        self.cell_title: TextCell_text = TextCell_text(
            self.draw,
            self.font_list[0],
            self.horizontal_spacing,
            self.vertical_spacing,
            self.title,
            self.text_color,
            self.shade_color,
            self.shade_offset,
        )
        self.text_columns: List[TextColumn_labelAndValue] = []
        for col_idx, col in enumerate(self.content):
            if col_idx % 2 == 1:
                continue

            new_column: TextColumnBase = TextColumn_labelAndValue(
                self.draw,
                self.font_list[col_idx + 1],
                self.horizontal_spacing,
                self.vertical_spacing,
                self.max_text_height,
            )
            for row_idx, text in enumerate(col):
                new_label_cell: TextCell_text = TextCell_labelText(
                    self.draw,
                    self.font_list[col_idx + 1],
                    self.horizontal_spacing,
                    self.vertical_spacing,
                    text,
                    self.text_color,
                    self.shade_color,
                    self.shade_offset,
                )
                new_value_cell: TextCell_text = TextCell_text(
                    self.draw,
                    self.font_list[col_idx + 1],
                    self.horizontal_spacing,
                    self.vertical_spacing,
                    self.content[col_idx + 1][row_idx],
                    self.text_color,
                    self.shade_color,
                    self.shade_offset,
                )

                new_column.add_cell([new_label_cell, new_value_cell])

            self.text_columns.append(new_column)

        self._allocate_column_widths()

        # Store start positions for text drawing
        self.content_start: List[List[Tuple[int, int]]] = []
        self._calculate_content_start()

    def _allocate_column_widths(self) -> None:
        """
        Allocate the width for each column in the grid based on the maximum width of each column's text.

        The maximum width for each column is determined by the longest text in that column.
        The width is then stored in the member variable `column_widths`.
        """
        # number_of_column = len(self.text_columns)

        while True:
            # for column in self.text_columns:
            #     print(repr(column))

            for column in self.text_columns:
                column.cal_size()

            required_width = sum(column.value_width for column in self.text_columns)
            remaining_width = self.max_text_width - sum(column.label_width for column in self.text_columns)

            if required_width < remaining_width:
                number_of_column = sum(1 for column in self.text_columns)
                for column in self.text_columns:
                    column.set_width(column.width + (remaining_width - required_width) / number_of_column)

                break
            else:
                longest_cell: List[Tuple[TextColumn_labelAndValue, TextCell_text, float]] = (
                    []
                )  # (column, value_cell, value_width)
                for column in self.text_columns:
                    cell = column.get_widest_cell()
                    longest_cell.append((column, cell, cell.width))

                # Pick top 2 longest (not in the same column)
                longest_cell.sort(key=lambda x: x[2], reverse=True)
                longest_cell: List[Tuple[TextColumn_labelAndValue, TextCell_text, float]] = longest_cell[:2]

                sum_ellipsis_width = 0
                for _, cell, _ in longest_cell:
                    sum_ellipsis_width += cell.ellipsis_width

                excess_width = required_width - remaining_width + sum_ellipsis_width
                # Then shorten the 2 longest cell to the target length
                shorten_target = (sum(width for _, _, width in longest_cell) - excess_width) / 2

                for column, cell, _ in longest_cell:
                    cell.cal_width_every_char()
                    if column.extra_lines <= 0:
                        # can't creat a new line, just truncate
                        cell.truncate_content(shorten_target)
                    else:
                        # attemp to warp
                        for idx_extra in range(column.extra_lines):
                            original_text = cell.content
                            shorten_index = 1 + max(
                                (i for i, num in enumerate(cell.width_to_idx) if num < shorten_target),
                                default=0,
                            )
                            truncated_text = original_text[:shorten_index]
                            remaining_text = original_text[shorten_index:]

                            cell.update_content(truncated_text)
                            new_cell: TextCell_text = TextCell_text(
                                self.draw,
                                cell.font,
                                cell.h_spacing,
                                cell.v_spacing,
                                remaining_text,
                                self.text_color,
                                self.shade_color,
                                self.shade_offset,
                            )
                            column.insert_cell(cell, new_cell)

                            cell = new_cell
                            cell.cal_width_every_char()
                            if idx_extra == column.extra_lines - 1:
                                shorten_index = 1 + max(
                                    (i for i, num in enumerate(new_cell.width_to_idx) if num < shorten_target),
                                    default=0,
                                )
                                if new_cell.width_to_idx[-1] < shorten_target:
                                    pass
                                else:
                                    new_cell.truncate_content(shorten_target)

                        # for idx_extra in range(column.extra_lines)
                    # if column.extra_lines <= 0 / else
                # for column, cell, _ in longest_cell
            # if required_width < remaining_width / else
        # while True, break

    def _calculate_content_start(self) -> None:
        # Origin of content is (Ox, Oy) and it will change
        Ox = self.content_margin_left
        for col_idx, column in enumerate(self.text_columns):
            Oy = self.content_margin_top
            self.content_start.append([])
            for label_cell in column.label_cells:
                self.content_start[2 * col_idx].append((int(Ox), int(Oy)))
                Oy += label_cell.height

            Ox += column.label_width
            Oy = self.content_margin_top
            self.content_start.append([])
            for cell in column.cells:
                self.content_start[1 + 2 * col_idx].append((int(Ox), int(Oy)))
                Oy += cell.height

            Ox = Ox - column.label_width + column.width

    # TODO: 分离读取、转换和验证步骤
    @staticmethod
    def _parse_text_list(text_list: List[List[str | TextField]], video_info: VideoInfo) -> List[List[str]]:
        parsed_list: List[List[str]] = []

        for row in text_list:
            parsed_row: List[str] = []
            for item in row:
                if isinstance(item, TextField):
                    parsed_row.append(video_info[item.field][item.key])
                elif isinstance(item, str):
                    parsed_row.append(item)
                else:
                    raise ValueError(f"Unsupported item in text_list: {item!r}")
            parsed_list.append(parsed_row)
        return parsed_list

    @staticmethod
    def _parse_font_list(font_idx_list: List[int], font_list: List[FreeTypeFont]) -> List[FreeTypeFont]:
        parsed_list: List[FreeTypeFont] = []
        for idx in font_idx_list:
            if isinstance(idx, int):
                parsed_list.append(font_list[idx])
        return parsed_list

    def get_time_font(self) -> FreeTypeFont:
        """
        This font is used outside, but parsed in this class.
        """
        return self.time_font

    def draw_text(self) -> None:
        if self.use_new_method:
            self.cell_title.draw_content((self.title_margin_left, self.title_margin_top))
            for col_idx, column in enumerate(self.text_columns):
                for row_idx, cell in enumerate(column.label_cells):
                    cell.draw_content(self.content_start[2 * col_idx][row_idx])

                for row_idx, cell in enumerate(column.cells):
                    cell.draw_content(self.content_start[1 + 2 * col_idx][row_idx])
        else:
            for i, j, k in zip(self.old_content, self.pos_list, self.font_list):
                self._multiline_text_with_shade(
                    self.draw,
                    "\n".join(i),
                    j,
                    self.shade_offset,
                    self.vertical_spacing,
                    k,
                    self.text_color,
                    self.shade_color,
                )

    @staticmethod
    def _multiline_text_with_shade(
        draw_obj: ImageDrawType,
        text: str,
        pos: Tuple[int, int],
        offset: Tuple[int, int],
        spacing: int,
        font: FreeTypeFont,
        text_color: Tuple[int, int, int],
        shade_color: Tuple[int, int, int],
    ) -> None:
        """
        Draw multiline text with a shaded background on the image.
        The old method to draw multitext, used when `use_new_method` is False.

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
        draw_obj.multiline_text((x + dx, y + dy), text, fill=shade_color, font=font, spacing=spacing)
        draw_obj.multiline_text((x, y), text, fill=text_color, font=font, spacing=spacing)

        return None
