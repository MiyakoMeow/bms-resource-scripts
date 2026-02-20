import multiprocessing
import subprocess
import time
from pathlib import Path

"""
Audio
"""


class AudioPreset:
    def __init__(self, exec: str, output_format: str, arg: str | None = None) -> None:
        self.exec = exec
        self.output_format = output_format
        self.arg = arg

    def __str__(self) -> str:
        return f"AudioPreset {{ exec: {self.exec}, output_format: {self.output_format} arg: {self.arg} }}"

    def __repr__(self) -> str:
        return self.__str__()


AUDIO_PRESET_OGG_Q10 = AudioPreset("oggenc", "ogg", "-q10")
AUDIO_PRESET_OGG_FFMPEG = AudioPreset("ffmpeg", "ogg", "")

AUDIO_PRESET_WAV_FFMPEG = AudioPreset("ffmpeg", "wav", None)
AUDIO_PRESET_WAV_FROM_FLAC = AudioPreset("flac", "wav", "-d --keep-foreign-metadata-if-present -f")

AUDIO_PRESET_FLAC = AudioPreset("flac", "flac", "--keep-foreign-metadata-if-present --best -f")
AUDIO_PRESET_FLAC_FFMPEG = AudioPreset("ffmpeg", "flac", "")

AUDIO_PRESETS = [
    AUDIO_PRESET_FLAC,
    AUDIO_PRESET_WAV_FROM_FLAC,
    AUDIO_PRESET_OGG_Q10,
    AUDIO_PRESET_FLAC_FFMPEG,
    AUDIO_PRESET_WAV_FFMPEG,
    AUDIO_PRESET_OGG_FFMPEG,
]


def _get_audio_precess_cmd(
    file_path: Path,
    output_file_path: Path,
    preset: AudioPreset,
) -> str:
    # Execute
    arg = preset.arg if preset.arg is not None else ""
    # 外部库 subprocess 要求字符串路径用于 shell 命令，需要显式转换
    file_path_str = str(file_path)
    output_file_path_str = str(output_file_path)
    if preset.exec == "ffmpeg":
        return (
            f'ffmpeg -hide_banner -loglevel panic -i "{file_path_str}" '
            f'-f {preset.output_format} -map_metadata 0 {arg} "{output_file_path_str}"'
        )
    elif preset.exec == "oggenc":
        return f'oggenc {arg} "{file_path_str}" -o "{output_file_path_str}"'
    elif preset.exec == "flac":
        return f'flac {arg} "{file_path_str}" -o "{output_file_path_str}"'
    else:
        return ""


def transfer_audio_by_format_in_dir(
    dir: Path,
    input_exts: list[str],
    presets: list[AudioPreset],
    remove_origin_file_when_success: bool = True,
    remove_origin_file_when_failed: bool = False,
    remove_existing_target_file: bool = True,
) -> bool:
    """
    Example:
    wav flac flac
    wav ogg ogg -ab 320k
    """

    def check_input_file(dir: Path, file_name: str, input_exts: list[str]) -> Path | None:
        file_path = dir / file_name
        if not file_path.is_file():
            return None
        # Check ext
        ext_found: str | None = None
        for ext in input_exts:
            if file_path.suffix.lower() == "." + ext:
                ext_found = ext
        if ext_found is None:
            return None
        return dir / file_name

    def spawn_parse_audio_process(
        file_path: Path, preset_index: int, preset: AudioPreset
    ) -> tuple[tuple[Path, int], subprocess.Popen | None]:
        # New cmd
        output_file_path = file_path.parent / (file_path.stem + "." + preset.output_format)
        # Target File exists?
        if output_file_path.is_file():
            if output_file_path.stat().st_size > 0 and not remove_existing_target_file:
                print(f" - File {output_file_path} exists! Skipping...")
                return (file_path, preset_index), None
            else:
                print(f" - Remove existing file: {output_file_path}")
                output_file_path.unlink()
        # Run cmd
        cmd = _get_audio_precess_cmd(
            file_path,
            output_file_path,
            preset,
        )
        if len(cmd) == 0:
            return (file_path, preset_index), None
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return (file_path, preset_index), process

    has_error = False
    err_file_path = ""
    err_stdout = b""
    err_stderr = b""

    # 创建线程池
    hdd = dir.drive.upper() != "C:"
    max_workers = min(multiprocessing.cpu_count(), 24) if hdd else multiprocessing.cpu_count()

    # Submit
    processes: list[tuple[tuple[Path, int], subprocess.Popen | None]] = []
    task_args: list[tuple[Path, int, AudioPreset]] = [
        (dir / file_name, 0, presets[0])
        for file_name in [p.name for p in dir.iterdir()]
        if check_input_file(dir, file_name, input_exts) is not None
    ]

    if len(task_args) > 0:
        print("Entering dir:", dir, "Input ext:", input_exts)
        print("Preset:", presets)

    # Count
    file_count = len(task_args)
    fallback_file_names: list[tuple[str, int]] = []

    for task_arg in task_args:
        if len(processes) >= max_workers:
            break
        processes.append(spawn_parse_audio_process(*task_arg))
    task_args = task_args[len(processes) :]

    # 等待所有任务完成
    while len(processes) > 0:
        new_processes: list[tuple[tuple[Path, int], subprocess.Popen | None]] = []

        # 检查进程状态
        switch_next_list: list[tuple[Path, int]] = []
        for process_tuple in processes:
            (file_path, preset_index), process = process_tuple
            # Switch Next?
            switch_next = False
            if process is None:
                # Empty process
                switch_next = True
            else:
                process_returncode = process.poll()
                if process_returncode is None:
                    # Running
                    new_processes.append(((file_path, preset_index), process))
                elif process_returncode == 0:
                    # Succcess
                    if remove_origin_file_when_success and file_path.is_file():
                        try:
                            file_path.unlink()
                        except PermissionError:
                            print(f" -> PermissionError When Deleting: {file_path}")
                else:
                    # Failed
                    switch_next = True
                    err_stdout, err_stderr = process.communicate()

            if switch_next:
                switch_next_list.append((file_path, preset_index))

        # 切换下个预设
        for file_path, preset_index in switch_next_list:
            new_preset_index = preset_index + 1
            if new_preset_index not in range(0, len(presets)):
                # Last, Return
                has_error = True
                # Remove Origin files
                if remove_origin_file_when_failed and file_path.is_file():
                    try:
                        file_path.unlink()
                    except PermissionError:
                        print(f" -> PermissionError When Deleting: {file_path}")
                continue
            # Count
            fallback_file_names.append((file_path.name, new_preset_index))
            # Try Next
            task_args.append((file_path, new_preset_index, presets[new_preset_index]))

        # 启动新进程
        running_count_delta = 0
        for task_arg in task_args:
            if len(new_processes) >= max_workers:
                break
            new_processes.append(spawn_parse_audio_process(*task_arg))
            running_count_delta += 1
        task_args = task_args[running_count_delta:]

        processes = new_processes

        # 休眠一阵子
        time.sleep(0.001)

    if has_error:
        print("Has Error!")
        print("- Err file_path: ", err_file_path)
        print("- Err stdout: ", err_stdout)
        print("- Err stderr: ", err_stderr)
        if remove_origin_file_when_failed:
            print(" ! The failed origin file has been removed.")

    if file_count > 0:
        print(f" -v- Parsed {file_count} file(s).")
    if len(fallback_file_names) > 0:
        print(f" x_x Fallback: {fallback_file_names}. Totally {len(fallback_file_names)} files.")

    return not has_error


MODES: list[tuple[str, list[str], list[AudioPreset]]] = [
    (
        "Convert: WAV to FLAC",
        ["wav"],
        [
            AUDIO_PRESET_FLAC,
            AUDIO_PRESET_FLAC_FFMPEG,
        ],
    ),
    ("Compress: FLAC to OGG Q10", ["flac"], [AUDIO_PRESET_OGG_Q10]),
    ("Compress: WAV to OGG Q10", ["wav"], [AUDIO_PRESET_OGG_Q10]),
    (
        "Reverse: FLAC to WAV",
        ["flac"],
        [AUDIO_PRESET_WAV_FROM_FLAC, AUDIO_PRESET_WAV_FFMPEG],
    ),
]


def bms_folder_transfer_audio(
    root_dir: Path,
    input_ext: list[str] | None = None,
    transfer_mode: list[AudioPreset] | None = None,
    remove_origin_file_when_success: bool = True,
    remove_origin_file_when_failed: bool = True,
    skip_on_fail: bool = False,
) -> None:
    # Select Modes
    if transfer_mode is None:
        transfer_mode = []
    if input_ext is None:
        input_ext = []
    if len(transfer_mode) == 0 or len(input_ext) == 0:
        for i, (mode_str, mode_input_exts, mode_presets) in enumerate(MODES):
            print(f"- {i}: {mode_str} ({mode_input_exts}) ({mode_presets})")
        selection = int(input("Select Mode (Type numbers above):"))
        input_ext = MODES[selection][1]
        transfer_mode = MODES[selection][2]

    for bms_dir_name in [p.name for p in root_dir.iterdir()]:
        bms_dir_path = root_dir / bms_dir_name
        if not bms_dir_path.is_dir():
            continue
        is_success = transfer_audio_by_format_in_dir(
            bms_dir_path,
            input_ext,
            transfer_mode,
            remove_origin_file_when_success=remove_origin_file_when_success,
            remove_origin_file_when_failed=remove_origin_file_when_failed,
        )
        if not is_success:
            print(" - Dir:", bms_dir_path, "Error occured!")
            if skip_on_fail:
                break
