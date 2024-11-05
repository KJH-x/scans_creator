from datetime import timedelta
from typing import Dict, List


class VideoInfo:
    def __init__(self, file_info: Dict[str, str | int], video_info: Dict, audio_info: Dict, subtitle_info: Dict):
        # File information
        self.file_name: str = _ if isinstance(_ := file_info.get("name"), str) else ""
        self.file_path: str = _ if isinstance(_ := file_info.get("path"), str) else ""
        self.file_size: int = _ if isinstance(_ := file_info.get("size"), int) else 0
        self.duration: int = _ if isinstance(_ := file_info.get("duration"), int) else 0
        self.bitrate: int = _ if isinstance(_ := file_info.get("bitrate"), int) else 0

        # Video information
        self.video_codec: str = _ if isinstance(_ := video_info.get("codec"), str) else ""
        self.video_colorspace: str = _ if isinstance(_ := video_info.get("colorspace"), str) else ""
        self.frame_size: str = _ if isinstance(_ := video_info.get("frame_size"), str) else ""
        self.framerate: float = _ if isinstance(_ := video_info.get("framerate"), float) else 0.0
        # self.video_lang: str = _ if isinstance(_ := video_info.get("lang"), str) else ""

        # Audio information
        self.audio_codec: str = _ if isinstance(_ := audio_info.get("codec"), str) else ""
        self.audio_lang: str = _ if isinstance(_ := audio_info.get("lang"), str) else ""
        self.audio_title: str = _ if isinstance(_ := audio_info.get("title"), str) else ""
        self.audio_sampleRate: str = _ if isinstance(_ := audio_info.get("sampleRate"), str) else ""
        self.audio_channels: str = _ if isinstance(_ := audio_info.get("channels"), str) else ""

        # Subtitle information
        self.subtitle_codec: str = _ if isinstance(_ := subtitle_info.get("codec"), str) else ""
        self.subtitle_lang: str = _ if isinstance(_ := subtitle_info.get("lang"), str) else ""
        self.subtitle_title: str = _ if isinstance(_ := subtitle_info.get("title"), str) else ""

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
            f"Video Colorspace: {self.video_colorspace}",
            f"Frame Size:       {self.frame_size}",
            f"Framerate:        {self.framerate:.2f} fps",
            # f"Video Language:   {self.video_lang}",
            f"Subtitle Codec:   {self.subtitle_codec}",
            f"Subtitle Language:{self.subtitle_lang}",
            f"Subtitle Title:   {self.subtitle_title}"
        ]

    def __str__(self) -> str:
        return "\n".join(self.__list__())

    def __dict__(self) -> Dict[str, Dict[str, str]]:
        return {
            "F": {
                "name": self.file_name,
                "size": f"{(self.file_size)/1024/1024:,.2f} MiB",
                "duration": str(timedelta(seconds=self.duration)),
                "bitrate": f"{(self.bitrate)/1000:,.2f} kbps",
            },
            "V": {
                "codec": self.video_codec,
                "colorspace": self.video_colorspace,
                "frameSize": self.frame_size,
                "frameRate": f"{self.framerate:.2f} fps",
                # "lang": self.video_lang
            },
            "A": {
                "codec": self.audio_codec,
                "lang": self.audio_lang,
                "title": self.audio_title,
            },
            "S": {
                "codec": self.subtitle_codec,
                "lang": self.subtitle_lang,
                "title": self.subtitle_title,
            }
        }

    def __getitem__(self, key) -> Dict[str, str]:
        # Retrieve values as a dictionary and allow indexing
        return self.__dict__().get(key, {"err": "No value"})

