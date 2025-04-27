import os
from typing import Callable, Dict, List, Set, Tuple
import re
import shutil

from fs.move import (
    REPLACE_OPTION_UPDATE_PACK,
    move_elements_across_dir,
)

# 日文平假名
RE_JAPANESE_HIRAGANA = re.compile("[\u3040-\u309f]+")
# 日文片假名
RE_JAPANESE_KATAKANA = re.compile("[\u30a0-\u30ff]+")
# 汉字
RE_CHINESE_CHARACTER = re.compile("[\u4e00-\u9fa5]+")

RULES: List[Tuple[str, Callable[[str], bool]]] = [
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


def _rules_find(name: str) -> str:
    for group_name, func in RULES:
        if not func(name):
            continue
        return group_name
    return "未分类"


def split_folders_with_first_char(root_dir: str):
    root_folder_name = os.path.split(root_dir)[-1]
    if not os.path.isdir(root_dir):
        print(f"{root_dir} is not a dir! Aborting...")
        return
    if root_dir.endswith("]"):
        print(f"{root_dir} endswith ']'. Aborting...")
        return
    parent_dir = os.path.join(root_dir, "..")
    for element_name in os.listdir(root_dir):
        element_path = os.path.join(root_dir, element_name)
        # Find target dir
        rule = _rules_find(element_name)
        target_dir = os.path.join(parent_dir, f"{root_folder_name} [{rule}]")
        if not os.path.isdir(target_dir):
            os.mkdir(target_dir)
        # Move
        target_path = os.path.join(target_dir, element_name)
        shutil.move(element_path, target_path)


def undo_split_pack(root_dir: str):
    if not os.path.isdir(root_dir):
        os.mkdir(root_dir)
    root_folder_name = os.path.split(root_dir)[-1]
    parent_dir = os.path.join(root_dir, "..")
    pairs: List[Tuple[str, str]] = []
    for folder_name in os.listdir(parent_dir):
        folder_path = os.path.join(parent_dir, folder_name)
        if folder_name.startswith(f"{root_folder_name} [") and folder_name.endswith(
            "]"
        ):
            print(f" - {root_dir} <- {folder_path}")
            pairs.append((folder_path, root_dir))

    confirm = input("Confirm? [y/N]")
    if not confirm.lower().startswith("y"):
        return

    for from_dir, to_dir in pairs:
        move_elements_across_dir(from_dir, to_dir)


def merge_split_folders(root_dir: str):
    dir_names: List[str] = [
        dir_name
        for dir_name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, dir_name))
    ]

    pairs: List[Tuple[str, str]] = []

    for dir_name in dir_names:
        dir_path = os.path.join(root_dir, dir_name)
        if not os.path.isdir(dir_path):
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
            dir_path_without_artist = os.path.join(root_dir, dir_name_without_artist)
            if not os.path.isdir(dir_path_without_artist):
                continue
            # Check has another folders
            dir_names_with_starter = [
                dir_name
                for dir_name in dir_names
                if dir_name.startswith(f"{dir_name_without_artist} [")
            ]
            if len(dir_names_with_starter) > 2:
                print(
                    " !_! {} have more then 2 folders! {}".format(
                        dir_name_without_artist, dir_names_with_starter
                    )
                )
                continue

            # Append
            pairs.append((dir_name, dir_name_without_artist))

    # Check dumplate
    last_from_dir_name = ""
    dumplate_list: List[str] = []
    for target_dir_name, from_dir_name in pairs:
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
        print("- Find Dir pair: {} <- {}".format(target_dir_name, from_dir_name))

    selection = input(f"There are {len(pairs)} actions. Do transfering? [y/N]:")
    if not selection.lower().startswith("y"):
        print("Aborted.")
        return

    for target_dir_name, from_dir_name in pairs:
        from_dir_path = os.path.join(root_dir, from_dir_name)
        target_dir_path = os.path.join(root_dir, target_dir_name)
        print(f" - Moving: {target_dir_name} <- {from_dir_name}")
        move_elements_across_dir(from_dir_path, target_dir_path)


def move_works_in_pack(root_dir_from: str, root_dir_to: str):
    if root_dir_from == root_dir_to:
        return
    move_count = 0
    for bms_dir_name in os.listdir(root_dir_from):
        bms_dir = os.path.join(root_dir_from, bms_dir_name)
        if not os.path.isdir(bms_dir):
            continue

        print(f"Moving: {bms_dir_name}")

        dst_bms_dir = os.path.join(root_dir_to, bms_dir_name)
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


def remove_unneed_media_files(root_dir: str, rules: List[Tuple[List[str], List[str]]]):
    remove_pairs: List[Tuple[str, str]] = []
    removed_files: Set[str] = set()
    for file_name in os.listdir(root_dir):
        file_path = os.path.join(root_dir, file_name)
        if not os.path.isfile(file_path):
            continue

        file_ext = file_name.rsplit(".")[-1]
        for upper_exts, lower_exts in rules:
            if file_ext not in upper_exts:
                continue
            # File is empty?
            if os.path.getsize(file_path) == 0:
                print(f" - !x!: File {file_path} is Empty! Skipping...")
                continue
            # File is in upper_exts, search for file in lower_exts.
            for lower_ext in lower_exts:
                replacing_file_path = f"{file_path[: -len(file_ext)] + lower_ext}"
                # File not exist?
                if not os.path.isfile(replacing_file_path):
                    continue
                if replacing_file_path in removed_files:
                    continue
                remove_pairs.append((file_path, replacing_file_path))
                removed_files.add(replacing_file_path)

    if len(remove_pairs) > 0:
        print(f"Entering: {root_dir}")

    # Remove file
    for file_path, replacing_file_path in remove_pairs:
        print(
            f"- Remove file {os.path.split(replacing_file_path)[-1]}, because {os.path.split(file_path)[-1]} exists."
        )
        os.remove(replacing_file_path)

    # Finished: Count Ext
    ext_count: Dict[str, List[str]] = dict()
    for file_name in os.listdir(root_dir):
        file_path = os.path.join(root_dir, file_name)
        if not os.path.isfile(file_path):
            continue

        # Count ext
        file_ext = file_name.rsplit(".")[-1]
        if ext_count.get(file_ext) is None:
            ext_count.update({file_ext: [file_name]})
        else:
            ext_count[file_ext].append(file_name)

    # Do With Ext Count
    mp4_count = ext_count.get("mp4")
    if mp4_count is not None and len(mp4_count) > 1:
        print(f" - Tips: {root_dir} has more than 1 mp4 files! {mp4_count}")


REMOVE_MEDIA_RULE_ORAJA: List[Tuple[List[str], List[str]]] = [
    (["mp4"], ["avi", "wmv", "mpg", "mpeg"]),
    (["avi"], ["wmv", "mpg", "mpeg"]),
    (["flac", "wav"], ["ogg"]),
    (["flac"], ["wav"]),
    (["mpg"], ["wmv"]),
]
REMOVE_MEDIA_RULE_WAV_FILL_FLAC: List[Tuple[List[str], List[str]]] = [
    (["wav"], ["flac"]),
]
REMOVE_MEDIA_RULE_MPG_FILL_WMV: List[Tuple[List[str], List[str]]] = [
    (["mpg"], ["wmv"]),
]

REMOVE_MEDIA_FILE_RULES: List[List[Tuple[List[str], List[str]]]] = [
    REMOVE_MEDIA_RULE_ORAJA,
    REMOVE_MEDIA_RULE_WAV_FILL_FLAC,
    REMOVE_MEDIA_RULE_MPG_FILL_WMV,
]
