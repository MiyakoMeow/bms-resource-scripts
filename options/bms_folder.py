import difflib
import shutil
from pathlib import Path

from bms import BMSInfo, get_dir_bms_info
from fs import bms_dir_similarity
from fs.move import REPLACE_OPTION_UPDATE_PACK, move_elements_across_dir
from fs.name import get_vaild_fs_name
from options import Input, InputType, Option, is_root_dir


def append_artist_name_by_bms(root_dir: Path) -> None:
    """该脚本适用于希望在作品文件夹名后添加" [艺术家]"的情况。"""
    dir_names: list[str] = [p.name for p in root_dir.iterdir() if p.is_dir()]

    pairs: list[tuple[str, str]] = []

    for dir_name in dir_names:
        dir_path = root_dir / dir_name
        if not dir_path.is_dir():
            continue
        # Has been set?
        if dir_name.endswith("]"):
            continue
        bms_info: BMSInfo | None = get_dir_bms_info(dir_path)
        if bms_info is None:
            print(f"Dir {dir_path} has no bms files!")
            continue
        new_dir_name = f"{dir_name} [{get_vaild_fs_name(bms_info.artist)}]"
        print(f"- Ready to rename: {dir_name} -> {new_dir_name}")
        pairs.append((dir_name, new_dir_name))

    selection = input("Do transfering? [y/N]:")
    if not selection.lower().startswith("y"):
        print("Aborted.")
        return

    for from_dir_name, target_dir_name in pairs:
        from_dir_path = root_dir / from_dir_name
        target_dir_path = root_dir / target_dir_name
        shutil.move(from_dir_path, target_dir_path)


def _workdir_append_name_by_bms(work_dir: Path) -> bool:
    """
    该脚本适用于原有文件夹名与BMS文件无关内容的情况。
    会在文件夹名后添加". 标题 [艺术家]"
    """
    if not work_dir.name.strip().isdigit():
        print(f"{work_dir} has been renamed! Skipping...")
        return False

    info: BMSInfo | None = get_dir_bms_info(work_dir)
    if info is None:
        print(f"{work_dir} has no bms/bmson files!")
        return False

    # Deal with info
    print(f"{work_dir} found bms title: {info.title} artist: {info.artist}")
    title = info.title
    artist = info.artist

    # Rename
    new_dir_path = work_dir.parent / f"{work_dir.name}. {get_vaild_fs_name(title)} [{get_vaild_fs_name(artist)}]"
    shutil.move(work_dir, new_dir_path)
    return True


def append_name_by_bms(root_dir: Path) -> None:
    """
    该脚本用于重命名作品文件夹。
    格式："标题 [艺术家]"
    """
    fail_list = []
    for dir_name in [p.name for p in root_dir.iterdir()]:
        dir_path = root_dir / dir_name
        if not dir_path.is_dir():
            continue
        result = _workdir_append_name_by_bms(dir_path)
        if not result:
            fail_list.append(dir_name)
    if len(fail_list) > 0:
        print("Fail Count:", len(fail_list))
        print(fail_list)


def _workdir_set_name_by_bms(work_dir: Path) -> bool:
    info: BMSInfo | None = get_dir_bms_info(work_dir)
    while info is None:
        print(f"{work_dir} has no bms/bmson files! Trying to move out.")
        bms_dir_elements = [p.name for p in work_dir.iterdir()]
        if len(bms_dir_elements) == 0:
            print(" - Empty dir! Deleting...")
            try:
                work_dir.rmdir()
            except PermissionError as e:
                print(e)
            return False
        if len(bms_dir_elements) != 1:
            print(f" - Element count: {len(bms_dir_elements)}")
            return False
        bms_dir_inner = work_dir / bms_dir_elements[0]
        if not bms_dir_inner.is_dir():
            print(f" - Folder has only a file: {bms_dir_elements[0]}")
            return False
        print(" - Moving out files...")
        move_elements_across_dir(bms_dir_inner, work_dir)
        info = get_dir_bms_info(work_dir)

    parent_dir = work_dir.parent
    if parent_dir is None:
        raise Exception("Parent is None!")

    if len(info.title) == 0 and len(info.artist) == 0:
        print(f"{work_dir}: Info title and artist is EMPTY!")
        return False

    # Rename
    new_dir_path = parent_dir / f"{get_vaild_fs_name(info.title)} [{get_vaild_fs_name(info.artist)}]"

    # Same? Ignore
    if work_dir == new_dir_path:
        return True

    print(f"{work_dir}: Rename! Title: {info.title}; Artist: {info.artist}")
    if not new_dir_path.is_dir():
        # Move Directly
        shutil.move(work_dir, new_dir_path)
        return True

    # Same dir?
    similarity = bms_dir_similarity(work_dir, new_dir_path)
    print(f" - Directory {new_dir_path} exists! Similarity: {similarity}")
    if similarity < 0.8:
        print(" - Merge canceled.")
        return False

    print(" - Merge start!")
    move_elements_across_dir(
        work_dir,
        new_dir_path,
        replace_options=REPLACE_OPTION_UPDATE_PACK,
    )
    return True


def set_name_by_bms(root_dir: Path) -> None:
    """
    该脚本用于重命名作品文件夹。
    格式："标题 [艺术家]"
    """
    fail_list = []
    for dir_name in [p.name for p in root_dir.iterdir()]:
        dir_path = root_dir / dir_name
        if not dir_path.is_dir():
            continue
        result = _workdir_set_name_by_bms(dir_path)
        if not result:
            fail_list.append(dir_name)
    if len(fail_list) > 0:
        print("Fail Count:", len(fail_list))
        print(fail_list)


def copy_numbered_workdir_names(root_dir_from: Path, root_dir_to: Path) -> None:
    """
    该脚本使用于以下情况：
    已经有一个文件夹A，它的子文件夹名为""等带有编号+小数点的形式。
    现在有另一个文件夹B，它的子文件夹名都只有编号。
    将A中的子文件夹名，同步给B的对应的子文件夹。
    """
    src_dir_names = [p.name for p in root_dir_from.iterdir() if p.is_dir()]
    # List Dst Dir
    for dir_name in [p.name for p in root_dir_to.iterdir()]:
        dir_path = root_dir_to / dir_name
        # Get Num
        dir_num = dir_name.split(" ")[0].split(".")[0]
        if not dir_num.isdigit():
            continue
        # Search src name
        for src_name in src_dir_names:
            if not src_name.startswith(dir_num):
                continue
            # Rename
            target_dir_path = root_dir_to / src_name
            print(f"Rename {dir_name} to {src_name}")
            shutil.move(dir_path, target_dir_path)
            break


def scan_folder_similar_folders(root_dir: Path, similarity_trigger: float = 0.7) -> None:
    dir_names: list[str] = [p.name for p in root_dir.iterdir() if p.is_dir()]
    print(f"当前目录下有{len(dir_names)}个文件夹。")
    # Sort
    dir_names.sort()
    # Scan
    for i, dir_name in enumerate(dir_names):
        if i == 0:
            continue
        former_dir_name = dir_names[i - 1]
        # 相似度
        similarity = difflib.SequenceMatcher(None, former_dir_name, dir_name).ratio()
        if similarity < similarity_trigger:
            continue
        print(f"发现相似项：{former_dir_name} <=> {dir_name}")


def undo_set_name(root_dir: Path) -> None:
    for dir_name in [p.name for p in root_dir.iterdir()]:
        dir_path = root_dir / dir_name
        if not dir_path.is_dir():
            continue
        new_dir_name = dir_name.split(" ")[0]
        new_dir_path = root_dir / new_dir_name
        if dir_name == new_dir_name:
            continue
        print(f"Rename {dir_name} to {new_dir_name}")
        shutil.move(dir_path, new_dir_path)


def remove_zero_sized_media_files(current_dir: Path, print_dir: bool = False) -> None:
    if print_dir:
        print(f"Entering dir: {current_dir}")

    if not current_dir.is_dir():
        print("Not a vaild dir! Aborting...")
        pass

    next_dir_list: list[str] = []

    for element_name in [p.name for p in current_dir.iterdir()]:
        element_path = current_dir / element_name
        if element_path.is_file():
            # 检查是否为临时文件
            is_temp_file = element_name.lower() in (
                "desktop.ini",
                "thumbs.db",
                ".ds_store",
            ) or element_name.startswith((".trash-", "._"))

            if is_temp_file:
                try:
                    print(f" - Remove temp file: {element_path}")
                    element_path.unlink()
                except PermissionError:
                    print(" x PermissionError!")
                continue

            # 检查是否为大小为0的媒体文件
            if not element_name.endswith((".ogg", ".wav", ".flac", ".bmp", ".mpg", ".wmv", ".mp4")):
                continue
            if element_path.stat().st_size > 0:
                continue
            try:
                print(f" - Remove empty file: {element_path}")
                element_path.unlink()
            except PermissionError:
                print(" x PermissionError!")
        elif element_path.is_dir():
            # print(f" - Found dir: {element_name}")
            next_dir_list.append(element_name)

    for next_dir_name in next_dir_list:
        remove_zero_sized_media_files(current_dir=current_dir / next_dir_name, print_dir=print_dir)


OPTIONS: list[Option] = [
    Option(
        set_name_by_bms,
        name="BMS根目录：按照BMS设置文件夹名",
        inputs=[Input(InputType.Path, "Root Dir")],
        check_func=is_root_dir,
    ),
    Option(
        append_name_by_bms,
        name="BMS根目录：按照BMS追加文件夹名",
        inputs=[Input(InputType.Path, "Root Dir")],
        check_func=is_root_dir,
    ),
    Option(
        append_artist_name_by_bms,
        name="BMS根目录：按照BMS追加文件夹艺术家名",
        inputs=[Input(InputType.Path, "Root Dir")],
        check_func=is_root_dir,
    ),
    Option(
        copy_numbered_workdir_names,
        name="BMS根目录：克隆带编号的文件夹名",
        inputs=[
            Input(InputType.Path, "Src Root Dir"),
            Input(InputType.Path, "Dst Root Dir"),
        ],
        check_func=is_root_dir,
    ),
    Option(
        scan_folder_similar_folders,
        name="BMS根目录：扫描相似文件夹名",
        inputs=[Input(InputType.Path, "Root Dir")],
        check_func=is_root_dir,
    ),
    Option(
        undo_set_name,
        inputs=[Input(InputType.Path, "Root Dir")],
        check_func=is_root_dir,
    ),
    Option(
        remove_zero_sized_media_files,
        name="BMS根目录：移除大小为0的媒体文件和临时文件",
        inputs=[Input(InputType.Path, "Root Dir")],
        check_func=is_root_dir,
    ),
]
