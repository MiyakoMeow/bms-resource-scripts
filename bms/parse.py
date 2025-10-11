import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from bms.encoding import get_bms_file_str


class BMSDifficulty(Enum):
    Unknown = 0
    Beginner = 1
    Normal = 2
    Hyper = 3
    Another = 4
    Insane = 5


@dataclass
class BMSInfo:
    title: str
    artist: str
    genre: str
    difficulty: BMSDifficulty = BMSDifficulty.Unknown
    playlevel: int = 0
    bmp_formats: list[str] = field(default_factory=list)


def parse_bms_file(file_path: str, encoding: str | None = None) -> BMSInfo:
    title = ""
    artist = ""
    genre = ""
    difficulty = BMSDifficulty.Unknown
    playlevel = 0
    ext_list = []
    with open(file_path, "rb") as file:
        file_bytes = file.read()
        file_str = get_bms_file_str(file_bytes, encoding)

        for line in file_str.splitlines():
            line = line.strip()
            if line.startswith("#ARTIST"):
                artist = line.replace("#ARTIST", "").strip()
            elif line.startswith("#TITLE"):
                title = line.replace("#TITLE", "").strip()
            elif line.startswith("#GENRE"):
                genre = line.replace("#GENRE", "").strip()
            elif line.startswith("#PLAYLEVEL"):
                value_str = line.replace("#PLAYLEVEL", "").strip()
                if len(value_str) > 0 and value_str.isdecimal():
                    playlevel_float = float(value_str)
                    playlevel = (
                        int(playlevel_float) if 0.0 <= playlevel_float <= 99.0 else -1
                    )
            elif line.startswith("#DIFFICULTY"):
                value_str = line.replace("#DIFFICULTY", "").strip()
                if len(value_str) > 0 and value_str.isdecimal():
                    value = int(float(value_str))
                    difficulty = (
                        BMSDifficulty(value)
                        if 0 <= value <= 5
                        else BMSDifficulty.Unknown
                    )
            elif line.startswith("#BMP"):
                value_str = line.replace("#BMP", "").strip()
                ext = os.path.splitext(value_str)[1]
                if ext is not None:
                    ext_list.append(ext)

    return BMSInfo(title, artist, genre, difficulty, playlevel, ext_list)


def parse_bmson_file(file_path: str, encoding: str | None = None) -> BMSInfo:
    title = ""
    artist = ""
    genre = ""
    difficulty = BMSDifficulty.Unknown
    playlevel = 0
    with open(file_path, "rb") as file:
        file_bytes = file.read()
        file_str = get_bms_file_str(file_bytes, encoding)

        try:
            bmson_info: dict[Any, Any] = json.loads(file_str)
        except json.JSONDecodeError:
            print(f" !_!: Json Decode Error! {file_path}")
            return BMSInfo("Error", "Error", "Error")

        # Get info
        def dict_get(data: dict[Any, Any], *info: Any) -> Any | None:
            now: dict[Any, Any] | None = data
            for i in info:
                if now is not None:
                    now = now.get(i)
            return now

        title = dict_get(bmson_info, "info", "title") or ""
        artist = dict_get(bmson_info, "info", "artist") or ""
        genre = dict_get(bmson_info, "info", "genre") or ""
        playlevel = int(dict_get(bmson_info, "info", "level") or 0)
        ext_list = []
        bga_headers = dict_get(bmson_info, "bga", "bga_header")
        if bga_headers is not None:
            for bga_header in bga_headers:
                file_name = bga_header["name"]
                ext = os.path.splitext(file_name)[1]
                if ext is not None:
                    ext_list.append(ext)

    return BMSInfo(title, artist, genre, difficulty, playlevel, ext_list)
