import os
import shutil

from fs.move import is_dir_having_file


def remove_empty_folder(parent_dir: str) -> None:
    for dir_name in os.listdir(parent_dir):
        dir_path = os.path.join(parent_dir, dir_name)
        if not os.path.isdir(dir_path):
            continue
        if not is_dir_having_file(dir_path):
            try:
                print(f"Remove empty dir: {dir_path}")
                shutil.rmtree(dir_path)
            except PermissionError:
                print(" x PermissionError!")


def bms_dir_similarity(dir_path_a: str, dir_path_b: str) -> float:
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

    def fetch_dir_elements(dir_path: str) -> tuple[list[str], list[str], list[str]]:
        file_list: list[str] = [name or "" for name in os.listdir(dir_path)]
        media_list: list[str] = [os.path.splitext(name)[0] or "" for name in file_list if name.endswith(media_ext_list)]
        non_media_list: list[str] = [name for name in file_list if not name.endswith(media_ext_list)]
        return (file_list, media_list, non_media_list)

    file_set_a, media_set_a, non_media_set_a = [set(e_list) for e_list in fetch_dir_elements(dir_path_a)]
    if not file_set_a or not media_set_a or not non_media_set_a:
        return 0.0
    file_set_b, media_set_b, non_media_set_b = [set(e_list) for e_list in fetch_dir_elements(dir_path_b)]
    if not file_set_b or not media_set_b or not non_media_set_b:
        return 0.0
    media_set_merge = media_set_a.intersection(media_set_b)
    media_ratio = len(media_set_merge) / min(len(media_set_a), len(media_set_b))
    return media_ratio  # Use media ratio only?
