import shutil
from pathlib import Path

from fs.move import is_dir_having_file, move_elements_across_dir
from fs.rawpack import (
    get_num_set_file_names,
    move_out_files_in_folder_in_cache_dir,
    unzip_file_to_cache_dir,
)
from options import Input, InputType, Option


def unzip_numeric_to_bms_folder(pack_dir: Path, cache_dir: Path, root_dir: Path, confirm: bool = False) -> None:
    if not cache_dir.is_dir():
        cache_dir.mkdir()
    if not root_dir.is_dir():
        root_dir.mkdir()

    num_set_file_names: list[str] = get_num_set_file_names(pack_dir)

    if confirm:
        for file_name in num_set_file_names:
            print(f" --> {file_name}")
        selection = input("-> Confirm [y/N]:")
        if not selection.lower().startswith("y"):
            print("Aborted.")
            return

    for file_name in num_set_file_names:
        file_path = pack_dir / file_name
        id_str = file_name.split(" ")[0]

        # Prepare an empty cache dir
        cache_dir_path = cache_dir / id_str

        if cache_dir_path.is_dir() and is_dir_having_file(cache_dir_path):
            shutil.rmtree(cache_dir_path)

        if not cache_dir_path.is_dir():
            cache_dir_path.mkdir()

        # Unpack & Copy
        unzip_file_to_cache_dir(file_path, cache_dir_path)

        # Move files in dir
        move_result = move_out_files_in_folder_in_cache_dir(cache_dir_path)
        if not move_result:
            continue

        # Find Existing Target dir
        target_dir_path = None
        for dir_name in [p.name for p in root_dir.iterdir()]:
            dir_path = root_dir / dir_name
            if not dir_path.is_dir():
                continue
            if not (
                dir_name.startswith(id_str)
                and (len(dir_name) == len(id_str) or dir_name[len(id_str) :].startswith("."))
            ):
                continue
            target_dir_path = dir_path

        # Create New Target dir
        if target_dir_path is None:
            target_dir_path = root_dir / id_str

        # Move cache to bms dir
        print(f" > Moving files in {cache_dir_path} to {target_dir_path}")
        move_elements_across_dir(cache_dir_path, target_dir_path)
        try:
            cache_dir_path.rmdir()
        except FileNotFoundError:
            pass

        # Move File to Another dir
        print(f" > Finish dealing with file: {file_name}")
        used_pack_dir = pack_dir / "BOFTTPacks"
        if not used_pack_dir.is_dir():
            used_pack_dir.mkdir()
        shutil.move(file_path, used_pack_dir / file_name)


def unzip_with_name_to_bms_folder(pack_dir: Path, cache_dir: Path, root_dir: Path, confirm: bool = False) -> None:
    if not cache_dir.is_dir():
        cache_dir.mkdir()
    if not root_dir.is_dir():
        root_dir.mkdir()

    num_set_file_names: list[str] = [
        file_name
        for file_name in [p.name for p in pack_dir.iterdir()]
        if (pack_dir / file_name).is_file()
        and (file_name.endswith(".zip") or file_name.endswith(".7z") or file_name.endswith(".rar"))
    ]

    if confirm:
        for file_name in num_set_file_names:
            print(f" --> {file_name}")
        selection = input("-> Confirm [y/N]:")
        if not selection.lower().startswith("y"):
            print("Aborted.")
            return

    for file_name in num_set_file_names:
        file_path = pack_dir / file_name
        file_name_without_ext = file_path.stem
        while len(file_name_without_ext) > 0 and file_name_without_ext[-1] == ".":
            file_name_without_ext = file_name_without_ext[:-1]

        # Prepare an empty cache dir
        cache_dir_path = cache_dir / file_name_without_ext

        if cache_dir_path.is_dir() and is_dir_having_file(cache_dir_path):
            shutil.rmtree(cache_dir_path)

        if not cache_dir_path.is_dir():
            cache_dir_path.mkdir()

        # Unpack & Copy
        unzip_file_to_cache_dir(file_path, cache_dir_path)

        # Move files in dir
        move_result = move_out_files_in_folder_in_cache_dir(cache_dir_path)
        if not move_result:
            continue

        target_dir_path = root_dir / file_name_without_ext

        # Move cache to bms dir
        print(f" > Moving files in {cache_dir_path} to {target_dir_path}")
        move_elements_across_dir(cache_dir_path, target_dir_path)
        try:
            cache_dir_path.rmdir()
        except FileNotFoundError:
            pass

        # Move File to Another dir
        print(f" > Finish dealing with file: {file_name}")
        used_pack_dir = pack_dir / "BOFTTPacks"
        if not used_pack_dir.is_dir():
            used_pack_dir.mkdir()
        shutil.move(file_path, used_pack_dir / file_name)


def _rename_file_with_num(dir: Path, file_name: str, input_num: int) -> None:
    file_path = dir / file_name
    new_file_name = f"{input_num} {file_name}"
    new_file_path = dir / new_file_name
    shutil.move(file_path, new_file_path)
    print(f"Rename {file_name} to {new_file_name}.")
    print()


def _set_file_num(
    dir: Path,
    allow_ext: list[str] | None = None,
    disallow_ext: list[str] | None = None,
    allow_others: bool = True,
) -> None:
    if disallow_ext is None:
        disallow_ext = []
    if allow_ext is None:
        allow_ext = []
    file_names = []
    for file_name in [p.name for p in dir.iterdir()]:
        file_path = dir / file_name
        # Not File?
        if not file_path.is_file():
            continue
        # Has been numbered?
        if file_name.split()[0].isdigit():
            continue
        # Linux: Has Partial File?
        part_file_path = file_path.with_name(f"{file_path.name}.part")
        if part_file_path.is_file():
            continue
        # Linux: Empty File?
        if file_path.stat().st_size == 0:
            continue
        # Is Allowed?
        file_ext = file_name.rsplit(".", 1)[-1]
        allowed = allow_others
        if file_ext in allow_ext:
            allowed = True
        elif file_ext in disallow_ext:
            allowed = False
        if not allowed:
            continue
        file_names.append(file_name)

    # Print Selections
    print(f"Here are files in {dir}:")
    for i, file_name in enumerate(file_names):
        print(f" - {i}: {file_name}")

    print("Input a number: to set num [0] to the first selection.")
    print("Input two numbers: to set num [1] to the selection in index [0].")
    input_str = input("Input:")
    input_str_split = input_str.split()
    if len(input_str_split) == 2:
        file_name = file_names[int(input_str_split[0])]
        input_num = int(input_str_split[1])
        _rename_file_with_num(dir, file_name, input_num)
    elif len(input_str_split) == 1:
        file_name = file_names[0]
        input_num = int(input_str_split[0])
        _rename_file_with_num(dir, file_name, input_num)
    else:
        print("Invaild input.")
        print()


def set_file_num(dir: Path) -> None:
    while True:
        _set_file_num(
            dir,
            allow_ext=["zip", "7z", "rar", "mp4", "bms", "bme", "bml", "pms"],
            disallow_ext=[],
            allow_others=False,
        )
        # 询问是否继续
        cont = input("继续处理其他文件? [y/N]: ")
        if not cont.lower().startswith("y"):
            break


OPTIONS: list[Option] = [
    Option(
        unzip_numeric_to_bms_folder,
        name="BMS原文件：将赋予编号的文件，解压或放置至指定根目录下，带对应编号的作品目录（自动处理文件夹嵌套）",
        inputs=[
            Input(InputType.Path, "Pack Dir"),
            Input(InputType.Path, "Cache Dir"),
            Input(InputType.Path, "Root Dir"),
        ],
    ),
    Option(
        unzip_with_name_to_bms_folder,
        name="BMS原文件：将文件，解压或放置至指定根目录下，对应原文件名的作品目录（自动处理文件夹嵌套）",
        inputs=[
            Input(InputType.Path, "Pack Dir"),
            Input(InputType.Path, "Cache Dir"),
            Input(InputType.Path, "Root Dir"),
        ],
    ),
    Option(
        set_file_num,
        name="BMS原文件：赋予编号",
        inputs=[
            Input(InputType.Path, "RawFile Dir"),
        ],
    ),
]
