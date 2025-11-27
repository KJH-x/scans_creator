# pyright: reportCallIssue=false
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import List, Literal, Tuple

from pydantic import BaseModel, Field, conint, model_validator


class TextField(BaseModel):
    field: Literal["F", "V", "A", "S"]
    key: str


class InfoLayout(BaseModel):
    canvas_width: int = Field(3200, ge=1200, description="Width of the output canvas in pixels")
    grid_shape: Tuple[conint(ge=1), conint(ge=1)] = Field(..., description="Grid size as [rows, columns], each >=1")
    font_list: List[int] = Field(..., min_items=1, description="Indexes of fonts to use")
    time_font: int = Field(..., description="Index of font for time display")
    shade_offset: Tuple[int, int] = Field(..., description="Shadow offset values")
    text_color: List[conint(ge=0, le=255)] = Field(
        ..., min_items=3, max_items=4, description="RGB values for text color"
    )
    shade_color: List[conint(ge=0, le=255)] = Field(
        ..., min_items=3, max_items=4, description="RGB values for shadow color"
    )
    text_list: List[List[TextField | str]] = Field(..., min_items=1, description="Structured text entries for display")
    spacing_title_to_content: int = Field(
        22, ge=0, description="Vertical spacing between title and content sections in pixels"
    )
    spacing_label_to_value: int = Field(
        6, ge=0, description="Horizontal spacing between label and value in metadata entries in pixels"
    )
    spacing_in_one_metadata_column: int = Field(
        10, ge=0, description="Vertical spacing between entries in one metadata column in pixels"
    )
    spacing_metadata_columns: int = Field(25, ge=0, description="Horizontal spacing between metadata columns in pixels")
    timestamp_offset_y: int = Field(10, description="Vertical offset for snapshot timestamp display in pixels")

    @model_validator(mode="after")
    def check_text_list_vs_fonts(cls, values):
        font_list = values.font_list
        text_list = values.text_list
        if font_list is not None and text_list is not None:
            if len(font_list) != len(text_list):
                raise ValueError(
                    f"The length of font_list ({len(font_list)}) does not match the number of text_list rows ({len(text_list)})"
                )
        return values


if __name__ == "__main__":
    # for development
    import json

    with open(Path(__file__).parents[2] / "config/schemas/layout.schema.json", "w", encoding="utf-8") as f:
        json.dump(InfoLayout.model_json_schema(), f, indent=2, ensure_ascii=False)
