import hashlib
import os
import shutil
from enum import Enum


class SoftSyncExec(Enum):
    NONE = 0
    COPY = 1
    MOVE = 2

    def __str__(self) -> str:
        match self:
            case SoftSyncExec.NONE:
                return "无操作"
            case SoftSyncExec.COPY:
                return "使用复制命令"
            case SoftSyncExec.MOVE:
                return "使用移动命令"

    def __repr__(self) -> str:
        return self.__str__()


class SoftSyncPreset:
    def __init__(
        self,
        name: str = "本地文件同步预设",
        allow_src_exts: list[str] = None,
        disallow_src_exts: list[str] = None,
        allow_other_exts: bool = True,
        no_activate_ext_bound_pairs: list[tuple[list[str], list[str]]] = None,
        remove_dst_extra_files: bool = True,
        check_file_size: bool = True,
        check_file_mtime: bool = True,
        check_file_sha512: bool = False,
        remove_src_same_files: bool = False,
        exec: SoftSyncExec = SoftSyncExec.COPY,
    ) -> None:
        if no_activate_ext_bound_pairs is None:
            no_activate_ext_bound_pairs = []
        if disallow_src_exts is None:
            disallow_src_exts = []
        if allow_src_exts is None:
            allow_src_exts = []
        self.name = name
        self.allow_src_exts = allow_src_exts
        self.disallow_src_exts = disallow_src_exts
        self.allow_other_exts = allow_other_exts
        self.remove_dst_extra_files = remove_dst_extra_files
        self.no_activate_ext_bound_pairs = no_activate_ext_bound_pairs
        self.check_file_size = check_file_size
        self.check_file_mtime = check_file_mtime
        self.check_file_sha512 = check_file_sha512
        self.remove_src_same_files = remove_src_same_files
        self.exec = exec

    def __str__(self) -> str:
        ret = f"{self.name}："
        # Copy/Move
        ret += f"{self.exec}"
        ret += " "
        # Ext
        if self.allow_other_exts:
            ret += "允许同步未定义扩展名"
            ret += " "
        if len(self.allow_src_exts):
            ret += f"允许扩展名：{self.allow_src_exts}"
            ret += " "
        if len(self.disallow_src_exts):
            ret += f"拒绝扩展名：{self.disallow_src_exts}"
            ret += " "
        # Remove Src
        if self.remove_src_same_files:
            ret += "移除源中相对于目标，不需要同步的文件"
            ret += " "
        # Remove Dst
        if self.remove_dst_extra_files:
            ret += "移除目标文件夹相对源文件夹的多余文件"
            ret += " "
        # Check
        if self.check_file_mtime:
            ret += "检查修改时间"
            ret += " "
        if self.check_file_size:
            ret += "检查大小"
            ret += " "
        if self.check_file_sha512:
            ret += "检查SHA-512"
            ret += " "
        return ret


def get_file_sha512(file_path: str) -> str:
    if not os.path.isfile(file_path):
        # print(f"{file_path}：文件不存在。")
        return ""
    h = hashlib.sha512()
    with open(file_path, "rb") as f:
        b = f.read()
        h.update(b)
    ret = h.hexdigest()
    # print(f" - {file_path}: {ret}")
    return ret


SYNC_PRESET_DEFAULT = SoftSyncPreset()
SYNC_PRESET_FOR_APPEND = SoftSyncPreset(
    name="同步预设（用于更新包）",
    check_file_size=True,
    check_file_mtime=False,
    check_file_sha512=True,
    remove_src_same_files=True,
    remove_dst_extra_files=False,
    exec=SoftSyncExec.NONE,
)
SYNC_PRESET_FLAC = SoftSyncPreset(
    allow_src_exts=["flac"], allow_other_exts=False, remove_dst_extra_files=False
)
SYNC_PRESET_MP4_AVI = SoftSyncPreset(
    allow_src_exts=["mp4", "avi"], allow_other_exts=False, remove_dst_extra_files=False
)
SYNC_PRESET_CACHE = SoftSyncPreset(
    allow_src_exts=["mp4", "avi", "flac"],
    allow_other_exts=False,
    remove_dst_extra_files=False,
    exec=SoftSyncExec.NONE,
)

SYNC_PRESETS: list[SoftSyncPreset] = [
    SYNC_PRESET_DEFAULT,
    SYNC_PRESET_FOR_APPEND,
    SYNC_PRESET_FLAC,
    SYNC_PRESET_MP4_AVI,
    SYNC_PRESET_CACHE,
]


def sync_folder(
    src_dir: str,
    dst_dir: str,
    preset: SoftSyncPreset,
):
    src_list = os.listdir(src_dir)
    dst_list = os.listdir(dst_dir)

    # Cache For Print
    _src_copy_files: list[str] = []
    _src_move_files: list[str] = []
    _src_remove_files: list[str] = []
    _dst_remove_files: list[str] = []
    _dst_remove_dirs: list[str] = []

    # Src: Copy or Move or Remove
    for src_element in src_list:
        src_path = os.path.join(src_dir, src_element)
        dst_path = os.path.join(dst_dir, src_element)
        if os.path.isdir(src_path):
            # Src: Dir
            if os.path.isdir(dst_path):
                sync_folder(
                    src_path,
                    dst_path,
                    preset,
                )
            else:
                os.mkdir(dst_path)
                sync_folder(
                    src_path,
                    dst_path,
                    preset,
                )
        elif os.path.isfile(src_path):
            # Src: File
            # Check Ext
            ext_check_passed = preset.allow_other_exts
            ext = src_element.rsplit(".")[-1]
            if ext in preset.allow_src_exts:
                ext_check_passed = True
            if ext in preset.disallow_src_exts:
                ext_check_passed = False
            if not ext_check_passed:
                continue
            # Check Ext Bound
            ext_in_bound = False
            for (
                ext_bound_from_list,
                ext_bound_to_list,
            ) in preset.no_activate_ext_bound_pairs:
                if ext not in ext_bound_from_list:
                    continue
                # Found: Bound From
                for ext_bound_to in ext_bound_to_list:
                    bound_file_path = dst_path[: -len(ext)] + ext_bound_to
                    if not os.path.isfile(bound_file_path):
                        continue
                    # Found: Bound To
                    ext_in_bound = True
                    break
                if ext_in_bound:
                    break
            if ext_in_bound:
                continue
            # Replace: Check
            dst_file_exists = os.path.isfile(dst_path)
            is_same_file = dst_file_exists
            if preset.check_file_size and is_same_file and dst_file_exists:
                src_size = os.path.getsize(src_path)
                dst_size = os.path.getsize(dst_path)
                is_same_file = is_same_file and src_size == dst_size
            if preset.check_file_mtime and is_same_file and dst_file_exists:
                src_mtime = os.path.getmtime(src_path)
                dst_mtime = os.path.getmtime(dst_path)
                is_same_file = is_same_file and src_mtime == dst_mtime
            if preset.check_file_sha512 and is_same_file and dst_file_exists:
                src_value = get_file_sha512(src_path)
                dst_value = get_file_sha512(dst_path)
                is_same_file = is_same_file and src_value == dst_value
            # Replace: Exec
            if not dst_file_exists or not is_same_file:
                src_mtime = os.path.getmtime(src_path)
                match preset.exec:
                    case SoftSyncExec.NONE:
                        pass
                    case SoftSyncExec.COPY:
                        _src_copy_files.append(src_element)
                        shutil.copy(src_path, dst_path)
                        # Set atime/mtime
                        os.utime(dst_path, (src_mtime, src_mtime))
                    case SoftSyncExec.MOVE:
                        _src_move_files.append(src_element)
                        shutil.move(src_path, dst_path)
                        # Set atime/mtime
                        os.utime(dst_path, (src_mtime, src_mtime))
            # Remove same ori files
            if (
                preset.remove_src_same_files
                and dst_file_exists
                and is_same_file
                and os.path.isfile(src_path)
            ):
                _src_remove_files.append(src_element)
                os.remove(src_path)

    # Dst: Remove
    for dst_element in dst_list:
        if not preset.remove_dst_extra_files:
            break
        src_path = os.path.join(src_dir, dst_element)
        dst_path = os.path.join(dst_dir, dst_element)
        if os.path.isdir(dst_path):
            if os.path.isdir(src_path):
                pass
            else:
                _dst_remove_dirs.append(dst_element)
                shutil.rmtree(dst_path)
        elif os.path.isfile(dst_path):
            if not os.path.isfile(src_path):
                _dst_remove_files.append(dst_element)
                os.remove(dst_path)

    # Print
    if (
        len(_src_copy_files) > 0
        or len(_src_move_files) > 0
        or len(_src_remove_files) > 0
        or len(_dst_remove_files) > 0
        or len(_dst_remove_dirs) > 0
    ):
        print(f"{src_dir} -> {dst_dir}:")
        if len(_src_copy_files) > 0:
            print(f"Src copy: {_src_copy_files}")
        if len(_src_move_files) > 0:
            print(f"Src move: {_src_move_files}")
        if len(_src_remove_files) > 0:
            print(f"Src remove: {_src_remove_files}")
        if len(_dst_remove_files) > 0:
            print(f"Dst remove: {_dst_remove_files}")
        if len(_dst_remove_dirs) > 0:
            print(f"Dst remove dir: {_dst_remove_dirs}")
