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


def main() -> None:
    # 按模块分组功能
    module_groups = [
        ("BMS活动", options.bms_events.OPTIONS),
        ("BMS根目录", options.bms_folder.OPTIONS),
        ("BMS大包目录", options.bms_folder_bigpack.OPTIONS),
        ("BMS活动目录", options.bms_folder_event.OPTIONS),
        ("BMS媒体", options.bms_folder_media.OPTIONS),
        ("BMS原文件", options.rawpack.OPTIONS),
        ("大包脚本", scripts.pack.OPTIONS),
    ]

    # 构建编号映射
    option_map = {}
    current_number = 1

    print("功能列表如下：")
    for module_name, module_options in module_groups:
        print(f"\n【{module_name}】")
        for option in module_options:
            option_map[current_number] = option
            print(f" - {current_number}: {option.name if option.name else option.func.__name__}")
            current_number += 1
        # 跳到下一个十位数的开头
        current_number = ((current_number - 1) // 10 + 1) * 10 + 1

    selection_str = input("\n输入要启用的功能的下标：").strip()
    while not selection_str.isdigit() or int(selection_str) not in option_map:
        print("请重新输入")
        selection_str = input("输入要启用的功能的下标：").strip()

    selection = int(selection_str)
    option_map[selection].exec()


if __name__ == "__main__":
    main()
