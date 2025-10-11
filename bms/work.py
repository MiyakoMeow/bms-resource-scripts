from collections import defaultdict


def extract_work_name(
    titles: list[str],
    remove_unclosed_pair: bool = True,
    remove_tailing_sign_list: list[str] = None,
) -> str:
    """
    从多个BMS文件标题中提取共同的作品名（改进版）

    :param titles: 包含多个BMS标题的列表
    :return: 提取出的共同作品名（经过后处理）
    """
    # 统计所有可能前缀的出现次数
    if remove_tailing_sign_list is None:
        remove_tailing_sign_list = []
    prefix_counts = defaultdict(int)
    for title in titles:
        for i in range(1, len(title) + 1):
            prefix = title[:i]
            prefix_counts[prefix] += 1

    if not prefix_counts:
        return ""

    max_count = max(prefix_counts.values())

    candidates = [
        (prefix, count)
        for prefix, count in prefix_counts.items()
        if count >= max_count * 0.67  # 超过2/3就可以算上
    ]

    # 排序规则：优先长度降序，其次次数降序，最后字典序升序
    candidates.sort(key=lambda x: (-len(x[0]), -x[1], x[0]))

    # 提取最优候选
    best_candidate = candidates[0][0] if candidates else ""

    # 后处理：移除未闭合括号及其后续内容
    return _extract_work_name_post_process(
        best_candidate,
        remove_unclosed_pair=remove_unclosed_pair,
        remove_tailing_sign_list=remove_tailing_sign_list,
    )


def _extract_work_name_post_process(
    s: str,
    remove_unclosed_pair: bool = True,
    remove_tailing_sign_list: list[str] = None,
) -> str:
    """
    后处理函数：移除未闭合括号及其后续内容

    :param s: 原始字符串
    :return: 处理后的字符串
    """

    # 清除前后空格
    if remove_tailing_sign_list is None:
        remove_tailing_sign_list = []
    s = s.strip()

    while True:
        triggered = False
        if remove_unclosed_pair:
            stack: list[tuple[str, int]] = []

            # 遍历字符串记录括号状态
            pairs = [
                ("(", ")"),
                ("[", "]"),
                ("{", "}"),
                ("（", "）"),
                ("［", "］"),
                ("｛", "｝"),
                ("【", "】"),
            ]
            for i, c in enumerate(s):
                for p_open, p_close in pairs:
                    if c == p_open:
                        stack.append((c, i))  # 记录括号类型和位置
                    if c == p_close and stack and stack[-1][0] == p_open:
                        stack.pop()

            # 如果存在未闭合括号
            if stack:
                last_unmatched_pos = stack[-1][1]
                s = s[:last_unmatched_pos].rstrip()  # 截断并移除末尾空格
                triggered = True

        for sign in remove_tailing_sign_list:
            if s.endswith(sign):
                s = s[: -len(sign)].rstrip()
                triggered = True
        # 没触发？
        if not triggered:
            break

    return s
