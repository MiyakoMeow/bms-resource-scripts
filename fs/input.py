import os

# 获取当前文件的绝对路径
_CURRENT_PATH = os.path.abspath(__file__)

# 获取当前文件所在目录
_CURRENT_DIR = os.path.dirname(_CURRENT_PATH)

_LOG_FILE_PATH = os.path.join(_CURRENT_DIR, "history.log")


def input_path() -> str:
    if not os.path.isfile(_LOG_FILE_PATH):
        with open(_LOG_FILE_PATH, "w") as f:
            f.write("\n")
    paths = []
    with open(_LOG_FILE_PATH) as f:
        paths = [path.lstrip() for path in f.readlines()]
        paths = [path for path in paths if len(path) > 0]
        paths = [(path[:-1] if path.endswith("\n") else path) for path in paths]
        paths = [(path[:-1] if path.endswith("\r") else path) for path in paths]
        paths = [
            (path[1:-1] if path.startswith('"') and path.endswith('"') else path)
            for path in paths
        ]
        paths = [path.lstrip() for path in paths]
    # Tips
    # Select Path
    if len(paths) > 0:
        print("Input path start. These are paths used before:")
    for i, path in enumerate(paths):
        print(f" -> {i}: {path}")
    selection_str = input(
        "Input path directly, or input a number(index) above to select:"
    )
    selection = paths[int(selection_str)] if selection_str.isdigit() else selection_str
    # Save
    if not selection_str.isdigit():
        with open(_LOG_FILE_PATH, "a") as f:
            f.write(selection)
            f.write("\n")
    return selection


if __name__ == "__main__":
    print(input_path())
