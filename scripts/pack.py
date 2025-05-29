import os

from fs import remove_empty_folder
from fs.sync import sync_folder, SYNC_PRESET_FOR_APPEND
from fs.rawpack import get_num_set_file_names
from fs.move import is_dir_having_file

from media.audio import (
    AUDIO_PRESET_FLAC,
    AUDIO_PRESET_FLAC_FFMPEG,
    AUDIO_PRESET_OGG_Q10,
    bms_folder_transfer_audio,
)
from media.video import (
    VIDEO_PRESET_MPEG1VIDEO_512X512,
    VIDEO_PRESET_AVI_512X512,
    VIDEO_PRESET_WMV2_512X512,
    bms_folder_transfer_video,
)

from options.base import Input, InputType, Option
from options.bms_folder_bigpack import (
    REMOVE_MEDIA_RULE_ORAJA,
    remove_unneed_media_files,
)
from options.bms_folder import copy_numbered_workdir_names, append_name_by_bms
from options.rawpack import unzip_numeric_to_bms_folder


def pack_raw_to_hq(root_dir: str):
    """This function is for parsing Raw version to HQ version. Just for beatoraja/Qwilight players."""
    # Parse Audio
    print("Parsing Audio... Phase 1: WAV -> FLAC")
    bms_folder_transfer_audio(
        root_dir=root_dir,
        input_ext=["wav"],
        transfer_mode=[AUDIO_PRESET_FLAC, AUDIO_PRESET_FLAC_FFMPEG],
        remove_origin_file_when_success=True,
        remove_origin_file_when_failed=True,
        skip_on_fail=False,
    )
    # Remove Unneed Media File
    print("Removing Unneed Files")
    remove_unneed_media_files(root_dir, rule=REMOVE_MEDIA_RULE_ORAJA)


def pack_hq_to_lq(root_dir: str):
    """This file is for parsing HQ version to LQ version. Just for LR2 players."""
    # Parse Audio
    print("Parsing Audio... Phase 1: FLAC -> OGG")
    bms_folder_transfer_audio(
        root_dir=root_dir,
        input_ext=["flac"],
        transfer_mode=[AUDIO_PRESET_OGG_Q10],
        remove_origin_file_when_success=True,
        remove_origin_file_when_failed=False,
        skip_on_fail=False,
    )
    # Parse Audio
    print("Parsing Video...")
    bms_folder_transfer_video(
        root_dir=root_dir,
        input_exts=["mp4"],
        presets=[
            VIDEO_PRESET_MPEG1VIDEO_512X512,
            VIDEO_PRESET_WMV2_512X512,
            VIDEO_PRESET_AVI_512X512,
        ],
        remove_origin_file=True,
        use_prefered=False,
    )


def _pack_setup_rawpack_to_hq_check(pack_dir: str, root_dir: str) -> bool:
    # Input 1
    print(" - Input 1: Pack dir path")
    if not os.path.isdir(pack_dir):
        print("Pack dir is not vaild dir.")
        return False
    # Print Packs
    file_id_names = get_num_set_file_names(pack_dir)
    print(" -- There are packs in pack_dir:")
    for file_name in file_id_names:
        print(f" > {file_name}")
    # Input 2
    print(" - Input 2: BMS Cache Folder path. (Input a dir path that NOT exists)")
    if os.path.isdir(root_dir):
        print("Root dir is an existing dir.")
        return False
    return True


def pack_setup_rawpack_to_hq(pack_dir: str, root_dir: str):
    """
    BMS Pack Generator by MiyakoMeow.
    - For Pack Create:
    Fast creating pack script, from: Raw Packs set numed, to: target bms folder.
    You need to set pack num before running this script, see options/rawpack.py => set_file_num
    """
    # Setup
    os.makedirs(root_dir, exist_ok=False)
    # Unzip
    print(f" > 1. Unzip packs from {pack_dir} to {root_dir}")
    cache_dir = os.path.join(root_dir, "CacheDir")
    unzip_numeric_to_bms_folder(
        root_dir=root_dir,
        pack_dir=pack_dir,
        cache_dir=cache_dir,
    )
    if not is_dir_having_file(cache_dir):
        os.rmdir(cache_dir)
    # Syncing folder name
    print(" > 2. Setting dir names from BMS Files")
    append_name_by_bms(root_dir=root_dir)
    # Parse Audio
    print(" > 3. Parsing Audio... Phase 1: WAV -> FLAC")
    bms_folder_transfer_audio(
        root_dir=root_dir,
        input_ext=["wav"],
        transfer_mode=[AUDIO_PRESET_FLAC, AUDIO_PRESET_FLAC_FFMPEG],
        remove_origin_file_when_success=True,
        skip_on_fail=False,
    )
    # Remove Unneed Media File
    print(" > 4. Removing Unneed Files")
    remove_unneed_media_files(root_dir=root_dir, rule=REMOVE_MEDIA_RULE_ORAJA)


def _pack_update_rawpack_to_hq_check(
    pack_dir: str, root_dir: str, sync_dir: str
) -> bool:
    # Input 1
    print(" - Input 1: Pack dir path")
    if not os.path.isdir(pack_dir):
        print("Pack dir is not vaild dir.")
        return False
    # Print Packs
    file_id_names = get_num_set_file_names(pack_dir)
    print(" -- There are packs in pack_dir:")
    for file_name in file_id_names:
        print(f" > {file_name}")
    # Input 2
    print(" - Input 2: BMS Cache Folder path. (Input a dir path that NOT exists)")
    if os.path.isdir(root_dir):
        print("Root dir is an existing dir.")
        return False
    # Input 3
    print(
        " - Input 3: Already exists BMS Folder path. (Input a dir path that ALREADY exists)"
    )
    print("This script will use this dir, just for name syncing and file checking.")
    if not os.path.isdir(sync_dir):
        print("Syncing dir is not vaild dir.")
        return False
    return True


def pack_update_rawpack_to_hq(pack_dir: str, root_dir: str, sync_dir: str):
    """
    BMS Pack Generator by MiyakoMeow.
     - For Pack Update:
    Fast update script, from: Raw Packs set numed, to: delta bms folder just for making pack update.
    You need to set pack num before running this script, see scripts_rawpack/rawpack_set_num.py
    """
    # Setup
    os.makedirs(root_dir, exist_ok=False)
    # Unzip
    print(f" > 1. Unzip packs from {pack_dir} to {root_dir}")
    unzip_numeric_to_bms_folder(
        root_dir=root_dir,
        pack_dir=pack_dir,
        cache_dir=os.path.join(root_dir, "CacheDir"),
    )
    # Syncing folder name
    print(f" > 2. Syncing dir name from {sync_dir} to {root_dir}")
    copy_numbered_workdir_names(sync_dir, root_dir)
    # Parse Audio
    print(" > 3. Parsing Audio... Phase 1: WAV -> FLAC")
    bms_folder_transfer_audio(
        root_dir=root_dir,
        input_ext=["wav"],
        transfer_mode=[AUDIO_PRESET_FLAC, AUDIO_PRESET_FLAC_FFMPEG],
        remove_origin_file_when_success=True,
        skip_on_fail=False,
    )
    # Remove Unneed Media File
    print(" > 4. Removing Unneed Files")
    remove_unneed_media_files(root_dir=root_dir, rule=REMOVE_MEDIA_RULE_ORAJA)
    # Soft syncing
    print(f" > 5. Syncing dir files from {sync_dir} to {root_dir}")
    sync_folder(src_dir=root_dir, dst_dir=sync_dir, preset=SYNC_PRESET_FOR_APPEND)
    # Remove Empty folder
    print(f" > 6. Remove empty folder in {root_dir}")
    remove_empty_folder(parent_dir=root_dir)


OPTIONS = [
    Option(
        func=pack_setup_rawpack_to_hq,
        name="大包生成脚本：原包 -> HQ版大包",
        inputs=[
            Input(InputType.Path, "Pack Dir"),
            Input(InputType.Path, "Root Dir"),
        ],
    ),
    Option(
        func=pack_update_rawpack_to_hq,
        name="大包更新脚本：原包 -> HQ版大包",
        check_func=_pack_update_rawpack_to_hq_check,
        inputs=[
            Input(InputType.Path, "Pack Dir"),
            Input(InputType.Path, "Root Dir"),
            Input(InputType.Path, "Sync Dir"),
        ],
    ),
    Option(
        func=pack_raw_to_hq,
        name="BMS大包脚本：原包 -> HQ版大包",
        inputs=[
            Input(InputType.Path, "Root Dir"),
        ],
    ),
    Option(
        func=pack_hq_to_lq,
        name="BMS大包脚本：HQ版大包 -> LQ版大包",
        inputs=[
            Input(InputType.Path, "Root Dir"),
        ],
    ),
]
