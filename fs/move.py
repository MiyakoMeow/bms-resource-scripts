import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum


def is_dir_having_file(dir_path: str) -> bool:
    has_file = False
    for element_name in os.listdir(dir_path):
        element_path = os.path.join(dir_path, element_name)
        if os.path.isfile(element_path) and os.path.getsize(element_path) > 0:
            has_file = True
        elif os.path.isdir(element_path):
            has_file = has_file or is_dir_having_file(element_path)

        if has_file:
            break

    return has_file


def is_same_content(file_a: str, file_b: str) -> bool:
    if not os.path.isfile(file_a):
        return False
    if not os.path.isfile(file_b):
        return False
    fa = open(file_a, "rb")
    ca: bytes = fa.read()
    fa.close()
    fb = open(file_b, "rb")
    cb: bytes = fb.read()
    fb.close()
    return ca == cb


@dataclass
class MoveOptions:
    print_info: bool = False


class ReplaceAction(Enum):
    Skip = 0
    Replace = 1
    Rename = 2
    CheckReplace = 12


@dataclass
class ReplaceOptions:
    ext: dict[str, ReplaceAction] = field(default_factory=dict)
    default: ReplaceAction = ReplaceAction.Replace


REPLACE_OPTION_UPDATE_PACK = ReplaceOptions(
    ext=dict.fromkeys(
        ["bms", "bml", "bme", "pms", "txt", "bmson"], ReplaceAction.CheckReplace
    ),
    default=ReplaceAction.Replace,
)


def move_elements_across_dir(
    dir_path_ori: str,
    dir_path_dst: str,
    options: MoveOptions = MoveOptions(),
    replace_options: ReplaceOptions = ReplaceOptions(),
):
    if dir_path_ori == dir_path_dst:
        return
    if not os.path.isdir(dir_path_ori):
        return
    if not os.path.isdir(dir_path_dst):
        os.mkdir(dir_path_dst)

    next_folder_paths: list[tuple[str, str]] = []

    def move_action(ori_path: str, dst_path: str):
        if options.print_info:
            print(f" - Moving from {ori_path} to {dst_path}")
        # Move
        if os.path.isfile(ori_path):
            move_file(ori_path, dst_path)
        elif os.path.isdir(ori_path):
            move_dir(ori_path, dst_path)

    def move_file(ori_path: str, dst_path: str):
        # Replace?
        file_ext = os.path.splitext(ori_path)[1]
        if file_ext.startswith("."):
            file_ext = file_ext[1:]
        action = replace_options.ext.get(file_ext) or replace_options.default

        def action_move():
            shutil.move(ori_path, dst_path)

        def action_move_rename():
            # 移动并重命名
            file_name = os.path.split(dst_path)[1]
            for i in range(100):
                name, ext = os.path.splitext(file_name)
                if ext.startswith("."):
                    ext = ext[1:]
                new_file_name = f"{name}.{i}.{ext}"
                new_dst_path = os.path.join(dir_path_dst, new_file_name)
                if os.path.isfile(new_dst_path):
                    if is_same_content(ori_path, new_dst_path):
                        break
                    continue
                shutil.move(ori_path, new_dst_path)
                break

        match action:
            case ReplaceAction.Replace:
                action_move()
            case ReplaceAction.Skip:
                if os.path.isfile(dst_path):
                    return
                action_move()
            case ReplaceAction.Rename:
                action_move_rename()
            case ReplaceAction.CheckReplace:
                if not os.path.isfile(dst_path):
                    action_move()
                elif is_same_content(ori_path, dst_path):
                    # 内容相同？
                    action_move()
                else:
                    action_move_rename()

    def move_dir(ori_path: str, dst_path: str):
        # Directly move dir
        if not os.path.isdir(dst_path):
            shutil.move(ori_path, dst_path)
        else:
            # Add child dir
            next_folder_paths.append((ori_path, dst_path))

    # Check Dst Dir
    if os.path.isdir(dir_path_ori) and not os.path.isdir(dir_path_dst):
        shutil.move(dir_path_ori, dir_path_dst)
        return

    # Start
    with ThreadPoolExecutor(max_workers=4) as executor:
        # 提交任务
        dir_lists: list[tuple[str, str]] = [
            (
                os.path.join(dir_path_ori, element_name),
                os.path.join(dir_path_dst, element_name),
            )
            for element_name in os.listdir(dir_path_ori)
        ]
        futures = [
            executor.submit(
                move_action,
                path_ori,
                path_dst,
            )
            for path_ori, path_dst in dir_lists
        ]
        # 等待任务完成
        for _ in as_completed(futures):
            pass

    # Next Level
    for ori_path, dst_path in next_folder_paths:
        move_elements_across_dir(ori_path, dst_path, options)

    # Clean Source
    if replace_options.default != ReplaceAction.Skip or not is_dir_having_file(
        dir_path_ori
    ):
        try:
            shutil.rmtree(dir_path_ori)
        except PermissionError:
            print(f" x PermissionError! ({dir_path_ori})")
