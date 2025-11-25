# pyright: reportCallIssue=false
# pyright: reportInvalidTypeForm=false
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field, conint, field_validator
from pydantic_core import PydanticCustomError


def ensure_file_exists(v: str) -> str:
    if not Path(v).exists():
        raise PydanticCustomError("file_not_found", "File does not exist: {v}", {"v": v})
    return v


class Font(BaseModel):
    path: str
    size: conint(ge=1)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        return ensure_file_exists(v)

    # conint does not work in nested List, so we manually validate here
    @field_validator("size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v < 1:
            raise PydanticCustomError("invalid_font_size", "Font size must be a positive integer: {v}", {"v": v})
        return v


class GlobalConfig(BaseModel):
    logo_file: str = Field(..., description="Path to the logo image file")
    fonts: List[Font] = Field(..., min_items=1, description="List of font definitions")
    resize_scale: int = Field(..., ge=1, description="Scaling factor for resizing")
    avoid_leading: bool = Field(False, description="Whether to avoid leading content")
    avoid_ending: bool = Field(False, description="Whether to avoid ending content")

    @field_validator("logo_file")
    @classmethod
    def validate_logo_file(cls, v: str) -> str:
        return ensure_file_exists(v)


if __name__ == "__main__":
    # for development
    import json

    with open(Path(__file__).parent.parent / "config/schemas/global.schema.json", "w", encoding="utf-8") as f:
        json.dump(GlobalConfig.model_json_schema(), f, indent=2, ensure_ascii=False)
