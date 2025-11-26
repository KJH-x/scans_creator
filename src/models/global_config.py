# pyright: reportCallIssue=false
# pyright: reportInvalidTypeForm=false
import re
from datetime import datetime
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


PLACEHOLDER_PATTERN = re.compile(r"\{([^:{}]+)(?::([^{}]+))?\}")
ALLOWED_PLACEHOLDERS = {"timestamp", "file_name"}


class GlobalConfig(BaseModel):
    logo_file: str = Field(..., description="Path to the logo image file")
    fonts: List[Font] = Field(..., min_items=1, description="List of font definitions")
    resize_scale: int = Field(..., ge=1, description="Scaling factor for resizing")
    avoid_leading: bool = Field(False, description="Whether to avoid leading content")
    avoid_ending: bool = Field(False, description="Whether to avoid ending content")
    output_filename_format: str = Field(
        "{timestamp:%H%M%S}.scan.{file_name}.png",
        description="Output file name format, must end with .png",
        pattern=r".*\.png$",
    )
    max_text_multiline: int = Field(3, ge=1, description="Maximum number of lines for text elements")

    @field_validator("logo_file")
    @classmethod
    def validate_logo_file(cls, v: str) -> str:
        return ensure_file_exists(v)

    @field_validator("output_filename_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        for field, fmt in PLACEHOLDER_PATTERN.findall(v):
            if field not in ALLOWED_PLACEHOLDERS:
                raise ValueError(f"Unknown placeholder '{{{field}}}' in: {v}")
            if field == "timestamp" and fmt:
                try:
                    datetime.now().strftime(fmt)
                except Exception as e:
                    raise ValueError(f"Invalid strftime format in '{{timestamp:{fmt}}}' → {e}")
        return v


if __name__ == "__main__":
    # for development
    import json

    with open(Path(__file__).parents[2] / "config/schemas/global.schema.json", "w", encoding="utf-8") as f:
        json.dump(GlobalConfig.model_json_schema(), f, indent=2, ensure_ascii=False)
