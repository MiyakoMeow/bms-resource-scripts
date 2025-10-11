import subprocess

import options.bms_events
import options.bms_folder
import options.bms_folder_bigpack
import options.bms_folder_event
import options.bms_folder_media
import options.rawpack
import scripts.pack

OPTIONS = (
    options.bms_events.OPTIONS
    + options.bms_folder.OPTIONS
    + options.bms_folder_bigpack.OPTIONS
    + options.bms_folder_event.OPTIONS
    + options.bms_folder_media.OPTIONS
    + options.rawpack.OPTIONS
    + scripts.pack.OPTIONS
)


def check_exec() -> bool:
    cmds = ["flac --version", "ffmpeg -version", "oggenc -v"]
    for cmd in cmds:
        pass
        run = subprocess.run(
            cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        if run.returncode != 0:
            print(f'Run "{cmd}" failed.')
            return False
    return True


def main() -> None:
    print("Checking exec...")
    if not check_exec():
        print("Check exec failed. See README.md to install necessary suits.")
        return
    print("功能列表如下：")
    for i, option in enumerate(OPTIONS):
        print(f" - {i}: {option.name if option.name else option.func.__name__}")
    selection_str = input("输入要启用的功能的下标：").strip()
    while not selection_str.isdigit():
        print("请重新输入")
        selection_str = input("输入要启用的功能的下标：").strip()

    selection = int(selection_str)
    OPTIONS[selection].exec()


if __name__ == "__main__":
    main()
