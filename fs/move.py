import multiprocessing
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


def is_dir_having_file(dir_path: Path) -> bool:
    has_file = False
    for element_path in dir_path.iterdir():
        if element_path.is_file() and element_path.stat().st_size > 0:
            has_file = True
        elif element_path.is_dir():
            has_file = has_file or is_dir_having_file(element_path)

        if has_file:
            break

    return has_file


def is_same_content(file_a: Path, file_b: Path) -> bool:
    if not file_a.is_file():
        return False
    if not file_b.is_file():
        return False
    with open(file_a, "rb") as fa:
        ca: bytes = fa.read()
    with open(file_b, "rb") as fb:
        cb: bytes = fb.read()
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
    ext=dict.fromkeys(["bms", "bml", "bme", "pms", "txt", "bmson"], ReplaceAction.CheckReplace),
    default=ReplaceAction.Replace,
)

DEFAULT_MOVE_OPTIONS = MoveOptions()
DEFAULT_REPLACE_OPTIONS = ReplaceOptions()


def move_elements_across_dir(
    dir_path_ori: Path,
    dir_path_dst: Path,
    options: MoveOptions = DEFAULT_MOVE_OPTIONS,
    replace_options: ReplaceOptions = DEFAULT_REPLACE_OPTIONS,
) -> None:
    ori_path = dir_path_ori
    dst_path = dir_path_dst

    if ori_path.resolve() == dst_path.resolve():
        return
    if not ori_path.is_dir():
        return

    # Dst directory not exist? Move it
    if not dst_path.is_dir():
        shutil.move(ori_path, dst_path)
        return

    next_folder_paths: list[tuple[Path, Path]] = []
    write_ops: list[tuple[Path, Path]] = []
    reserved_paths: set[Path] = set()
    reserve_lock = threading.Lock()

    def plan_move_file(ori_item: Path, dst_item: Path) -> tuple[Path, Path] | None:
        # Replace?
        file_ext = ori_item.suffix.lstrip(".")
        action = replace_options.ext.get(file_ext) or replace_options.default

        def plan_move() -> tuple[Path, Path]:
            return (ori_item, dst_item)

        def plan_move_rename() -> tuple[Path, Path] | None:
            # 计划重命名后的移动，不实际写入
            file_name = dst_item.name
            for i in range(100):
                name = Path(file_name).stem
                ext = Path(file_name).suffix.lstrip(".")
                new_file_name = f"{name}.{i}.{ext}"
                new_dst_path = dst_path / new_file_name
                # 并发下使用预占位避免冲突
                with reserve_lock:
                    if new_dst_path in reserved_paths:
                        continue
                    if new_dst_path.is_file():
                        if is_same_content(ori_item, new_dst_path):
                            # 已存在且内容相同：无需移动
                            return None
                        # 存在但内容不同，尝试下一个序号
                        continue
                    reserved_paths.add(new_dst_path)
                return (ori_item, new_dst_path)
            return None

        match action:
            case ReplaceAction.Replace:
                return plan_move()
            case ReplaceAction.Skip:
                if dst_item.is_file():
                    return None
                return plan_move()
            case ReplaceAction.Rename:
                return plan_move_rename()
            case ReplaceAction.CheckReplace:
                if not dst_item.is_file():
                    return plan_move()
                elif is_same_content(ori_item, dst_item):
                    # 内容相同？仍计划移动以统一位置
                    return plan_move()
                else:
                    return plan_move_rename()

    def plan_move_dir(ori_item: Path, dst_item: Path) -> tuple[Path, Path] | None:
        # 目录：若目标不存在则计划整体移动，否则递归后续
        if not dst_item.is_dir():
            return (ori_item, dst_item)
        else:
            next_folder_paths.append((ori_item, dst_item))
            return None

    def plan_action(ori_item: Path, dst_item: Path) -> tuple[Path, Path] | None:
        if ori_item.is_file():
            return plan_move_file(ori_item, dst_item)
        elif ori_item.is_dir():
            return plan_move_dir(ori_item, dst_item)
        return None

    # Check Dst Dir
    if ori_path.is_dir() and not dst_path.is_dir():
        shutil.move(ori_path, dst_path)
        return

    # 第一阶段：仅执行读操作与规划
    dir_lists: list[tuple[Path, Path]] = [
        (ori_path / element_path.name, dst_path / element_path.name) for element_path in ori_path.iterdir()
    ]

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() or 4) as executor:
        futures = [executor.submit(plan_action, path_ori, path_dst) for path_ori, path_dst in dir_lists]
        for f in as_completed(futures):
            try:
                res = f.result()
                if res is not None:
                    write_ops.append(res)
            except Exception as e:
                print(f" !_! Move plan error: {e}")

    # 第二阶段：等待读操作完成后，统一执行写操作（批量并发）
    def _do_move(src: Path, dst: Path) -> None:
        if options.print_info:
            print(f" - Moving from {src} to {dst}")
        shutil.move(src, dst)

    with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() or 4) as executor:
        futures = [executor.submit(_do_move, src, dst) for src, dst in write_ops]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f" !_! Move error: {e}")

    # Next Level
    for ori_subpath, dst_subpath in next_folder_paths:
        move_elements_across_dir(ori_subpath, dst_subpath, options)

    # Clean Source
    if replace_options.default != ReplaceAction.Skip or not is_dir_having_file(ori_path):
        try:
            shutil.rmtree(ori_path)
        except PermissionError:
            print(f" x PermissionError! ({ori_path})")
