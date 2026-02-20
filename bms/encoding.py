import codecs
from pathlib import Path

ENCODINGS = [
    "shift-jis",
    "shift-jis-2004",
    "gb2312",
    "utf-8",
    "gb18030",
    "shift-jisx0213",
]

BOFTT_ID_SPECIFIC_ENCODING_TABLE: dict[str, str] = {
    "134": "utf-8",
    "191": "gbk",
    "435": "gbk",
    "439": "gbk",
    # 159 bms文件本身有编码问题
}


class PriorityDecoder:
    def __init__(self, encoding_priority: list[str], final: str = "utf-8"):
        """
        初始化优先级解码器

        Args:
            encoding_priority (List[str]): 编码优先级列表，靠前的编码优先级更高
        """
        self.encoding_priority = encoding_priority
        # 预加载所有编码的编解码器
        self.codecs = {enc: codecs.lookup(enc) for enc in encoding_priority}
        # TODO: Impl Final
        self.final = final

    def _decode_byte_sequence(self, byte_data: bytes, start: int = 0) -> tuple[str | None, int]:
        """
        尝试用所有编码解码字节序列，返回第一个成功的解码结果和消耗的字节数

        Args:
            byte_data (bytes): 要解码的字节数据
            start (int): 开始解码的位置

        Returns:
            Tuple[Optional[str], int]: (解码后的字符, 消耗的字节数)
        """
        for enc in self.encoding_priority:
            codec = self.codecs[enc]
            try:
                # 尝试解码1-4个字节（日文编码通常不超过4字节）
                for length in range(1, min(5, len(byte_data) - start + 1)):
                    try:
                        char = codec.decode(byte_data[start : start + length])[0]
                        return char, length
                    except UnicodeDecodeError:
                        continue
            except (UnicodeDecodeError, LookupError):
                continue
        return None, 1  # 所有编码都失败，默认消耗1个字节

    def decode(self, byte_data: bytes, errors: str = "strict") -> str:
        """
        按照编码优先级逐字符解码字节数据

        Args:
            byte_data (bytes): 要解码的字节数据
            errors (str): 错误处理方式 ('strict', 'ignore', 'replace')

        Returns:
            str: 解码后的字符串
        """
        result = []
        position = 0
        total_length = len(byte_data)

        while position < total_length:
            char, consumed = self._decode_byte_sequence(byte_data, position)

            if char is not None:
                result.append(char)
            else:
                # 处理解码失败的字节
                if errors == "strict":
                    msg = f"无法用任何编码解码字节: {byte_data[position : position + 1]!r}"
                    raise UnicodeDecodeError(
                        "priority_decode",
                        byte_data,
                        position,
                        position + 1,
                        msg,
                    )
                elif errors == "replace":
                    result.append("�")
                # ignore模式不做任何操作

            position += consumed

        return "".join(result)


def read_file_with_priority(file_path: Path, encoding_priority: list[str], errors: str = "strict") -> str | None:
    """
    读取文件并按照编码优先级逐字符解码

    Args:
        file_path (Path): 文件路径
        encoding_priority (List[str]): 编码优先级列表
        errors (str): 错误处理方式

    Returns:
        Optional[str]: 解码后的内容，失败返回None
    """
    try:
        with file_path.open("rb") as f:
            byte_data = f.read()
            decoder = PriorityDecoder(encoding_priority)
            return decoder.decode(byte_data, errors)
    except (OSError, UnicodeDecodeError) as e:
        print(f"Error: {e}")
        return None


def get_bms_file_str(file_bytes: bytes, encoding: str | None = None) -> str:
    file_str = ""
    encoding_priority = ENCODINGS
    if encoding:
        encoding_priority.insert(0, encoding)
    decoder = PriorityDecoder(encoding_priority)
    try:
        file_str = decoder.decode(file_bytes, errors="strict")
    except UnicodeDecodeError:
        file_str = file_bytes.decode("utf-8", errors="ignore")

    return file_str


# 解码器测试
if __name__ == "__main__":
    # 测试数据
    # "こんにちは" + "①" (shift-jis不支持的字符)
    test_bytes = b"\x82\xb1\x82\xf1\x82\xc9\x82\xbf\x82\xcd\x87\x40"

    # 编码优先级
    # encodings = ["shift_jis", "shift_jis_2004", "euc-jp"]
    encodings = ["shift_jis", "shift_jis_2004", "euc-jp"]

    # 创建解码器
    decoder = PriorityDecoder(encodings)

    # 测试解码
    print("== strict模式 ==")
    try:
        result = decoder.decode(test_bytes)
        print(f"解码结果: {result}")
    except UnicodeDecodeError as e:
        print(f"解码失败: {e}")

    print("\n== replace模式 ==")
    result = decoder.decode(test_bytes, errors="replace")
    print(f"解码结果: {result}")  # 会显示"こんにちは�"

    print("\n== ignore模式 ==")
    result = decoder.decode(test_bytes, errors="ignore")
    print(f"解码结果: {result}")  # 会显示"こんにちは"
