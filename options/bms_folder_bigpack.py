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


def split_folders_with_first_char(root_dir: Path) -> None:
    root_folder_name = root_dir.name
    if not root_dir.is_dir():
        print(f"{root_dir} is not a dir! Aborting...")
        return
    if root_folder_name.endswith("]"):
        print(f"{root_dir} endswith ']'. Aborting...")
        return
    parent_dir = root_dir.parent
    for element_name in [p.name for p in root_dir.iterdir()]:
        element_path = root_dir / element_name
        # Find target dir
        rule = _first_char_rules_find(element_name)
        target_dir = parent_dir / f"{root_folder_name} [{rule}]"
        if not target_dir.is_dir():
            target_dir.mkdir()
        # Move
        target_path = target_dir / element_name
        shutil.move(element_path, target_path)

    # Remove the original folder when possible
    if not is_dir_having_file(root_dir):
        root_dir.rmdir()


def undo_split_pack(root_dir: Path) -> None:
    root_folder_name = root_dir.name
    parent_dir = root_dir.parent
    pairs: list[tuple[Path, Path]] = []
    for folder_name in [p.name for p in parent_dir.iterdir()]:
        folder_path = parent_dir / folder_name
        if folder_name.startswith(f"{root_folder_name} [") and folder_name.endswith("]"):
            print(f" - {root_dir} <- {folder_path}")
            pairs.append((folder_path, root_dir))

    confirm = input("Confirm? [y/N]")
    if not confirm.lower().startswith("y"):
        return

    for from_dir, to_dir in pairs:
        move_elements_across_dir(from_dir, to_dir)


def merge_split_folders(root_dir: Path) -> None:
    dir_names: list[str] = [p.name for p in root_dir.iterdir() if p.is_dir()]

    pairs: list[tuple[str, str]] = []

    for dir_name in dir_names:
        dir_path = root_dir / dir_name
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
            dir_path_without_artist = root_dir / dir_name_without_artist
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
        from_dir_path = root_dir / from_dir_name
        target_dir_path = root_dir / target_dir_name
        print(f" - Moving: {target_dir_name} <- {from_dir_name}")
        move_elements_across_dir(from_dir_path, target_dir_path)


def move_works_in_pack(root_dir_from: Path, root_dir_to: Path) -> None:
    if root_dir_from == root_dir_to:
        return
    move_count = 0
    for bms_dir_name in [p.name for p in root_dir_from.iterdir()]:
        bms_dir = root_dir_from / bms_dir_name
        if not bms_dir.is_dir():
            continue

        print(f"Moving: {bms_dir_name}")

        dst_bms_dir = root_dir_to / bms_dir_name
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
        root_dir_from,
        root_dir_to,
        replace_options=REPLACE_OPTION_UPDATE_PACK,
    )


def _workdir_remove_unneed_media_files(work_dir: Path, rule: list[tuple[list[str], list[str]]]) -> None:
    remove_pairs: list[tuple[Path, Path]] = []
    removed_files: set[Path] = set()
    for file_name in [p.name for p in work_dir.iterdir()]:
        check_file_path = work_dir / file_name
        if not check_file_path.is_file():
            continue

        file_ext = check_file_path.suffix.lstrip(".")
        for upper_exts, lower_exts in rule:
            if file_ext not in upper_exts:
                continue
            # File is empty?
            if check_file_path.stat().st_size == 0:
                print(f" - !x!: File {check_file_path} is Empty! Skipping...")
                continue
            # File is in upper_exts, search for file in lower_exts.
            for lower_ext in lower_exts:
                replacing_file_path = check_file_path.with_suffix(f".{lower_ext}")
                # File not exist?
                if not replacing_file_path.is_file():
                    continue
                if replacing_file_path in removed_files:
                    continue
                remove_pairs.append((check_file_path, replacing_file_path))
                removed_files.add(replacing_file_path)

    if len(remove_pairs) > 0:
        print(f"Entering: {work_dir}")

    # Remove file
    for check_file_path, replacing_file_path in remove_pairs:
        print(f"- Remove file {replacing_file_path.name}, because {check_file_path.name} exists.")
        replacing_file_path.unlink()

    # Finished: Count Ext
    ext_count: dict[str, list[str]] = {}
    for count_file_name in [p.name for p in work_dir.iterdir()]:
        count_file_path = work_dir / count_file_name
        if not count_file_path.is_file():
            continue

        # Count ext
        file_ext = count_file_path.suffix.lstrip(".")
        if ext_count.get(file_ext) is None:
            ext_count.update({file_ext: [count_file_name]})
        else:
            ext_count[file_ext].append(count_file_name)

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


def remove_unneed_media_files(root_dir: Path, rule: list[tuple[list[str], list[str]]] | None = None) -> None:
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
    for bms_dir_name in [p.name for p in root_dir.iterdir()]:
        bms_dir_path = root_dir / bms_dir_name
        if not bms_dir_path.is_dir():
            continue
        _workdir_remove_unneed_media_files(
            bms_dir_path,
            rule,
        )


def move_out_works(target_root_dir: Path) -> None:
    for root_dir_name in [p.name for p in target_root_dir.iterdir()]:
        root_dir_path = target_root_dir / root_dir_name
        if not root_dir_path.is_dir():
            continue
        for work_dir_name in [p.name for p in root_dir_path.iterdir()]:
            work_dir_path = root_dir_path / work_dir_name
            target_work_dir_path = target_root_dir / work_dir_name
            # Deal with song dir
            move_elements_across_dir(
                work_dir_path,
                target_work_dir_path,
                replace_options=REPLACE_OPTION_UPDATE_PACK,
            )
        if not is_dir_having_file(root_dir_path):
            root_dir_path.rmdir()


def move_works_with_same_name(root_dir_from: Path, root_dir_to: Path) -> None:
    """
    将源文件夹(dir_from)中的子文件夹合并到目标文件夹(dir_to)中的对应子文件夹

    规则：
    1. 对于dir_from中的每个子文件夹A
    2. 在dir_to中查找名称包含A的子文件夹B
    3. 如果找到，将A的内容合并到B中
    4. 递归处理子文件夹内的文件结构

    参数:
        dir_from (Path): 源文件夹路径
        dir_to (Path): 目标文件夹路径
    """

    # 验证输入路径是否存在且为目录
    if not root_dir_from.is_dir():
        raise ValueError(f"源路径不存在或不是目录: {root_dir_from}")
    if not root_dir_to.is_dir():
        raise ValueError(f"目标路径不存在或不是目录: {root_dir_to}")

    # 获取源目录中的所有直接子文件夹
    from_subdirs: list[str] = [d for d in [p.name for p in root_dir_from.iterdir()] if (root_dir_from / d).is_dir()]

    # 获取目标目录中的所有直接子文件夹
    to_subdirs: list[str] = [d for d in [p.name for p in root_dir_to.iterdir()] if (root_dir_to / d).is_dir()]

    pairs: list[tuple[str, Path, str, Path]] = []

    # 遍历源目录的每个子文件夹
    for from_dir_name in from_subdirs:
        from_dir_path: Path = root_dir_from / from_dir_name

        # 查找匹配的目标子文件夹（名称以源文件夹名开头）
        for to_dir_name in to_subdirs:
            if to_dir_name.startswith(from_dir_name):
                to_dir_path: Path = root_dir_to / to_dir_name
                pairs.append((from_dir_name, from_dir_path, to_dir_name, to_dir_path))
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


def move_works_with_same_name_to_siblings(root_dir_from: Path) -> None:
    """
    将源文件夹(dir_from)中的子文件夹合并到同级目录中的对应子文件夹

    规则：
    1. 对于dir_from中的每个子文件夹A
    2. 在其父目录下的所有其他同级目录中查找名称包含A的子文件夹B
    3. 如果找到，将A的内容合并到每个B中
    4. 递归处理子文件夹内的文件结构

    参数:
        dir_from (Path): 源文件夹路径
    """

    # 验证输入路径是否存在且为目录
    if not root_dir_from.is_dir():
        raise ValueError(f"源路径不存在或不是目录: {root_dir_from}")

    parent_dir = root_dir_from.parent
    root_base_name = root_dir_from.name

    # 获取源目录中的所有直接子文件夹
    from_subdirs: list[str] = [d for d in [p.name for p in root_dir_from.iterdir()] if (root_dir_from / d).is_dir()]

    # 收集合并对： (from_dir_path, target_path)
    pairs: list[tuple[Path, Path]] = []

    # 遍历同级目录（排除自身）
    for sibling_name in [p.name for p in parent_dir.iterdir()]:
        sibling_path = parent_dir / sibling_name
        if sibling_name == root_base_name or not sibling_path.is_dir():
            continue

        # 该同级目录中的直接子目录
        to_subdirs: list[str] = [d for d in [p.name for p in sibling_path.iterdir()] if (sibling_path / d).is_dir()]

        # 查找匹配并添加合并对
        for from_dir_name in from_subdirs:
            from_dir_path = root_dir_from / from_dir_name
            for to_dir_name in to_subdirs:
                if to_dir_name.startswith(from_dir_name):
                    target_path = sibling_path / to_dir_name
                    pairs.append((from_dir_path, target_path))
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
