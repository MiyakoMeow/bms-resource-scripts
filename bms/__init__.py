import os

from bms.encoding import BOFTT_ID_SPECIFIC_ENCODING_TABLE
from bms.parse import BMSInfo, parse_bms_file, parse_bmson_file
from bms.work import extract_work_name

BMS_FILE_EXTS = (
    ".bms",
    ".bme",
    ".bml",
    ".pms",
)
BMSON_FILE_EXTS = (".bmson",)
CHART_FILE_EXTS = BMS_FILE_EXTS + BMSON_FILE_EXTS

AUDIO_FILE_EXTS = (".flac", ".ogg", ".wav")
VIDEO_FILE_EXTS = (".mp4", ".mkv", ".avi", ".wmv", ".mpg", ".mpeg")
IMAGE_FILE_EXTS = (".jpg", ".png", ".bmp", ".svg")
MEDIA_FILE_EXTS = AUDIO_FILE_EXTS + VIDEO_FILE_EXTS + IMAGE_FILE_EXTS


def get_dir_bms_list(dir_path: str) -> list[BMSInfo]:
    """仅寻找该目录第一层的文件"""
    info_list: list[BMSInfo] = []
    # For BOFTT
    id = os.path.split(dir_path)[-1].split(".")[0]
    encoding = BOFTT_ID_SPECIFIC_ENCODING_TABLE.get(id)
    # Scan
    for file_name in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file_name)
        # Parse
        info: BMSInfo | None = None
        if file_name.lower().endswith(BMS_FILE_EXTS) and os.path.isfile(file_path):
            info = parse_bms_file(file_path, encoding)
        elif file_name.lower().endswith(BMSON_FILE_EXTS) and os.path.isfile(file_path):
            info = parse_bmson_file(file_path, encoding)
        # Append
        if info is not None:
            info_list.append(info)
    return info_list


def get_dir_bms_info(bms_dir_path: str) -> BMSInfo | None:
    # Find bmses
    bms_list: list[BMSInfo] = get_dir_bms_list(bms_dir_path)
    if len(bms_list) == 0:
        return None
    # Split title
    title = extract_work_name([bms.title for bms in bms_list])
    if title.endswith("-") and title.count("-") % 2 != 0 and title[-2].isspace():
        title = title[:-1].strip()
    artist = extract_work_name(
        [bms.artist for bms in bms_list],
        remove_tailing_sign_list=[
            "/",
            ":",
            "：",
            "-",
            "obj",
            "obj.",
            "Obj",
            "Obj.",
            "OBJ",
            "OBJ.",
        ],
    )
    genre = extract_work_name([bms.genre for bms in bms_list])
    return BMSInfo(title, artist, genre)
