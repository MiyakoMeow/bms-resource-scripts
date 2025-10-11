import os

from fs import bms_dir_similarity
from fs.move import REPLACE_OPTION_UPDATE_PACK, move_elements_across_dir


def main() -> None:
    src_dir = input("Input the src dir:")
    if src_dir.startswith('"') and src_dir.endswith('"'):
        src_dir = src_dir[1:-1]
    if not os.path.isdir(src_dir):
        print(f"{src_dir}: not a dir.")
        return
    dirs = [
        dir for dir in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, dir))
    ]
    # 扫描所有带aery的目录
    aery_pair: list[tuple[str, str, float]] = []
    for dir in dirs:
        if dir.find("Aery") == -1 and dir.find("AERY") == -1:
            continue
        # 源目录
        dir_path = os.path.join(src_dir, dir)
        for i in range(len(dir)):
            # 按长度寻找，排除自身，确认只剩下一个结果
            sub_len = i + 1
            scan_dirs = [
                sub_dir
                for sub_dir in dirs
                if sub_dir.startswith(dir[:sub_len]) and sub_dir != dir
            ]
            if len(scan_dirs) != 1:
                continue
            scan_dir = scan_dirs[0]
            # 目标路径
            scan_dir_path = os.path.join(src_dir, scan_dir)
            # 参数
            similarity = bms_dir_similarity(dir_path, scan_dir_path)
            aery_pair.append((dir_path, scan_dir_path, similarity))
            break
    # 打印待移动的部分
    for p in aery_pair:
        print(p)

    similarity_border = 0.95
    confirm = input(f"Confirm? (border: {similarity_border}) [y/N]")
    if not confirm.lower().startswith("y"):
        return

    for p in aery_pair:
        p_from: str = p[0]
        p_to: str = p[1]
        p_similarity: float = p[2]
        if p_similarity < similarity_border:
            continue
        print(f"Moving: {p_from} => {p_to}, similarity: {p_similarity}")
        move_elements_across_dir(
            p_from,
            p_to,
            replace_options=REPLACE_OPTION_UPDATE_PACK,
        )


if __name__ == "__main__":
    main()
