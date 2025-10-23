from bms import AUDIO_FILE_EXTS, VIDEO_FILE_EXTS
from media.audio import AUDIO_PRESETS, bms_folder_transfer_audio
from media.video import VIDEO_PRESETS, bms_folder_transfer_video
from options import Input, InputType, Option, is_root_dir


def transfer_audio(root_dir: str) -> None:
    print("选择目标格式：")
    for i, preset in enumerate(AUDIO_PRESETS):
        print(f" - {i}: {preset}")
    selection = ""
    while not selection.isdigit():
        selection = input(f"输入数字选择目标格式（0-{len(AUDIO_PRESETS)}）：")
    preset = AUDIO_PRESETS[int(selection)]
    # 执行
    print("Start Exec...")
    bms_folder_transfer_audio(
        root_dir,
        input_ext=list(AUDIO_FILE_EXTS),
        transfer_mode=[preset],
        remove_origin_file_when_success=True,
        remove_origin_file_when_failed=False,
        skip_on_fail=True,
    )


def transfer_video(root_dir: str) -> None:
    print("选择目标格式：")
    for i, preset in enumerate(VIDEO_PRESETS):
        print(f" - {i}: {preset}")
    selection = ""
    while not selection.isdigit():
        selection = input(f"输入数字选择目标格式（0-{len(VIDEO_PRESETS)}）：")
    preset = VIDEO_PRESETS[int(selection)]
    # 执行
    print("Start Exec...")
    bms_folder_transfer_video(
        root_dir,
        input_exts=list(VIDEO_FILE_EXTS),
        presets=[preset],
        remove_origin_file=True,
        remove_existing_target_file=True,
        use_prefered=False,
    )


OPTIONS = [
    Option(
        func=transfer_audio,
        name="BMS根目录：音频文件转换",
        inputs=[
            Input(InputType.Path, "Root Dir"),
        ],
        check_func=is_root_dir,
    ),
    Option(
        func=transfer_audio,
        name="BMS根目录：视频文件转换",
        inputs=[
            Input(InputType.Path, "Root Dir"),
        ],
        check_func=is_root_dir,
    ),
]
