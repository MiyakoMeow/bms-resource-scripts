from pathlib import Path

import openpyxl

from bms import get_dir_bms_info
from options import Input, InputType, Option, is_root_dir


def check_num_folder(bms_dir: Path, max_count: int) -> None:
    for no in range(1, max_count + 1):
        folder_path = bms_dir / str(no)
        if not folder_path.is_dir():
            print(f"{folder_path} is not exist!")


def create_num_folders(root_dir: Path, folder_count: int) -> None:
    existing_elements = [p.name for p in root_dir.iterdir() if p.is_dir()]

    for id in range(1, folder_count + 1):
        new_dir_name = f"{id}"
        id_exists = False
        for element_name in existing_elements:
            if element_name.startswith(f"{new_dir_name}"):
                id_exists = True
                break

        if id_exists:
            continue

        new_dir_path = root_dir / new_dir_name
        if not new_dir_path.is_dir():
            new_dir_path.mkdir()


def generate_work_info_table(root_dir: Path) -> None:
    print("Set default dir by env BOFTT_DIR")

    # 创建一个 workbook
    workbook = openpyxl.Workbook()
    workbook.create_sheet("BMS List")

    worksheet = workbook["BMS List"]

    # 访问目录下的BMS文件夹
    for dir_name in [p.name for p in root_dir.iterdir()]:
        dir_path = root_dir / dir_name
        if not dir_path.is_dir():
            continue
        # 获得BMS信息
        info = get_dir_bms_info(dir_path)
        if info is None:
            continue
        # 获得目录编号
        id = dir_name.split(".")[0]
        # 填充信息
        worksheet[f"A{id}"] = id
        worksheet[f"B{id}"] = info.title
        worksheet[f"C{id}"] = info.artist
        worksheet[f"D{id}"] = info.genre

    # 保存 Excel 文件
    table_path = root_dir / "bms_list.xlsx"
    print(f"Saving table to {table_path}")
    workbook.save(table_path)


OPTIONS: list[Option] = [
    Option(
        check_num_folder,
        name="BMS活动目录：检查各个的编号对应的文件夹是否存在",
        inputs=[
            Input(InputType.Path, "Root Dir:"),
            Input(InputType.Int, "Create Number:"),
        ],
        check_func=is_root_dir,
    ),
    Option(
        create_num_folders,
        name="BMS活动目录：创建只带有编号的空文件夹",
        inputs=[
            Input(InputType.Path, "Root Dir:"),
            Input(InputType.Int, "Create Number:"),
        ],
        check_func=is_root_dir,
    ),
    Option(
        generate_work_info_table,
        name="BMS活动目录：生成活动作品的xlsx表格",
        inputs=[
            Input(InputType.Path, "Root Dir:"),
        ],
        check_func=is_root_dir,
    ),
]
