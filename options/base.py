import os
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from bms import CHART_FILE_EXTS, MEDIA_FILE_EXTS
from fs.input import input_path


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
    check_func: Callable[..., bool] | None = None
    confirm: ConfirmType = ConfirmType.DefaultYes

    def exec(self) -> None:
        print(self.name if self.name else self.func.__name__)
        # Input
        args = []
        for i, input_arg in enumerate(self.inputs):
            print(
                f"Input {i + 1}/{len(self.inputs)}, Type: {input_arg.type}, Desc: {input_arg.description}"
            )
            res = input_arg.exec_input()
            print(f' - Input: "{res}"')
            args.append(res)
        # Check
        if self.check_func is not None:
            if not self.check_func(*args):
                print(" - exec: Check Failed.")
                return
        # Confirm
        match self.confirm:
            case ConfirmType.NoConfirm:
                pass
            case ConfirmType.DefaultYes:
                confirm = input("Confirm? [Y/n]:")
                go_pass = len(confirm) == 0 or confirm.lower().startswith("y")
                if not go_pass:
                    return
            case ConfirmType.DefaultNo:
                confirm = input("Confirm? [y/N]:")
                go_pass = confirm.lower().startswith("y")
                if not go_pass:
                    return
        # Exec
        self.func(*args)


def is_root_dir(*root_dir: str) -> bool:
    for dir in root_dir:
        result = (
            len(
                [
                    file
                    for file in os.listdir(dir)
                    if file.endswith(CHART_FILE_EXTS + MEDIA_FILE_EXTS)
                    and os.path.isfile(os.path.join(dir, file))
                ]
            )
            == 0
        )
        if not result:
            return False
    return True


def is_work_dir(*root_dir: str) -> bool:
    for dir in root_dir:
        result = (
            len(
                [
                    file
                    for file in os.listdir(dir)
                    if file.endswith(CHART_FILE_EXTS)
                    and os.path.isfile(os.path.join(dir, file))
                ]
            )
            > 0
            and len(
                [
                    file
                    for file in os.listdir(dir)
                    if file.endswith(MEDIA_FILE_EXTS)
                    and os.path.isfile(os.path.join(dir, file))
                ]
            )
            > 0
        )
        if not result:
            return False
    return True


def is_not_a_dir(dir: str) -> bool:
    return not os.path.isdir(dir)
