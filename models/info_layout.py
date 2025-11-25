# pyright: reportCallIssue=false
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import List, Tuple

from pydantic import BaseModel, Field, conint


class TextField(BaseModel):
    field: str
    key: str


class InfoLayout(BaseModel):
    grid_shape: Tuple[conint(ge=1), conint(ge=1)] = Field(..., description="Grid size as [rows, columns], each >=1")
    font_list: List[int] = Field(..., min_items=1, description="Indexes of fonts to use")
    time_font: int = Field(..., description="Index of font for time display")
    horizontal_spacing: int = Field(..., ge=0, description="Horizontal spacing in pixels")
    vertical_spacing: int = Field(..., ge=0, description="Vertical spacing in pixels")
    content_margin_left: int = Field(..., ge=0, description="Left margin for content")
    content_margin_top: int = Field(..., ge=0, description="Top margin for content")
    title_margin_left: int = Field(..., ge=0, description="Left margin for title")
    title_margin_top: int = Field(..., ge=0, description="Top margin for title")
    shade_offset: Tuple[int, int] = Field(..., description="Shadow offset values")
    text_color: List[conint(ge=0, le=255)] = Field(
        ..., min_items=3, max_items=4, description="RGB values for text color"
    )
    shade_color: List[conint(ge=0, le=255)] = Field(
        ..., min_items=3, max_items=4, description="RGB values for shadow color"
    )
    text_list: List[List[TextField | str]] = Field(..., min_items=1, description="Structured text entries for display")
    pos_list: List[Tuple[int, int]] = Field(..., min_items=1, description="Position coordinates as [x, y]")


if __name__ == "__main__":
    # for development
    import json

    with open(Path(__file__).parent.parent / "config/schemas/layout.schema.json", "w", encoding="utf-8") as f:
        json.dump(InfoLayout.model_json_schema(), f, indent=2, ensure_ascii=False)
