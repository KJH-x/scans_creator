import math
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Tuple, TypeVar, Union

from PIL.Image import Image as ImageType
from PIL.Image import Resampling
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont

"""
├  │  └

GridElement 
    ├── GridCell
    │   ├── TextCellBase
    │   └── ImageCellBase 
    │
    └── GridColumn
        └── TextColumnBase
"""


class GridElement(ABC):
    """
    Base class for all grid elements.

    Attributes:
        draw (ImageDrawType): The drawing context used to render the element.
        width (float): The width of the grid element.
        height (float): The height of the grid element.
        h_spacing (float): The horizontal spacing between elements.
        v_spacing (float): The vertical spacing between elements.

    Methods:
        set_width(width: float) -> None:
            Sets the width of the grid element.

        set_height(height: float) -> None:
            Sets the height of the grid element.

        cal_width() -> None:
            Abstract method for calculating the width of the grid element.

        cal_height() -> None:
            Abstract method for calculating the height of the grid element.
    """

    def __init__(self, draw: ImageDrawType, h_spacing: float, v_spacing: float) -> None:
        self.draw: ImageDrawType = draw

        self.width: float = 0
        self.height: float = 0
        self.h_spacing: float = h_spacing
        self.v_spacing: float = v_spacing

    def set_width(self, width: float) -> None:
        self.width = width

    def set_height(self, height: float) -> None:
        self.height = height

    def cal_size(self) -> None:
        self.cal_width()
        self.cal_height()

    @abstractmethod
    def cal_width(self) -> None:
        pass

    @abstractmethod
    def cal_height(self) -> None:
        pass


T = TypeVar("T", bound=Union[str, ImageType])


class GridCell(GridElement, Generic[T]):
    """
    A base class for grid cells.

    Attributes:
        content (T): The content of the cell.

    Methods:
        update_content(content: str) -> None:
            Updates the content of the cell and recalculates its width and height.

        draw_content(self, pos: Tuple[int, int]) -> None:
            Abstract method for drawing content.
    """

    def __init__(self, draw: ImageDrawType, h_spacing: float, v_spacing: float, content: Optional[T] = None) -> None:
        super(GridCell, self).__init__(draw, h_spacing, v_spacing)

        if content is not None:
            self.update_content(content)

    def update_content(self, content: T) -> None:
        self.content = content
        self.cal_width()
        self.cal_height()

    @abstractmethod
    def draw_content(self, pos: Tuple[int, int]) -> None:
        pass


class GridColumn(GridElement):
    """
    A base class for text columns. This class extends the `GridElement` class
    and manages multiple `GridCell` instances. It handles adding, removing,
    and arranging cells in a vertical column.

    Attributes:
        max_height (float): The maximum height of the column.
        cells (List[GridCell]): A list of cells contained in the column.

    Methods:
        add_cell(new_cell: List[TextCellBase]) -> None:
            Adds new cells to the column.

        insert_cell(origin_cell: TextCellBase, new_cell: TextCellBase) -> int:
            Inserts a new cell after an existing cell in the column.

        get_widest_cell() -> TextCellBase:
            Returns the cell with the maximum width in the column.
    """

    def __init__(self, draw: ImageDrawType, h_spacing: float, v_spacing: float, max_height: float) -> None:
        super(GridColumn, self).__init__(draw, h_spacing, v_spacing)

        self.extra_lines: int = 999
        self.max_height: float = max_height
        self.cells: List[GridCell] = []

    def add_cell(self, new_cell: List[GridCell]) -> None:
        if len(new_cell) == 1:
            self.cells.append(new_cell[0])
        elif len(new_cell) > 1:
            self.cells.extend(new_cell)
        else:
            raise IndexError("TextColumnBase.add_cell(): The length of new_cell is too short.")
        self.extra_lines = self.extra_lines - len(new_cell) + 1
        self.cal_size()

    def insert_cell(self, origin_cell: GridCell, new_cell: GridCell) -> None:
        """
        Find the same object of origin_cell in self.cells, and insert after it.
        If not found, the method doesn't add a cell.
        """
        for idx, cell in enumerate(self.cells):
            if cell == origin_cell:
                self.cells.insert(idx + 1, new_cell)

    def get_widest_cell(self) -> GridCell:
        longest_cell: List[Tuple[GridCell, float]] = []
        for cell in self.cells:
            longest_cell.append((cell, cell.width))

        longest_cell.sort(key=lambda x: x[1], reverse=True)
        return longest_cell[0][0]

    def __len__(self) -> int:
        return len(self.cells)

    def __repr__(self) -> str:
        return f"Column lenght: {len(self)}"


class TextCellBase(GridCell[str]):
    """
    A base class for text-based grid cells.

    Attributes:
        ellipsis_width (float): The width of the ellipsis ("...") in the current font.
        chinese_char_height (float): The height of a Chinese character in the current font.
        content (str): The text content of the cell.
        width_to_idx (List[float]): A list of cumulative widths for each character in the content.
    """

    def __init__(
        self, draw: ImageDrawType, font: FreeTypeFont, h_spacing: float, v_spacing: float, content: str
    ) -> None:
        self.font: FreeTypeFont = font
        self.ellipsis_width: float = draw.textbbox((0, 0), "...", font=font)[2]
        self.chinese_char_height: float = draw.textbbox((0, 0), "田", font=font)[3]
        super(TextCellBase, self).__init__(draw, h_spacing, v_spacing, content=content)

    def cal_width(self) -> None:
        bbox = self.draw.textbbox((0, 0), self.content, font=self.font)
        self.width = bbox[2] + self.h_spacing

    def cal_height(self):
        self.height = self.chinese_char_height + self.v_spacing

    def cal_width_every_char(self) -> None:
        str_every_char: List[str] = [char for char in self.content]
        width_every_char: List[float] = [self.draw.textbbox((0, 0), char, font=self.font)[2] for char in str_every_char]
        self.width_to_idx: List[float] = [sum(width_every_char[: i + 1]) for i in range(len(width_every_char))]
        # 这是另一种方法计算的长度，他们的结果有差异但是不大，时间开销差异无法感知到
        # width_to_idx_other: List[float] = [self.draw.textbbox((0, 0), str_to_change[:i+1], font=font)[2] for i in range(len(str_to_change))]
        if len(self.width_to_idx) == 0:
            # avoid error
            self.width_to_idx = [0]

    def truncate_content(self, shorten_target: float) -> None:
        shorten_index = max((i for i, num in enumerate(self.width_to_idx) if num < shorten_target), default=0)
        truncated_text = self.content[:shorten_index] + "..."
        self.update_content(truncated_text)

    def __repr__(self) -> str:
        return f"{self.content}"


class ImageCellBase(GridCell[ImageType]):
    """
    A base class for image-based grid cells.

    Attributes:
        content (ImageType): The text content of the cell.
    """

    def __init__(self, draw: ImageDrawType, h_spacing: float, v_spacing: float, content: ImageType) -> None:
        super(ImageCellBase, self).__init__(draw, h_spacing, v_spacing, content=content)

    def cal_width(self) -> None:
        pass

    def cal_height(self):
        pass

    def cal_size(self) -> None:
        self.width, self.height = self.content.size

    def scale_to_width(self, target_width: int) -> None:
        """
        Scale the image proportionally to the given target width.

        Args:
            target_width (int): The desired width of the image.
        """
        scale_factor = target_width / self.width
        new_size = (target_width, int(self.height * scale_factor))
        self.content = self.content.resize(new_size, Resampling.LANCZOS)
        self.cal_size()

    def scale_to_height(self, target_height: int) -> None:
        """
        Scale the image proportionally to the given target height.

        Args:
            target_height (int): The desired height of the image.
        """
        scale_factor = target_height / self.height
        new_size = (int(self.width * scale_factor), target_height)
        self.content = self.content.resize(new_size, Resampling.LANCZOS)
        self.cal_size()

    def scale_by_factor(self, scale_factor: float) -> None:
        """
        Scale the image by a custom factor.

        Args:
            scale_factor (float): The scaling factor (e.g., 0.5 for 50% reduction, 2.0 for 200% enlargement).
        """
        new_size = (int(self.width * scale_factor), int(self.height * scale_factor))
        self.content = self.content.resize(new_size, Resampling.LANCZOS)
        self.cal_size()

    def resize(self, target_width: int, target_height: int) -> None:
        """
        Resize the image to a specific width and height, ignoring aspect ratio.

        Args:
            target_width (int): The desired width of the image.
            target_height (int): The desired height of the image.
        """
        new_size = (target_width, target_height)
        self.content = self.content.resize(new_size, Resampling.LANCZOS)
        self.cal_size()

    def __repr__(self) -> str:
        content_desc = f"<Image {self.content.size}>" if hasattr(self.content, "size") else "<Invalid Image>"
        return f"{self.__class__.__name__}(content={content_desc}"


class TextColumnBase(GridColumn):
    """
    A base class for text columns. This class extends the `GridElement` class
    and manages multiple `TextCellBase` instances. It handles adding, removing,
    and arranging cells in a vertical column, as well as calculating the overall size
    of the column based on the individual cell sizes.

    Attributes:
        chinese_char_height (float): The height of a Chinese character in the current font.
        max_rows (int): The maximum number of rows that can fit in the column.
        extra_lines (int): The number of remaining lines available for adding more cells.
        cells (List[TextCellBase]): A list of cells contained in the column.

    Methods:
        add_cell(new_cell: List[TextCellBase]) -> None:
            Adds new cells to the column.

        insert_cell(origin_cell: TextCellBase, new_cell: TextCellBase) -> int:
            Inserts a new cell after an existing cell in the column.

        cal_size() -> None:
            Recalculates the overall width and height of the column.

        get_widest_cell() -> TextCellBase:
            Returns the cell with the maximum width in the column.
    """

    def __init__(
        self, draw: ImageDrawType, font: FreeTypeFont, h_spacing: float, v_spacing: float, max_height: float
    ) -> None:
        super(TextColumnBase, self).__init__(draw, h_spacing, v_spacing, max_height)

        self.font: FreeTypeFont = font
        self.ellipsis_width: float = draw.textbbox((0, 0), "...", font=font)[2]
        self.chinese_char_height: float = draw.textbbox((0, 0), "田", font=font)[3]
        self.max_rows: int = math.floor(self.max_height / (self.chinese_char_height + self.v_spacing))
        self.extra_lines: int = self.max_rows
