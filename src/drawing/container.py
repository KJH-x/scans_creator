import sys
from typing import List, Literal

from PIL.Image import Image as ImageType

from .element_base import Element, ElementMargin, ElementSize, ImageElement, TextElement


class FlexContainer(Element):
    def __init__(
        self,
        children: List[Element] | None = None,
        direction: Literal["row", "column"] = "row",
        align: Literal["start", "justify"] = "start",
        spacing: int = 0,
        margin: ElementMargin = ElementMargin(0, 0, 0, 0),
        max_width: int | None = None,
        max_height: int | None = None,
        flex_grow: float = 0,
    ):
        super().__init__(0, 0, margin, max_width=max_width, max_height=max_height, flex_grow=flex_grow)
        self.children = children or []
        self.direction = direction
        self.align = align
        self.spacing = spacing

    def add(self, element: Element):
        self.children.append(element)

    def layout(self, max_width: int | None = None):
        """
        - NEVER care about height limitation
        - root.measure() need be manually called outside BEFORE and AFTER method
        """
        if max_width is None:
            max_width = sys.maxsize

        children_widths: List[int] = [c.width + c.margin.left + c.margin.right for c in self.children]
        if self.direction == "row":
            total_width = sum(children_widths) + self.spacing * (len(children_widths) - 1)
        else:
            total_width = max(children_widths) if children_widths else 0

        ind_need_shorten = []
        shorten_target = max_width
        if total_width > max_width:
            if self.direction == "row":
                n = len(self.children)
                shrink_count = (n + 1) // 2  # ceil(n/2)

                sorted_indices = sorted(range(n), key=lambda i: children_widths[i], reverse=True)
                ind_need_shorten = sorted_indices[:shrink_count]

                excess_width = total_width - max_width
                total_longest_width = sum(children_widths[i] for i in ind_need_shorten)
                shorten_target = int((total_longest_width - excess_width) / shrink_count)
            elif self.direction == "column":
                ind_need_shorten = [i for i, w in enumerate(children_widths) if w > max_width]

        for i, child in enumerate(self.children):
            if i in ind_need_shorten:
                if child.no_flex_shrink:
                    continue

                if isinstance(child, FlexContainer):
                    child.layout(max_width=shorten_target - child.margin.x)
                elif isinstance(child, TextElement):
                    child.truncate_or_wrap(max_width=shorten_target - child.margin.x)
                elif isinstance(child, ImageElement):
                    ...  # TODO

    def calc_flex_grow(self):
        """
        - Allocate the remaining space based on the child element flex-grow
        - The root element needs to be manually sized before being invoked
        - Note that using measure() here may override the allocation result
        """
        if self.direction == "row":
            total_width = sum(c.width + c.margin.x for c in self.children) + self.spacing * (len(self.children) - 1)
            total_grow = sum(c.flex_grow for c in self.children if not c.no_flex_shrink)
            for c in self.children:
                if not c.no_flex_shrink and total_grow > 1e-5:
                    extra_width = int((c.flex_grow / total_grow) * (self.width - total_width))
                    c.width += extra_width

                c.height = self.height

        elif self.direction == "column":
            total_height = sum(c.height + c.margin.y for c in self.children) + self.spacing * (len(self.children) - 1)
            total_grow = sum(c.flex_grow for c in self.children if not c.no_flex_shrink)
            for c in self.children:
                if not c.no_flex_shrink and total_grow > 1e-5:
                    extra_height = int((c.flex_grow / total_grow) * (self.height - total_height))
                    c.height += extra_height

                c.width = self.width

        for c in self.children:
            if isinstance(c, FlexContainer):
                c.calc_flex_grow()

    def measure(self) -> ElementSize:
        widths = [c.measure().width + c.margin.x for c in self.children]
        heights = [c.measure().height + c.margin.y for c in self.children]
        if self.direction == "row":
            self.width = (sum(widths) if widths else 0) + self.spacing * (len(widths) - 1)
            self.height = max(heights) if heights else 0
        else:
            self.width = max(widths) if widths else 0
            self.height = (sum(heights) if heights else 0) + self.spacing * (len(heights) - 1)
        return ElementSize(self.width, self.height)

    def render(self, canvas: ImageType):
        cur_x, cur_y = self.x + self.margin.left, self.y + self.margin.top

        spacing = self.spacing
        if self.align == "justify" and len(self.children) > 1:
            widths = [c.width + c.margin.x for c in self.children]
            heights = [c.height + c.margin.y for c in self.children]

            if self.direction == "row":
                total_used = sum(widths)
                available = self.width - total_used
                spacing = available // (len(self.children) - 1) if available > 0 else 0
            elif self.direction == "column":
                total_used = sum(heights)
                available = self.height - total_used
                spacing = available // (len(self.children) - 1) if available > 0 else 0

        for child in self.children:
            child.x = cur_x
            child.y = cur_y
            child.render(canvas)

            if self.direction == "row":
                cur_x += child.width + child.margin.x + spacing
            else:
                cur_y += child.height + child.margin.y + spacing

    def __repr__(self):
        return f"Flex(direction={self.direction}, children={len(self.children)}, align={self.align}, spacing={self.spacing}, margin={self.margin})"
