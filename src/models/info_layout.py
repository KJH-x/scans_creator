# pyright: reportCallIssue=false
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import List, Tuple

from pydantic import BaseModel, Field, conint, model_validator


class TextField(BaseModel):
    field: str
    key: str


class InfoLayout(BaseModel):
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
