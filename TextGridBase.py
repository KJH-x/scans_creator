from typing import List, LiteralString, Tuple, Dict
from abc import ABC, abstractmethod
from PIL import ImageFont
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont


class GridElement(ABC):
    """
    Base class for all grid elements. This class defines common properties
    like drawing context, font, spacing, and size calculations for grid-based 
    elements (cells, columns, etc.).
    
    Attributes:
        draw: ImageDrawType — The drawing context used to render the element.
        font: FreeTypeFont — The font used for rendering text in the element.
        width: float — The width of the grid element.
        height: float — The height of the grid element.
        h_spacing: float — The horizontal spacing between elements.
        v_spacing: float — The vertical spacing between elements.
        chinese_char_height: float — The height of a Chinese character in the current font.
    
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
    def __init__(self, draw: ImageDrawType, font: FreeTypeFont, h_spacing: float, v_spacing: float) -> None:
        self.draw: ImageDrawType = draw
        self.font: FreeTypeFont = font
        
        self.width: float = 0
        self.height: float = 0
        self.h_spacing: float = h_spacing
        self.v_spacing: float = v_spacing
        
        self.chinese_char_height: float = draw.textbbox((0, 0), "田", font=font)[3]
        
    def set_width(self, width: float) -> None:
        self.width = width
        
    def set_height(self, height: float) -> None:
        self.height = height
        
    @abstractmethod
    def cal_width(self) -> None:
        pass
    
    @abstractmethod
    def cal_height(self) -> None:
        pass


class TextCellBase(GridElement):
    """
    A base class for text-based grid cells. This class extends the `GridElement`
    class and adds additional logic for handling text content, including
    calculating the cell width and height, truncating content, and rendering text.
    
    Attributes:
        ellipsis_width: float — The width of the ellipsis ("...") in the current font.
        content: str — The text content of the cell.
        width_to_idx: List[float] — A list of cumulative widths for each character in the content.

    Methods:
        update_content(content: str) -> None:
            Updates the content of the cell and recalculates its width and height.
        
        cal_width_every_char() -> None:
            Calculates the width of each character in the content and stores cumulative widths.
        
        truncate_content(shorten_target: float) -> None:
            Truncates the content to fit within a specified width, adding an ellipsis if necessary.
    """
    def __init__(self, draw: ImageDrawType, font: FreeTypeFont, h_spacing: float, v_spacing: float, content: str | None=None) -> None:
        super(TextCellBase, self).__init__(draw, font, h_spacing, v_spacing)
        
        self.ellipsis_width: float = draw.textbbox((0, 0), "...", font=font)[2]
        
        if content is not None:
            self.update_content(content)
    
    def update_content(self, content: str) -> None:
        self.content = content
        self.cal_width()
        self.cal_height()
    
    def cal_width_every_char(self) -> None:
        str_every_char: List[str] = [char for char in self.content]
        width_every_char: List[float] = [self.draw.textbbox((0, 0), char, font=self.font)[2] for char in str_every_char]
        self.width_to_idx: List[float] = [sum(width_every_char[:i+1]) for i in range(len(width_every_char))]
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


class TextColumnBase(GridElement):
    """
    A base class for text columns. This class extends the `GridElement` class
    and manages multiple `TextCellBase` instances. It handles adding, removing,
    and arranging cells in a vertical column, as well as calculating the overall size 
    of the column based on the individual cell sizes.

    Attributes:
        max_height: float — The maximum height of the column.
        max_rows: int — The maximum number of rows that can fit in the column.
        extra_lines: int — The number of remaining lines available for adding more cells.
        cells: List[TextCellBase] — A list of cells contained in the column.

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
    def __init__(self, draw: ImageDrawType, font: FreeTypeFont, h_spacing: float, v_spacing: float, max_height: float) -> None:
        super(TextColumnBase, self).__init__(draw, font, h_spacing, v_spacing)
        
        self.max_height: float = max_height
        self.max_rows: int = self.max_height // (self.chinese_char_height + self.v_spacing)
        # How many lines are left for line wrapping
        self.extra_lines: int = self.max_rows
        
        self.cells: List[TextCellBase] = []
        
    def add_cell(self, new_cell: List[TextCellBase]) -> None:
        if len(new_cell) == 1:
            self.cells.append(new_cell[0])
        elif len(new_cell) > 1:
            self.cells.extend(new_cell)
        else:
            raise IndexError("TextColumnBase.add_cell(): The length of new_cell is too short.")
        self.extra_lines = self.extra_lines - len(new_cell) + 1
        self.cal_size()
        
    def insert_cell(self, origin_cell: TextCellBase, new_cell: TextCellBase) -> int:
        """
        Find the same object of origin_cell in self.cells, and insert after it.
        If not found, the method doesn't add a cell.
        """
        for idx, cell in enumerate(self.cells):
            if cell == origin_cell:
                self.cells.insert(idx+1, new_cell)
        
    def cal_size(self) -> None:
        self.cal_width()
        self.cal_height()
    
    def get_widest_cell(self) -> TextCellBase:
        longest_cell: List[Tuple[TextCellBase, float]] = []
        for cell in self.cells:
            longest_cell.append((cell, cell.width))
            
        longest_cell.sort(key=lambda x: x[1], reverse=True)
        return longest_cell[0][0]
        
    def __len__(self) -> int:
        return len(self.cells)
    
    def __repr__(self) -> str:
        res: List[str] = []
        for cell in self.cells:
            res.append(repr(cell))
        return "\n".join(res)