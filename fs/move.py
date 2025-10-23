import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import threading


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

DEFAULT_MOVE_OPTIONS = MoveOptions()
DEFAULT_REPLACE_OPTIONS = ReplaceOptions()


def move_elements_across_dir(
    dir_path_ori: str,
    dir_path_dst: str,
    options: MoveOptions = DEFAULT_MOVE_OPTIONS,
    replace_options: ReplaceOptions = DEFAULT_REPLACE_OPTIONS,
) -> None:
    if dir_path_ori == dir_path_dst:
        return
    if not os.path.isdir(dir_path_ori):
        return

    # Dst directory not exist? Move it
    if not os.path.isdir(dir_path_dst):
        shutil.move(dir_path_ori, dir_path_dst)
        return

    next_folder_paths: list[tuple[str, str]] = []
    write_ops: list[tuple[str, str]] = []
    reserved_paths: set[str] = set()
    reserve_lock = threading.Lock()

    def plan_move_file(ori_path: str, dst_path: str) -> tuple[str, str] | None:
        # Replace?
        file_ext = os.path.splitext(ori_path)[1]
        if file_ext.startswith("."):
            file_ext = file_ext[1:]
        action = replace_options.ext.get(file_ext) or replace_options.default

        def plan_move() -> tuple[str, str]:
            return (ori_path, dst_path)

        def plan_move_rename() -> tuple[str, str] | None:
            # 计划重命名后的移动，不实际写入
            file_name = os.path.split(dst_path)[1]
            for i in range(100):
                name, ext = os.path.splitext(file_name)
                if ext.startswith("."):
                    ext = ext[1:]
                new_file_name = f"{name}.{i}.{ext}"
                new_dst_path = os.path.join(dir_path_dst, new_file_name)
                # 并发下使用预占位避免冲突
                with reserve_lock:
                    if new_dst_path in reserved_paths:
                        continue
                    if os.path.isfile(new_dst_path):
                        if is_same_content(ori_path, new_dst_path):
                            # 已存在且内容相同：无需移动
                            return None
                        # 存在但内容不同，尝试下一个序号
                        continue
                    reserved_paths.add(new_dst_path)
                return (ori_path, new_dst_path)
            return None

        match action:
            case ReplaceAction.Replace:
                return plan_move()
            case ReplaceAction.Skip:
                if os.path.isfile(dst_path):
                    return None
                return plan_move()
            case ReplaceAction.Rename:
                return plan_move_rename()
            case ReplaceAction.CheckReplace:
                if not os.path.isfile(dst_path):
                    return plan_move()
                elif is_same_content(ori_path, dst_path):
                    # 内容相同？仍计划移动以统一位置
                    return plan_move()
                else:
                    return plan_move_rename()

    def plan_move_dir(ori_path: str, dst_path: str) -> tuple[str, str] | None:
        # 目录：若目标不存在则计划整体移动，否则递归后续
        if not os.path.isdir(dst_path):
            return (ori_path, dst_path)
        else:
            next_folder_paths.append((ori_path, dst_path))
            return None

    def plan_action(ori_path: str, dst_path: str) -> tuple[str, str] | None:
        if os.path.isfile(ori_path):
            return plan_move_file(ori_path, dst_path)
        elif os.path.isdir(ori_path):
            return plan_move_dir(ori_path, dst_path)
        return None

    # Check Dst Dir
    if os.path.isdir(dir_path_ori) and not os.path.isdir(dir_path_dst):
        shutil.move(dir_path_ori, dir_path_dst)
        return

    # 第一阶段：仅执行读操作与规划
    dir_lists: list[tuple[str, str]] = [
        (
            os.path.join(dir_path_ori, element_name),
            os.path.join(dir_path_dst, element_name),
        )
        for element_name in os.listdir(dir_path_ori)
    ]
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = [
            executor.submit(plan_action, path_ori, path_dst)
            for path_ori, path_dst in dir_lists
        ]
        for f in as_completed(futures):
            try:
                res = f.result()
                if res is not None:
                    write_ops.append(res)
            except Exception as e:
                print(f" !_! Move plan error: {e}")

    # 第二阶段：等待读操作完成后，统一执行写操作（批量并发）
    def _do_move(src: str, dst: str) -> None:
        if options.print_info:
            print(f" - Moving from {src} to {dst}")
        shutil.move(src, dst)

    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = [executor.submit(_do_move, src, dst) for src, dst in write_ops]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f" !_! Move error: {e}")

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
