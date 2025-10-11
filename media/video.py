import copy
import json
import os
import subprocess
from typing import Any

"""
Media
"""


def get_media_file_probe(file_path: str) -> dict[Any, Any]:
    cmd = (
        f'ffprobe -show_format -show_streams -print_format json -v quiet "{file_path}"'
    )
    print(f"Exec: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        text=True,
    )
    out = result.stdout
    return json.loads(out)


"""
Video Info
"""


class VideoInfo:
    def __init__(self, width: int, height: int, bit_rate: int) -> None:
        self.width = width
        self.height = height
        self.bit_rate = bit_rate


def get_video_info(file_path: str) -> VideoInfo | None:
    probe = get_media_file_probe(file_path)
    for stream in probe["streams"]:
        stream: dict[Any, Any] = stream
        if stream["codec_type"] != "video":
            continue
        return VideoInfo(
            int(stream["width"]),
            int(stream["height"]),
            int(stream["bit_rate"]),
        )

    return None


def get_video_size(file_path: str) -> tuple[int, int] | None:
    probe = get_media_file_probe(file_path)
    for stream in probe["streams"]:
        stream: dict[Any, Any] = stream
        if stream["codec_type"] != "video":
            continue
        return (
            int(stream["width"]),
            int(stream["height"]),
        )

    return None


"""
Video
"""


class VideoPreset:
    def __init__(
        self,
        exec: str,
        input_arg: str | None,
        fliter_arg: str | None,
        output_file_ext: str,
        output_codec: str,
        arg: str | None = None,
    ) -> None:
        self.exec = exec
        self.input_arg = input_arg
        self.fliter_arg = fliter_arg
        self.output_file_ext = output_file_ext
        self.output_codec = output_codec
        self.arg = arg

    def __str__(self) -> str:
        return (
            f"VideoPreset {{ exec: {self.exec}, output_format: {self.output_codec} }}"
        )

    def __repr__(self) -> str:
        return self.__str__()

    def get_output_file_path(self, input_file_path: str) -> str:
        return (
            input_file_path[: -len(input_file_path.rsplit(".", 1)[-1])]
            + self.output_file_ext
        )

    def get_video_process_cmd(self, input_file_path: str, output_file_path: str) -> str:
        input_arg = self.input_arg if self.input_arg is not None else ""
        fliter_arg = self.fliter_arg if self.fliter_arg is not None else ""
        inner_arg = "-map_metadata 0" if self.exec == "ffmpeg" else ""
        return f'{self.exec} {input_arg} "{input_file_path}" {fliter_arg} {inner_arg} -c:v {self.output_codec} {self.arg} "{output_file_path}" '


FLITER_512X512 = '-filter_complex "[0:v]scale=512:512:force_original_aspect_ratio=increase,crop=512:512:(ow-iw)/2:(oh-ih)/2,boxblur=20[v1];[0:v]scale=512:512:force_original_aspect_ratio=decrease[v2];[v1][v2]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[vid]" -map [vid]'
FLITER_480P = '-filter_complex "[0:v]scale=640:480:force_original_aspect_ratio=increase,crop=640:480:(ow-iw)/2:(oh-ih)/2,boxblur=20[v1];[0:v]scale=640:480:force_original_aspect_ratio=decrease[v2];[v1][v2]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2[vid]" -map [vid]'

VIDEO_PRESET_AVI_512X512 = VideoPreset(
    "ffmpeg", "-hide_banner -i", FLITER_512X512, "avi", "mpeg4", "-an -q:v 8"
)
VIDEO_PRESET_WMV2_512X512 = VideoPreset(
    "ffmpeg", "-hide_banner -i", FLITER_512X512, "wmv", "wmv2", "-an -q:v 8"
)
VIDEO_PRESET_MPEG1VIDEO_512X512 = VideoPreset(
    "ffmpeg", "-hide_banner -i", FLITER_512X512, "mpg", "mpeg1video", "-an -b:v 1500k"
)
VIDEO_PRESET_AVI_480P = VideoPreset(
    "ffmpeg", "-hide_banner -i", FLITER_480P, "avi", "mpeg4", "-an -q:v 8"
)
VIDEO_PRESET_WMV2_480P = VideoPreset(
    "ffmpeg", "-hide_banner -i", FLITER_480P, "wmv", "wmv2", "-an -q:v 8"
)
VIDEO_PRESET_MPEG1VIDEO_480P = VideoPreset(
    "ffmpeg", "-hide_banner -i", FLITER_480P, "mpg", "mpeg1video", "-an -b:v 1500k"
)

VIDEO_PRESETS = [
    VIDEO_PRESET_AVI_512X512,
    VIDEO_PRESET_WMV2_512X512,
    VIDEO_PRESET_MPEG1VIDEO_512X512,
    VIDEO_PRESET_AVI_480P,
    VIDEO_PRESET_WMV2_480P,
    VIDEO_PRESET_MPEG1VIDEO_480P,
]


def get_prefered_preset_list(file_path: str) -> list[VideoPreset]:
    video_size = get_video_size(file_path)
    if video_size is None:
        return []
    width, height = video_size
    if width / height > 640 / 480:
        return [
            VIDEO_PRESET_MPEG1VIDEO_480P,
            VIDEO_PRESET_WMV2_480P,
            VIDEO_PRESET_AVI_480P,
        ]
    else:
        return [
            VIDEO_PRESET_MPEG1VIDEO_512X512,
            VIDEO_PRESET_WMV2_512X512,
            VIDEO_PRESET_AVI_512X512,
        ]


def process_video_in_dir(
    dir: str,
    input_exts: list[str] = None,
    presets: list[VideoPreset] = None,
    remove_origin_file: bool = True,
    remove_existing_target_file: bool = True,
    use_prefered: bool = False,
) -> bool:
    if presets is None:
        presets = [
            VIDEO_PRESET_MPEG1VIDEO_512X512,
            VIDEO_PRESET_WMV2_512X512,
            VIDEO_PRESET_AVI_512X512,
        ]
    if input_exts is None:
        input_exts = ["mp4", "avi"]
    has_error = False
    file_name_list: list[str] = []
    for file_name in os.listdir(dir):
        file_path = os.path.join(dir, file_name)
        if not os.path.isfile(file_path):
            continue
        # Check ext
        ext_checked = False
        for ext in input_exts:
            if file_name.lower().endswith("." + ext):
                ext_checked = True
        if not ext_checked:
            continue
        # Add File
        file_name_list.append(file_name)

    if len(file_name_list) > 0:
        print("Entering dir:", dir)

    for file_name in file_name_list:
        file_path = os.path.join(dir, file_name)
        # Get prefered
        presets_for_file = copy.deepcopy(presets)
        if use_prefered:
            presets_new = get_prefered_preset_list(file_path)
            presets_new.extend(presets_for_file)
            presets_for_file = presets_new
        # Check With Presets:
        for preset in presets_for_file:
            output_file_path = preset.get_output_file_path(file_path)
            if file_path == output_file_path:
                # This file is the preset's output.
                break
            if os.path.isfile(output_file_path):
                if remove_existing_target_file:
                    os.remove(output_file_path)
                else:
                    print(f"File exists: {output_file_path}")
                    continue
            # Process
            cmd = preset.get_video_process_cmd(file_path, output_file_path)
            print(f"Processing Video: {file_path} Preset: {preset}")
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode != 0:
                if os.path.isfile(output_file_path):
                    os.remove(output_file_path)
                if preset is presets[-1]:
                    print("Has Error!")
                    print("Cmd: ", cmd)
                    print("Stdout:", result.stdout)
                    print("Stderr:", result.stderr)
                    has_error = True
                    break
                continue

            # Normal End: Success
            if remove_origin_file and os.path.isfile(file_path):
                os.remove(file_path)
            # No need to exec next ctrl.
            break

    return not has_error


PRESETS: list[tuple[str, VideoPreset]] = [
    ("MP4 -> AVI 512x512", VIDEO_PRESET_AVI_512X512),
    ("MP4 -> AVI 480p", VIDEO_PRESET_AVI_480P),
    ("MP4 -> WMV2 512x512", VIDEO_PRESET_WMV2_512X512),
    ("MP4 -> WMV2 480p", VIDEO_PRESET_WMV2_480P),
    ("MP4 -> MPEG1VIDEO 512x512", VIDEO_PRESET_MPEG1VIDEO_512X512),
    ("MP4 -> MPEG1VIDEO 480p", VIDEO_PRESET_MPEG1VIDEO_480P),
]


def bms_folder_transfer_video(
    root_dir: str,
    input_exts: list[str] = None,
    presets: list[VideoPreset] = None,
    remove_origin_file: bool = True,
    remove_existing_target_file: bool = True,
    use_prefered: bool = False,
):
    if presets is None:
        presets = []
    if input_exts is None:
        input_exts = ["mp4"]
    if len(presets) == 0:
        for i, (mode_str, mode_args) in enumerate(PRESETS):
            print(f"- {i}: {mode_str} ({mode_args})")
        selection_str = input(
            "Select Modes (Type numbers above, split with space, then will exec in order):"
        )
        selections = selection_str.split()
        for selection in selections:
            presets.append(PRESETS[int(selection)][1])

    for bms_dir_name in os.listdir(root_dir):
        bms_dir_path = os.path.join(root_dir, bms_dir_name)
        if not os.path.isdir(bms_dir_path):
            continue

        is_success = process_video_in_dir(
            bms_dir_path,
            input_exts=input_exts,
            presets=presets,
            remove_origin_file=remove_origin_file,
            remove_existing_target_file=remove_existing_target_file,
            use_prefered=use_prefered,
        )
        if not is_success:
            print("Error occured!")
            break
