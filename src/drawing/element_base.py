from abc import ABC, abstractmethod
from typing import List, NamedTuple, Tuple

from PIL import ImageDraw
from PIL.Image import Image as ImageType
from PIL.ImageDraw import ImageDraw as ImageDrawType
from PIL.ImageFont import FreeTypeFont

from ..core.config_manager import config_manager


class ElementSize(NamedTuple):
    width: int
    height: int


class ElementMargin(NamedTuple):
    top: int
    right: int
    bottom: int
    left: int

    @property
    def x(self) -> int:
        return self.right + self.left

    @property
    def y(self) -> int:
        return self.bottom + self.top


class Element(ABC):
    def __init__(
        self,
        preferred_width: int,
        preferred_height: int,
        margin: ElementMargin = ElementMargin(0, 0, 0, 0),
        min_width: int | None = None,
        max_width: int | None = None,
        min_height: int | None = None,
        max_height: int | None = None,
        no_flex_shrink=False,
        flex_grow=0.0,
    ):
        self.preferred_width = preferred_width
        self.preferred_height = preferred_height
        self.margin = margin  # (top, right, bottom, left)
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height
        self.no_flex_shrink = no_flex_shrink
        self.flex_grow = flex_grow

        self.x: int = 0
        self.y: int = 0
        self.width: int = preferred_width
        self.height: int = preferred_height

    @abstractmethod
    def measure(self) -> ElementSize:
        """Trigger element size calculation and cache as member variables"""

    @abstractmethod
    def render(self, canvas: ImageType):
        """Render the element onto the given canvas"""


class TextElement(Element):
    def __init__(
        self,
        text: str,
        font: FreeTypeFont,
        line_spacing: int = 4,
        color: Tuple[int, int, int] = (0, 0, 0),
        shadow_color: Tuple[int, int, int] = (0, 0, 0),
        shadow_offset: Tuple[int, int] = (0, 0),
        margin: ElementMargin = ElementMargin(0, 0, 0, 0),
        no_flex_shrink: bool = False,
    ):
        self.original_text = text
        self.show_text: List[str] = [text]
        self.font = font
        self.color = color
        self.shadow_color = shadow_color
        self.shadow_offset = shadow_offset
        self.line_spacing = line_spacing

        width, height = self.measure()
        super().__init__(width, height, margin, no_flex_shrink=no_flex_shrink)

    def measure(self) -> ElementSize:
        widths = []
        for line in self.show_text:
            l, t, r, b = self.font.getbbox(line)
            widths.append(r - l)
        width = max(widths) if widths else 0

        ascent, descent = self.font.getmetrics()
        line_height = ascent + descent
        num_lines = len(self.show_text)
        if num_lines == 0:
            height = 0
        else:
            height = num_lines * line_height + (num_lines - 1) * self.line_spacing

        self.width = width
        self.height = height
        return ElementSize(width, height)

    def render(self, canvas: ImageType):
        draw = ImageDraw.Draw(canvas)
        x = self.x + self.margin.left
        y = self.y + self.margin.top

        ascent, descent = self.font.getmetrics()
        line_height = ascent + descent

        cur_y = y
        for line in self.show_text:
            self._render_text_with_shadow(x, cur_y, line, draw)
            cur_y += line_height + self.line_spacing

    def _render_text_with_shadow(self, x: int, y: int, text: str, draw: ImageDrawType):
        if self.shadow_offset != (0, 0):
            dx, dy = self.shadow_offset
            draw.text((x + dx, y + dy), text, font=self.font, fill=self.shadow_color)

        draw.text((x, y), text, font=self.font, fill=self.color)

    def test_width(self, text: str) -> int:
        l, t, r, b = self.font.getbbox(text)
        return int(r - l)

    def truncate_or_wrap(self, max_width: int):
        """
        Wrap or truncate text to ensure that each line is no more than `max_width` wide,
        And the total number of lines does not exceed `config_manager.max_text_multiline`
        """
        ellipsis_width = self.test_width("…")
        ellipsis_added = False
        self.show_text = []
        new_line = ""
        line_ind = 0
        for char in self.original_text:
            new_line += char
            line_width = self.test_width(new_line)
            if line_ind < config_manager.config.max_text_multiline - 1 and line_width > max_width:
                self.show_text.append(new_line[:-1])
                line_ind += 1
                new_line = char
            elif line_ind == config_manager.config.max_text_multiline - 1 and line_width + ellipsis_width > max_width:
                ellipsis_added = True
                self.show_text.append(new_line[:-1] + "…")
                break

        if not ellipsis_added:
            self.show_text.append(new_line)

        self.measure()


class ImageElement(Element):
    def __init__(
        self,
        image: ImageType,
        margin: ElementMargin = ElementMargin(0, 0, 0, 0),
        no_flex_shrink: bool = False,
    ):
        super().__init__(*image.size, margin, no_flex_shrink=no_flex_shrink)
        self.image = image

    def measure(self) -> ElementSize:
        self.width, self.height = self.image.size
        return ElementSize(*self.image.size)

    def render(self, canvas: ImageType):
        canvas.paste(self.image, (self.x + self.margin.left, self.y + self.margin.top))
