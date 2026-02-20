import shutil
from pathlib import Path

from fs.move import is_dir_having_file


def remove_empty_folder(parent_dir: Path) -> None:
    for dir_path in parent_dir.iterdir():
        if not dir_path.is_dir():
            continue
        if not is_dir_having_file(dir_path):
            try:
                print(f"Remove empty dir: {dir_path}")
                shutil.rmtree(dir_path)
            except PermissionError:
                print(" x PermissionError!")


def bms_dir_similarity(dir_path_a: Path, dir_path_b: Path) -> float:
    """两个文件夹中，非媒体文件文件名的相似度。"""
    # 相似度
    media_ext_list = (
        ".ogg",
        ".wav",
        ".flac",
        ".mp4",
        ".wmv",
        ".avi",
        ".mpg",
        ".mpeg",
        ".bmp",
        ".jpg",
        ".png",
    )

    def fetch_dir_elements(dir_path: Path) -> tuple[list[str], list[str], list[str]]:
        file_paths: list[Path] = list(dir_path.iterdir())
        media_list: list[str] = [p.stem for p in file_paths if p.is_file() and p.suffix.lower() in media_ext_list]
        non_media_list: list[str] = [
            p.name for p in file_paths if p.is_file() and p.suffix.lower() not in media_ext_list
        ]
        return ([p.name for p in file_paths], media_list, non_media_list)

    file_set_a, media_set_a, non_media_set_a = [set(e_list) for e_list in fetch_dir_elements(dir_path_a)]
    if not file_set_a or not media_set_a or not non_media_set_a:
        return 0.0
    file_set_b, media_set_b, non_media_set_b = [set(e_list) for e_list in fetch_dir_elements(dir_path_b)]
    if not file_set_b or not media_set_b or not non_media_set_b:
        return 0.0
    media_set_merge = media_set_a.intersection(media_set_b)
    media_ratio = len(media_set_merge) / min(len(media_set_a), len(media_set_b))
    return media_ratio  # Use media ratio only?
