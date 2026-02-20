import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from bms import CHART_FILE_EXTS, MEDIA_FILE_EXTS

# 获取当前文件的绝对路径
_CURRENT_PATH = Path(__file__).resolve()

# 获取当前文件所在目录
_CURRENT_DIR = _CURRENT_PATH.parent

_LOG_FILE_PATH = _CURRENT_DIR / "history.log"


def input_path() -> Path:
    if not _LOG_FILE_PATH.is_file():
        with _LOG_FILE_PATH.open("w") as f:
            f.write("\n")

    # 读取历史路径
    paths = []
    with _LOG_FILE_PATH.open() as f:
        paths = [path.lstrip() for path in f.readlines()]
        paths = [path for path in paths if len(path) > 0]
        paths = [(path[:-1] if path.endswith("\n") else path) for path in paths]
        paths = [(path[:-1] if path.endswith("\r") else path) for path in paths]
        paths = [(path[1:-1] if path.startswith('"') and path.endswith('"') else path) for path in paths]
        paths = [path.lstrip() for path in paths]

    # 去重并保持顺序，越往前代表时间越近
    unique_paths = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)
    paths = unique_paths  # 保存所有选择过的路径

    # 显示历史路径（只显示最近的5个）
    if len(paths) > 0:
        print("输入路径开始。以下是之前使用过的路径：")
        display_paths = paths[:5]  # 只显示最近的5个
        for i, path in enumerate(display_paths):
            print(f" -> {i}: {path}")
        if len(paths) > 5:
            print(f"（还有 {len(paths) - 5} 个历史路径，输入？查看全部）")

    # 获取用户输入
    selection_str = input("直接输入路径，或输入上面的数字（索引）进行选择，输入？查看所有选项：")

    # 处理帮助命令
    if selection_str.strip() in ["？", "?"]:
        if len(paths) > 0:
            print("所有可选选项：")
            for i, path in enumerate(paths):
                print(f"  {i}: {path}")
        else:
            print("暂无历史路径记录")
        selection_str = input("请输入选择：")

    # 处理选择
    if selection_str.isdigit() and 0 <= int(selection_str) < len(paths):
        selection = paths[int(selection_str)]
        # 将选中的路径移到最前面（最新的位置）
        paths.remove(selection)
        paths.insert(0, selection)
    else:
        selection = selection_str
        # 将新路径添加到最前面
        if selection not in paths:
            paths.insert(0, selection)
        else:
            # 如果已存在，移动到最前面
            paths.remove(selection)
            paths.insert(0, selection)

    # 保存更新后的路径（保存所有选择过的路径）
    with _LOG_FILE_PATH.open("w") as f:
        for path in paths:
            f.write(path + "\n")

    return Path(selection)


class InputType(Enum):
    Any = auto()
    Word = auto()
    Int = auto()
    Path = auto()


@dataclass
class Input:
    type: InputType = InputType.Any
    description: str = ""

    def exec_input(self) -> Any:
        match self.type:
            case InputType.Any:
                return input("Input:")
            case InputType.Word:
                tips = "Input a word:"
                w_str = input(tips)
                while w_str.find(" ") != -1:
                    print("Requires a word. Re-input.")
                    w_str = input(tips)
                return w_str
            case InputType.Int:
                tips = "Input a number:"
                w_str = input(tips)
                while not w_str.isdigit():
                    print("Requires a number. Re-input.")
                    w_str = input(tips)
                return int(w_str)
            case InputType.Path:
                return input_path()


class ConfirmType(Enum):
    NoConfirm = auto()
    DefaultYes = auto()
    DefaultNo = auto()


@dataclass
class Option:
    func: Callable[..., None]
    name: str = ""
    inputs: list[Input] = field(default_factory=list)
    check_func: Callable[..., bool] | list[Callable[..., bool]] | None = None
    confirm: ConfirmType = ConfirmType.DefaultYes

    def exec(self) -> None:
        print(self.name if self.name else self.func.__name__)
        # Input
        args = []
        for i, input_arg in enumerate(self.inputs):
            print(f"参数编号： {i + 1}/{len(self.inputs)}, 类型：{input_arg.type}, 描述：{input_arg.description}")
            res = input_arg.exec_input()
            print(f' - 输入："{res}"')
            args.append(res)
        # Check
        if self.check_func is not None:
            checks: list[Callable[..., bool]] = (
                self.check_func
                if isinstance(self.check_func, list)
                else [self.check_func]
                if self.check_func is not None
                else []
            )
            for idx, check in enumerate(checks, start=1):
                try:
                    passed = check(*args)
                except Exception as e:
                    print(f" - 检查 {idx} 异常：{e}")
                    return
                if not passed:
                    print(f" - 检查未通过（第 {idx} 项）。")
                    return
        # Confirm
        match self.confirm:
            case ConfirmType.NoConfirm:
                pass
            case ConfirmType.DefaultYes:
                # 在确认前打印当前输入及其描述
                if len(self.inputs) > 0:
                    print("确认以下输入：")
                    for i, input_arg in enumerate(self.inputs):
                        val = args[i] if i < len(args) else None
                        print(f" - 参数{i + 1}: {input_arg.description} = {val}")
                confirm = input("确认？ [Y/n]:")
                go_pass = len(confirm) == 0 or confirm.lower().startswith("y")
                if not go_pass:
                    return
            case ConfirmType.DefaultNo:
                # 在确认前打印当前输入及其描述
                if len(self.inputs) > 0:
                    print("确认以下输入：")
                    for i, input_arg in enumerate(self.inputs):
                        val = args[i] if i < len(args) else None
                        print(f" - 参数{i + 1}: {input_arg.description} = {val}")
                confirm = input("确认？ [y/N]:")
                go_pass = confirm.lower().startswith("y")
                if not go_pass:
                    return
        # Exec
        self.func(*args)


def is_root_dir(*root_dir: Path) -> bool:
    for dir in root_dir:
        result = (
            len([p.name for p in dir.iterdir() if p.name.endswith(CHART_FILE_EXTS + MEDIA_FILE_EXTS) and p.is_file()])
            == 0
        )
        if not result:
            return False
    return True


def is_work_dir(*root_dir: Path) -> bool:
    for dir in root_dir:
        result = (
            len([p.name for p in dir.iterdir() if p.name.endswith(CHART_FILE_EXTS) and p.is_file()]) > 0
            and len([p.name for p in dir.iterdir() if p.name.endswith(MEDIA_FILE_EXTS) and p.is_file()]) > 0
        )
        if not result:
            return False
    return True


def is_not_a_dir(dir: Path) -> bool:
    return not dir.is_dir()


# === Exec checks (split by executable) ===
def _check_exec(cmd: str, name: str) -> bool:
    run = subprocess.run(cmd, shell=True, stdin=subprocess.PIPE, capture_output=True)
    if run.returncode != 0:
        print(f' - 未找到或无法执行 {name}（命令 "{cmd}" 失败）。')
        return False
    return True


def check_ffmpeg_exec(*_args: Any) -> bool:
    return _check_exec("ffmpeg -version", "ffmpeg")


def check_flac_exec(*_args: Any) -> bool:
    return _check_exec("flac --version", "flac")


def check_oggenc_exec(*_args: Any) -> bool:
    return _check_exec("oggenc -v", "oggenc")
