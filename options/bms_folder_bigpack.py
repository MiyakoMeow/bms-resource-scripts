import re
import shutil
from collections.abc import Callable
from pathlib import Path

from fs.move import (
    REPLACE_OPTION_UPDATE_PACK,
    is_dir_having_file,
    move_elements_across_dir,
)
from options import Input, InputType, Option, is_not_a_dir, is_root_dir
from options.bms_folder import remove_zero_sized_media_files

# 日文平假名
RE_JAPANESE_HIRAGANA = re.compile("[\u3040-\u309f]+")
# 日文片假名
RE_JAPANESE_KATAKANA = re.compile("[\u30a0-\u30ff]+")
# 汉字
RE_CHINESE_CHARACTER = re.compile("[\u4e00-\u9fa5]+")

FIRST_CHAR_RULES: list[tuple[str, Callable[[str], bool]]] = [
    ("0-9", lambda name: "0" <= name[0].upper() <= "9"),
    ("ABCD", lambda name: "A" <= name[0].upper() <= "D"),
    ("EFGHIJK", lambda name: "E" <= name[0].upper() <= "K"),
    ("LMNOPQ", lambda name: "L" <= name[0].upper() <= "Q"),
    ("RST", lambda name: "R" <= name[0].upper() <= "T"),
    ("UVWXYZ", lambda name: "U" <= name[0].upper() <= "Z"),
    ("平假名", lambda name: RE_JAPANESE_HIRAGANA.search(name[0]) is not None),
    ("片假名", lambda name: RE_JAPANESE_KATAKANA.search(name[0]) is not None),
    ("汉字", lambda name: RE_CHINESE_CHARACTER.search(name[0]) is not None),
    ("+", lambda name: len(name) > 0),
]


def _first_char_rules_find(name: str) -> str:
    for group_name, func in FIRST_CHAR_RULES:
        if not func(name):
            continue
        return group_name
    return "未分类"


def split_folders_with_first_char(root_dir: str) -> None:
    root_path = Path(root_dir)
    root_folder_name = root_path.name
    if not root_path.is_dir():
        print(f"{root_dir} is not a dir! Aborting...")
        return
    if root_dir.endswith("]"):
        print(f"{root_dir} endswith ']'. Aborting...")
        return
    parent_dir = root_path.parent
    for element in root_path.iterdir():
        # Find target dir
        rule = _first_char_rules_find(element.name)
        target_dir = parent_dir / f"{root_folder_name} [{rule}]"
        if not target_dir.is_dir():
            target_dir.mkdir()
        # Move
        target_path = target_dir / element.name
        shutil.move(str(element), str(target_path))

    # Remove the original folder when possible
    if not is_dir_having_file(root_path):
        root_path.rmdir()


def undo_split_pack(root_dir: str) -> None:
    root_path = Path(root_dir)
    root_folder_name = root_path.name
    parent_dir = root_path.parent
    pairs: list[tuple[Path, Path]] = []
    for folder in parent_dir.iterdir():
        if folder.name.startswith(f"{root_folder_name} [") and folder.name.endswith("]"):
            print(f" - {root_dir} <- {folder}")
            pairs.append((folder, root_path))

    confirm = input("Confirm? [y/N]")
    if not confirm.lower().startswith("y"):
        return

    for from_dir, to_dir in pairs:
        move_elements_across_dir(from_dir, to_dir)


def merge_split_folders(root_dir: str) -> None:
    root_path = Path(root_dir)
    dir_names: list[str] = [dir_name.name for dir_name in root_path.iterdir() if dir_name.is_dir()]

    pairs: list[tuple[str, str]] = []

    for dir_name in dir_names:
        dir_path = root_path / dir_name
        if not dir_path.is_dir():
            continue
        # Situation 1: endswith "]"
        if dir_name.endswith("]"):
            # Find dir_name_without_artist
            dir_name_mps_i = dir_name.rfind("[")
            if dir_name_mps_i == -1:
                continue
            dir_name_without_artist = dir_name[: dir_name_mps_i - 1]
            if len(dir_name_without_artist) == 0:
                continue
            # Check folder
            dir_path_without_artist = root_path / dir_name_without_artist
            if not dir_path_without_artist.is_dir():
                continue
            # Check has another folders
            dir_names_with_starter = [
                dir_name for dir_name in dir_names if dir_name.startswith(f"{dir_name_without_artist} [")
            ]
            if len(dir_names_with_starter) > 2:
                print(f" !_! {dir_name_without_artist} have more then 2 folders! {dir_names_with_starter}")
                continue

            # Append
            pairs.append((dir_name, dir_name_without_artist))

    # Check dumplate
    last_from_dir_name = ""
    dumplate_list: list[str] = []
    for _target_dir_name, from_dir_name in pairs:
        if last_from_dir_name == from_dir_name:
            dumplate_list.append(from_dir_name)
        last_from_dir_name = from_dir_name

    if len(dumplate_list) > 0:
        print("Dumplate!")
        for name in dumplate_list:
            print(f" -> {name}")
        exit()

    # Confirm
    for target_dir_name, from_dir_name in pairs:
        # Print
        print(f"- Find Dir pair: {target_dir_name} <- {from_dir_name}")

    selection = input(f"There are {len(pairs)} actions. Do transfering? [y/N]:")
    if not selection.lower().startswith("y"):
        print("Aborted.")
        return

    for target_dir_name, from_dir_name in pairs:
        from_dir_path = root_path / from_dir_name
        target_dir_path = root_path / target_dir_name
        print(f" - Moving: {target_dir_name} <- {from_dir_name}")
        move_elements_across_dir(from_dir_path, target_dir_path)


def move_works_in_pack(root_dir_from: str, root_dir_to: str) -> None:
    if root_dir_from == root_dir_to:
        return
    root_from_path = Path(root_dir_from)
    root_to_path = Path(root_dir_to)
    move_count = 0
    for bms_dir in root_from_path.iterdir():
        if not bms_dir.is_dir():
            continue

        print(f"Moving: {bms_dir.name}")

        dst_bms_dir = root_to_path / bms_dir.name
        move_elements_across_dir(
            bms_dir,
            dst_bms_dir,
            replace_options=REPLACE_OPTION_UPDATE_PACK,
        )
        move_count += 1
    if move_count > 0:
        print(f"Move {move_count} songs.")
        return

    # Deal with song dir
    move_elements_across_dir(
        root_from_path,
        root_to_path,
        replace_options=REPLACE_OPTION_UPDATE_PACK,
    )


def _workdir_remove_unneed_media_files(work_dir: str, rule: list[tuple[list[str], list[str]]]) -> None:
    work_path = Path(work_dir)
    remove_pairs: list[tuple[Path, Path]] = []
    removed_files: set[Path] = set()
    for file in work_path.iterdir():
        if not file.is_file():
            continue

        file_ext = file.suffix.lstrip(".")
        for upper_exts, lower_exts in rule:
            if file_ext not in upper_exts:
                continue
            # File is empty?
            if file.stat().st_size == 0:
                print(f" - !x!: File {file} is Empty! Skipping...")
                continue
            # File is in upper_exts, search for file in lower_exts.
            for lower_ext in lower_exts:
                replacing_file = file.with_suffix(f".{lower_ext}")
                # File not exist?
                if not replacing_file.is_file():
                    continue
                if replacing_file in removed_files:
                    continue
                remove_pairs.append((file, replacing_file))
                removed_files.add(replacing_file)

    if len(remove_pairs) > 0:
        print(f"Entering: {work_dir}")

    # Remove file
    for file_path, replacing_file_path in remove_pairs:
        print(f"- Remove file {replacing_file_path.name}, because {file_path.name} exists.")
        replacing_file_path.unlink()

    # Finished: Count Ext
    ext_count: dict[str, list[str]] = {}
    for file in work_path.iterdir():
        if not file.is_file():
            continue

        # Count ext
        file_ext = file.suffix.lstrip(".")
        if ext_count.get(file_ext) is None:
            ext_count.update({file_ext: [file.name]})
        else:
            ext_count[file_ext].append(file.name)

    # Remove zero sized files
    remove_zero_sized_media_files(work_dir)

    # Do With Ext Count
    mp4_count = ext_count.get("mp4")
    if mp4_count is not None and len(mp4_count) > 1:
        print(f" - Tips: {work_dir} has more than 1 mp4 files! {mp4_count}")


REMOVE_MEDIA_RULE_ORAJA: list[tuple[list[str], list[str]]] = [
    (["mp4"], ["avi", "wmv", "mpg", "mpeg"]),
    (["avi"], ["wmv", "mpg", "mpeg"]),
    (["flac", "wav"], ["ogg"]),
    (["flac"], ["wav"]),
    (["mpg"], ["wmv"]),
]
REMOVE_MEDIA_RULE_WAV_FILL_FLAC: list[tuple[list[str], list[str]]] = [
    (["wav"], ["flac"]),
]
REMOVE_MEDIA_RULE_MPG_FILL_WMV: list[tuple[list[str], list[str]]] = [
    (["mpg"], ["wmv"]),
]

REMOVE_MEDIA_FILE_RULES: list[list[tuple[list[str], list[str]]]] = [
    REMOVE_MEDIA_RULE_ORAJA,
    REMOVE_MEDIA_RULE_WAV_FILL_FLAC,
    REMOVE_MEDIA_RULE_MPG_FILL_WMV,
]


def remove_unneed_media_files(root_dir: str, rule: list[tuple[list[str], list[str]]] | None = None) -> None:
    # Select Preset
    if rule is None:
        rule = []
    if len(rule) == 0:
        for i, _rule in enumerate(REMOVE_MEDIA_FILE_RULES):
            print(f"- {i}: {REMOVE_MEDIA_FILE_RULES[i]}")
        selection_str = input("Select Preset (Default: 0):")
        selection = 0
        if len(selection_str) > 0:
            selection = int(selection_str)
        rule = REMOVE_MEDIA_FILE_RULES[selection]
    print(f"Selected: {rule}")

    # Do
    root_path = Path(root_dir)
    for bms_dir in root_path.iterdir():
        if not bms_dir.is_dir():
            continue
        _workdir_remove_unneed_media_files(
            str(bms_dir),
            rule,
        )


def move_out_works(target_root_dir: str) -> None:
    target_root_path = Path(target_root_dir)
    for root_dir in target_root_path.iterdir():
        if not root_dir.is_dir():
            continue
        for work_dir in root_dir.iterdir():
            if not work_dir.is_dir():
                continue
            target_work_dir = target_root_path / work_dir.name
            # Deal with song dir
            move_elements_across_dir(
                work_dir,
                target_work_dir,
                replace_options=REPLACE_OPTION_UPDATE_PACK,
            )
        if not is_dir_having_file(root_dir):
            root_dir.rmdir()


def move_works_with_same_name(root_dir_from: str, root_dir_to: str) -> None:
    """
    将源文件夹(dir_from)中的子文件夹合并到目标文件夹(dir_to)中的对应子文件夹

    规则：
    1. 对于dir_from中的每个子文件夹A
    2. 在dir_to中查找名称包含A的子文件夹B
    3. 如果找到，将A的内容合并到B中
    4. 递归处理子文件夹内的文件结构

    参数:
        dir_from (str): 源文件夹路径
        dir_to (str): 目标文件夹路径
    """

    root_from_path = Path(root_dir_from)
    root_to_path = Path(root_dir_to)

    # 验证输入路径是否存在且为目录
    if not root_from_path.is_dir():
        raise ValueError(f"源路径不存在或不是目录: {root_dir_from}")
    if not root_to_path.is_dir():
        raise ValueError(f"目标路径不存在或不是目录: {root_dir_to}")

    # 获取源目录中的所有直接子文件夹
    from_subdirs: list[Path] = [d for d in root_from_path.iterdir() if d.is_dir()]

    # 获取目标目录中的所有直接子文件夹
    to_subdirs: list[Path] = [d for d in root_to_path.iterdir() if d.is_dir()]

    pairs: list[tuple[str, Path, str, Path]] = []

    # 遍历源目录的每个子文件夹
    for from_dir in from_subdirs:
        # 查找匹配的目标子文件夹（名称包含源文件夹名）
        for to_dir in to_subdirs:
            if from_dir.name in to_dir.name:
                pairs.append((from_dir.name, from_dir, to_dir.name, to_dir))
                break

    for from_dir_name, _from_dir_path, to_dir_name, _target_path in pairs:
        print(f" -> {from_dir_name} => {to_dir_name}")
    selection = input("是否合并？[y/N]")
    if not selection.lower().startswith("y"):
        return

    # 将源文件夹内容合并到每个匹配的目标文件夹
    for _, from_dir_path, _, target_path in pairs:
        print(f"合并: '{from_dir_path}' -> '{target_path}'")
        move_elements_across_dir(
            from_dir_path,
            target_path,
            replace_options=REPLACE_OPTION_UPDATE_PACK,
        )


def move_works_with_same_name_to_siblings(root_dir_from: str) -> None:
    """
    将源文件夹(dir_from)中的子文件夹合并到同级目录中的对应子文件夹

    规则：
    1. 对于dir_from中的每个子文件夹A
    2. 在其父目录下的所有其他同级目录中查找名称包含A的子文件夹B
    3. 如果找到，将A的内容合并到每个B中
    4. 递归处理子文件夹内的文件结构

    参数:
        dir_from (str): 源文件夹路径
    """

    root_from_path = Path(root_dir_from)

    # 验证输入路径是否存在且为目录
    if not root_from_path.is_dir():
        raise ValueError(f"源路径不存在或不是目录: {root_dir_from}")

    parent_dir = root_from_path.parent
    root_base_name = root_from_path.name

    # 获取源目录中的所有直接子文件夹
    from_subdirs: list[Path] = [d for d in root_from_path.iterdir() if d.is_dir()]

    # 收集合并对： (from_dir_path, target_path)
    pairs: list[tuple[Path, Path]] = []

    # 遍历同级目录（排除自身）
    for sibling in parent_dir.iterdir():
        if sibling.name == root_base_name or not sibling.is_dir():
            continue

        # 该同级目录中的直接子目录
        to_subdirs: list[Path] = [d for d in sibling.iterdir() if d.is_dir()]

        # 查找匹配并添加合并对
        for from_dir in from_subdirs:
            for to_dir in to_subdirs:
                if from_dir.name in to_dir.name:
                    pairs.append((from_dir, to_dir))
                    break

    for from_dir_path, target_path in pairs:
        print(f" -> {from_dir_path.name} => {target_path}")

    selection = input("是否合并到各平级目录？[y/N]")
    if not selection.lower().startswith("y"):
        return

    # 将源文件夹内容合并到每个匹配的目标文件夹
    for from_dir_path, target_path in pairs:
        print(f"合并: '{from_dir_path}' -> '{target_path}'")
        move_elements_across_dir(
            from_dir_path,
            target_path,
            replace_options=REPLACE_OPTION_UPDATE_PACK,
        )


OPTIONS: list[Option] = [
    Option(
        split_folders_with_first_char,
        name="BMS大包目录：将该目录下的作品，按照首字符分成多个文件夹",
        inputs=[Input(InputType.Path, "")],
        check_func=is_root_dir,
    ),
    Option(
        undo_split_pack,
        name="BMS大包目录：（撤销操作）将该目录下的作品，按照首字符分成多个文件夹",
        inputs=[Input(InputType.Path, "The target folder path.")],
        check_func=is_not_a_dir,
    ),
    Option(
        move_works_in_pack,
        name="BMS大包目录：将目录A下的作品，移动到目录B（自动合并）",
        inputs=[Input(InputType.Path, "From"), Input(InputType.Path, "To")],
        check_func=is_root_dir,
    ),
    Option(
        move_out_works,
        name="BMS大包父目录：移出一层目录（自动合并）",
        inputs=[Input(InputType.Path, "Target Root Dir")],
    ),
    Option(
        move_works_with_same_name,
        name="BMS大包目录：将源文件夹(dir_from)中，文件名相似的子文件夹，合并到目标文件夹(dir_to)中的对应子文件夹",
        inputs=[Input(InputType.Path, "From"), Input(InputType.Path, "To")],
        check_func=is_root_dir,
    ),
    Option(
        move_works_with_same_name_to_siblings,
        name="BMS大包目录：将该目录中文件名相似的子文件夹，合并到各平级目录中",
        inputs=[Input(InputType.Path, "Dir")],
        check_func=is_root_dir,
    ),
]

OPTIONS_LEGACY: list[Option] = [
    Option(
        merge_split_folders,
        inputs=[Input(InputType.Path, "")],
        check_func=is_not_a_dir,
    ),
]
