from typing import TypedDict


class FileInfoDict(TypedDict):
    name: str
    path: str
    size: int
    duration: int
    bitrate: int


class VideoInfoDict(TypedDict):
    codec: str
    color: str
    frame_size: str
    framerate: float
    lang: str
    pix_fmt: str
    color_range: str
    color_space: str
    codec_name: str
    profile: str
    pix_depth: int
    pix_channels: int
    width: int
    height: int
    sar: str
    dar: str


class AudioInfoDict(TypedDict):
    codec: str
    lang: str
    title: str
    sampleRate: str
    channels: str
    channelLayout: str


class SubtitleInfoDict(TypedDict):
    codec: str
    lang: str
    title: str
