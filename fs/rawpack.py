import multiprocessing
import os
import shutil
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import py7zr
import rarfile  # type: ignore[import-untyped]

from bms import CHART_FILE_EXTS
from fs.move import move_elements_across_dir


def _safe_join(base_dir: str, relative_path: str) -> str:
    # Normalize separators to OS style first
    rel = relative_path.replace("/", os.sep).replace("\\", os.sep)
    # Remove drive letters and leading path separators to avoid traversal / drive jump
    rel = rel.lstrip("/\\")
    # Compose and normalize
    candidate = os.path.normpath(os.path.join(base_dir, rel))
    base_dir_norm = os.path.normpath(base_dir)
    # Ensure candidate is under base_dir (path-aware)
    abs_candidate = os.path.abspath(candidate)
    abs_base = os.path.abspath(base_dir_norm)
    try:
        common = os.path.commonpath([abs_candidate, abs_base])
    except ValueError:
        # Different drives or invalid path -> unsafe
        raise ValueError(f"Unsafe path detected: {relative_path}") from None
    if common != abs_base:
        raise ValueError(f"Unsafe path detected: {relative_path}")
    return candidate


def _set_mtime(target_path: str, date_time_tuple: tuple[int, int, int, int, int, int]) -> None:
    # date_time_tuple: (Y, M, D, H, M, S)
    d_gettime = (
        f"{date_time_tuple[0]}/{date_time_tuple[1]}/{date_time_tuple[2]} {date_time_tuple[3]}:{date_time_tuple[4]}"
    )
    d_timearry = time.mktime(time.strptime(d_gettime, "%Y/%m/%d %H:%M"))
    try:
        os.utime(target_path, (d_timearry, d_timearry))
    except FileNotFoundError:
        pass


def _try_decode_cp932_from_cp437(name: str) -> str | None:
    try:
        raw = name.encode("cp437", "strict")
        return raw.decode("cp932", "strict")
    except Exception:
        return None


def unzip_zip_file_to_cache_dir(file_path: str, cache_dir_path: str) -> None:
    print(f"Extracting {file_path} to {cache_dir_path} (zip)")
    zf = zipfile.ZipFile(file_path)
    infos = zf.infolist()

    # 先判断是否需要 cp932 解码（仅对非 UTF-8 条目）
    non_utf8_infos = [i for i in infos if (i.flag_bits & 0x800) == 0]
    use_cp932 = False
    for i in non_utf8_infos:
        sjis = _try_decode_cp932_from_cp437(i.filename)
        if sjis is None:
            continue
        # 粗略判断是否包含常见日文/中日韩字符
        if any(("\u3040" <= ch <= "\u30ff") or ("\u3400" <= ch <= "\u9fff") for ch in sjis):
            use_cp932 = True
            break

    # Name 解码函数
    def decode_name(info: zipfile.ZipInfo) -> str:
        if (info.flag_bits & 0x800) != 0:
            return info.filename
        if use_cp932:
            sjis = _try_decode_cp932_from_cp437(info.filename)
            if sjis is not None:
                return sjis
        return info.filename

    # 单条目任务：重新打开 zip 以避免多线程共享句柄
    def extract_one(member_name: str) -> None:
        with zipfile.ZipFile(file_path) as z2:
            info = next(i for i in z2.infolist() if i.filename == member_name)
            rel_name = decode_name(info)
            out_path = _safe_join(cache_dir_path, rel_name)
            if info.is_dir() or rel_name.endswith("/"):
                os.makedirs(out_path, exist_ok=True)
                _set_mtime(out_path, info.date_time)
                return
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with z2.open(info) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
            _set_mtime(out_path, info.date_time)

    max_workers = multiprocessing.cpu_count()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(extract_one, i.filename) for i in infos]
        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f" !_! Extract error: {e}")
    zf.close()


def unzip_7z_file_to_cache_dir(file_path: str, cache_dir_path: str) -> None:
    print(f"Extracting {file_path} to {cache_dir_path} (7z)")
    sevenzip_file = py7zr.SevenZipFile(file_path)
    sevenzip_file.extractall(cache_dir_path)
    sevenzip_file.close()


def unzip_rar_file_to_cache_dir(file_path: str, cache_dir_path: str) -> None:
    print(f"Extracting {file_path} to {cache_dir_path} (RAR)")
    rar_file = rarfile.RarFile(file_path)
    rar_file.extractall(cache_dir_path)
    rar_file.close()


def unzip_file_to_cache_dir(file_path: str, cache_dir_path: str) -> None:
    file_name = os.path.split(file_path)[-1]
    if file_path.endswith(".zip"):
        unzip_zip_file_to_cache_dir(file_path, cache_dir_path)
    elif file_path.endswith(".7z"):
        unzip_7z_file_to_cache_dir(file_path, cache_dir_path)
    elif file_path.endswith(".rar"):
        unzip_rar_file_to_cache_dir(file_path, cache_dir_path)
    else:
        target_file_path = os.path.join(cache_dir_path, "".join(file_name.split(" ")[1:]))
        print(f"Coping {file_path} to {target_file_path}")
        shutil.copy(file_path, target_file_path)


def get_num_set_file_names(pack_dir: str) -> list[str]:
    file_id_names: list[str] = []
    for file_name in os.listdir(pack_dir):
        file_path = os.path.join(pack_dir, file_name)
        if not os.path.isfile(file_path):
            continue
        id_str = file_name.split(" ")[0]
        if not id_str.isdigit():
            continue
        file_id_names.append(file_name)
    return file_id_names


def move_out_files_in_folder_in_cache_dir(cache_dir_path: str) -> bool:
    cache_folder_count = 0
    cache_file_count = 0
    inner_dir_name = None
    file_ext_count: dict[str, list[str]] = {}
    done = False
    error = False
    while True:
        file_ext_count = {}
        cache_folder_count = 0
        cache_file_count = 0
        inner_dir_name = None
        for cache_name in os.listdir(cache_dir_path):
            cache_path = os.path.join(cache_dir_path, cache_name)
            if os.path.isdir(cache_path):
                # Remove __MACOSX dir
                if cache_name == "__MACOSX":
                    shutil.rmtree(cache_path)
                    continue
                # Normal dir
                cache_folder_count += 1
                inner_dir_name = cache_name
            if os.path.isfile(cache_path):
                cache_file_count += 1
                # Count ext
                file_ext = cache_name.rsplit(".")[-1]
                if file_ext_count.get(file_ext) is None:
                    file_ext_count.update({file_ext: [cache_name]})
                else:
                    file_ext_count[file_ext].append(cache_name)

        if cache_folder_count == 0:
            done = True

        if cache_folder_count == 1 and cache_file_count >= 10:
            done = True

        if cache_folder_count > 1:
            # If there are .bms chart files anywhere in cache_dir, do not error
            has_bms = False
            for _root, _dirs, _files in os.walk(cache_dir_path):
                for _fname in _files:
                    if _fname.lower().endswith(CHART_FILE_EXTS):
                        has_bms = True
                        break
                if has_bms:
                    break
            if has_bms:
                # Consider this state acceptable and stop further moving
                done = True
            else:
                print(f" !_! {cache_dir_path}: has more then 1 folders, please do it manually.")
                error = True

        if done or error:
            break

        # move out files
        if inner_dir_name is not None:
            inner_dir_path = os.path.join(cache_dir_path, inner_dir_name)
            # Avoid two floor same name
            inner_inner_dir_path = os.path.join(inner_dir_path, inner_dir_name)
            if os.path.isdir(inner_inner_dir_path):
                print(f" - Renaming inner inner dir name: {inner_inner_dir_path}")
                shutil.move(inner_inner_dir_path, f"{inner_inner_dir_path}-rep")
            # Move
            print(f" - Moving inner files in {inner_dir_path} to {cache_dir_path}")
            move_elements_across_dir(inner_dir_path, cache_dir_path)
            try:
                os.rmdir(inner_dir_path)
            except FileNotFoundError:
                pass

    if error:
        return False

    if cache_folder_count == 0 and cache_file_count == 0:
        print(f" !_! {cache_dir_path}: Cache is Empty!")
        os.rmdir(cache_dir_path)
        return False

    # Has More Than 1 mp4?!
    mp4_count = file_ext_count.get("mp4")
    if mp4_count is not None and len(mp4_count) > 1:
        print(f" - Tips: {cache_dir_path} has more than 1 mp4 files!", mp4_count)

    return True
