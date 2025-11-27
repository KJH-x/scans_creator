from datetime import timedelta
from typing import Dict, List

from ..typings.video_info import (
    AudioInfoDict,
    FileInfoDict,
    SubtitleInfoDict,
    VideoInfoDict,
)


class VideoInfo:
    def __init__(
        self,
        file_info: FileInfoDict,
        video_streams: List[VideoInfoDict],
        audio_info: AudioInfoDict,
        subtitle_info: SubtitleInfoDict,
    ) -> None:
        # File information
        self.file_name: str = _ if isinstance(_ := file_info.get("name"), str) else ""
        self.file_path: str = _ if isinstance(_ := file_info.get("path"), str) else ""
        self.file_size: int = _ if isinstance(_ := file_info.get("size"), int) else 0
        self.duration: int = _ if isinstance(_ := file_info.get("duration"), int) else 0
        self.bitrate: int = _ if isinstance(_ := file_info.get("bitrate"), int) else 0

        # multiply video streams
        self.video_streams: List[VideoInfoDict] = video_streams
        self.set_active_video_stream(0)

        # Audio information
        self.audio_codec: str = _ if isinstance(_ := audio_info.get("codec"), str) else ""
        self.audio_lang: str = _ if isinstance(_ := audio_info.get("lang"), str) else ""
        self.audio_title: str = _ if isinstance(_ := audio_info.get("title"), str) else ""
        self.audio_sampleRate: str = _ if isinstance(_ := audio_info.get("sampleRate"), str) else ""
        self.audio_channels: str = _ if isinstance(_ := audio_info.get("channels"), str) else ""
        self.audio_channelLayout: str = _ if isinstance(_ := audio_info.get("channelLayout"), str) else ""
        self.audio_channel: str = f"{self.audio_channelLayout}({self.audio_channels}@{self.audio_sampleRate})"

        # Subtitle information
        self.subtitle_codec: str = _ if isinstance(_ := subtitle_info.get("codec"), str) else ""
        self.subtitle_lang: str = _ if isinstance(_ := subtitle_info.get("lang"), str) else ""
        self.subtitle_title: str = _ if isinstance(_ := subtitle_info.get("title"), str) else ""

    def set_active_video_stream(self, index: int) -> None:
        def _has_long_aspect_ratio(aspect_ratio: str) -> bool:
            parts = aspect_ratio.split(":")
            return any(len(part) > 2 for part in parts)

        # ddd:ddd -> f.ff (d:d or dd:dd remain itself)
        def _short_aspect_ratio(aspect_ratio: str) -> str:
            return (
                f"{eval(aspect_ratio.replace(':','/')):.2f}" if _has_long_aspect_ratio(aspect_ratio) else aspect_ratio
            )

        if index >= len(self.video_streams) | index < 0:
            if len(self.video_streams) == 0:
                raise IndexError(f"No video streeams available.")
            else:
                raise IndexError(f"{index} is not available.")

        else:
            self.current_video_stream_index: int = index  # Index for active video stream
            video_info = self.video_streams[self.current_video_stream_index]

            # Detail info, not for print
            self.pix_fmt: str = _ if isinstance(_ := video_info.get("pix_fmt"), str) else ""
            self.color_range: str = _ if isinstance(_ := video_info.get("color_range"), str) else ""
            self.color_space: str = _ if isinstance(_ := video_info.get("color_space"), str) else ""
            self.codec_name: str = _ if isinstance(_ := video_info.get("codec_name"), str) else ""
            self.profile: str = _ if isinstance(_ := video_info.get("profile"), str) else ""
            self.pix_depth: int = _ if isinstance(_ := video_info.get("pix_depth"), int) else 0
            self.pix_channels: int = _ if isinstance(_ := video_info.get("pix_channels"), int) else 0
            self.width: int = _ if isinstance(_ := video_info.get("width"), int) else 0
            self.height: int = _ if isinstance(_ := video_info.get("height"), int) else 0
            self.sar: str = _ if isinstance(_ := video_info.get("sar"), str) else ""
            self.dar: str = _ if isinstance(_ := video_info.get("dar"), str) else ""
            # self.video_lang: str = _ if isinstance(_ := video_info.get("lang"), str) else ""

            # Video information
            self.video_codec: str = f"{self.codec_name} ({self.profile}, {self.pix_channels}x{self.pix_depth}bit)"
            self.video_color: str = f"{self.pix_fmt} ({self.color_range}, {self.color_space})"

            self.frame_size: str = (
                f"{self.width}x{self.height} ({_short_aspect_ratio(self.sar)}/{_short_aspect_ratio(self.dar)})"
            )
            self.framerate: float = _ if isinstance(_ := video_info.get("framerate"), float) else 0.0

    def __list__(self) -> List[str]:
        return [
            f"File Name: {self.file_name}",
            f"File Size:        {(self.file_size)/1024/1024:,.2f} MiB",
            f"Duration:         {timedelta(seconds=self.duration)}",
            f"Bitrate:          {(self.bitrate)/1000:,.2f} kbps",
            f"Audio Codec:      {self.audio_codec}",
            f"Audio Language:   {self.audio_lang}",
            f"Audio Title:      {self.audio_title}",
            f"Video Codec:      {self.video_codec}",
            f"Video color:      {self.video_color}",
            f"Frame Size:       {self.frame_size}",
            f"Framerate:        {self.framerate:.2f} fps",
            # f"Video Language:   {self.video_lang}",
            f"Subtitle Codec:   {self.subtitle_codec}",
            f"Subtitle Language:{self.subtitle_lang}",
            f"Subtitle Title:   {self.subtitle_title}",
        ]

    def __str__(self) -> str:
        return "\n".join(self.__list__())

    def to_dict(self) -> Dict[str, Dict[str, str]]:
        return {
            "F": {
                "name": self.file_name,
                "size": f"{(self.file_size)/1024/1024:,.2f} MiB",
                "duration": str(timedelta(seconds=self.duration)),
                "bitrate": f"{(self.bitrate)/1000:,.2f} kbps",
            },
            "V": {
                "codec": self.video_codec,
                "color": self.video_color,
                "frameSize": self.frame_size,
                "frameRate": f"{self.framerate:.2f} fps",
                # "lang": self.video_lang
            },
            "A": {
                "codec": self.audio_codec,
                "lang": self.audio_lang,
                "title": self.audio_title,
                "sampleRate": self.audio_sampleRate,
                "channel": self.audio_channel,
            },
            "S": {
                "codec": self.subtitle_codec,
                "lang": self.subtitle_lang,
                "title": self.subtitle_title,
            },
        }

    def __getitem__(self, key) -> Dict[str, str]:
        # Retrieve values as a dictionary and allow indexing
        return self.to_dict().get(key, {"err": "No value"})
