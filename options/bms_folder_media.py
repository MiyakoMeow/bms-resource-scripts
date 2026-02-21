from pathlib import Path

from bms import AUDIO_FILE_EXTS, VIDEO_FILE_EXTS
from media.audio import AUDIO_PRESETS, bms_folder_transfer_audio
from media.video import VIDEO_PRESETS, bms_folder_transfer_video
from options import (
    Input,
    InputType,
    Option,
    check_ffmpeg_exec,
    check_flac_exec,
    check_oggenc_exec,
    is_root_dir,
)


def transfer_audio(root_dir: Path) -> None:
    print("选择目标格式：")
    for i, preset in enumerate(AUDIO_PRESETS):
        print(f" - {i}: {preset}")

    max_index = len(AUDIO_PRESETS) - 1
    while True:
        selection = input(f"输入数字选择目标格式（0-{max_index}）：")
        if not selection.isdigit():
            print("请输入有效的数字！")
            continue
        selection_int = int(selection)
        if 0 <= selection_int <= max_index:
            break
        print(f"请输入 0 到 {max_index} 之间的数字！")

    preset = AUDIO_PRESETS[selection_int]
    # 执行
    print("Start Exec...")
    bms_folder_transfer_audio(
        root_dir,
        input_ext=list(AUDIO_FILE_EXTS),
        transfer_mode=[preset],
        remove_origin_file_when_success=True,
        remove_origin_file_when_failed=False,
        stop_on_error=True,
    )


def transfer_video(root_dir: Path) -> None:
    print("选择目标格式：")
    for i, preset in enumerate(VIDEO_PRESETS):
        print(f" - {i}: {preset}")

    max_index = len(VIDEO_PRESETS) - 1
    while True:
        selection = input(f"输入数字选择目标格式（0-{max_index}）：")
        if not selection.isdigit():
            print("请输入有效的数字！")
            continue
        selection_int = int(selection)
        if 0 <= selection_int <= max_index:
            break
        print(f"请输入 0 到 {max_index} 之间的数字！")

    preset = VIDEO_PRESETS[selection_int]
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
        check_func=[is_root_dir, check_ffmpeg_exec, check_flac_exec, check_oggenc_exec],
    ),
    Option(
        func=transfer_video,
        name="BMS根目录：视频文件转换",
        inputs=[
            Input(InputType.Path, "Root Dir"),
        ],
        check_func=[is_root_dir, check_ffmpeg_exec],
    ),
]
