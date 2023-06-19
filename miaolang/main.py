import base64
from dataclasses import dataclass
from typing import List, Optional

from pagermaid.enums import Message
from pagermaid.listener import listener

BASE64_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/="
SEP = "\u200b"
CODE = "\u200c\u200d"

PUNCTUATIONS = {
    0: (",", "，"),
    1: (",", "，"),
    2: (",", "，"),
    3: (",", "，"),
    7: (".", "。"),
    8: ("?", "？"),
    9: ("!", "！"),
    10: ("~", "～"),
}

_table: Optional[List[str]] = None


@dataclass(frozen=True)
class Options:
    calls: str = "喵"
    halfwidth_symbol: bool = False


def get_table() -> List[str]:
    global _table

    if _table:
        return _table

    count = len(BASE64_CHARS)
    code_len = len(CODE)
    table = []

    while (table_len := len(table)) < count:
        for i in range(code_len):
            c = CODE[i]
            if c not in table:
                if len(table) >= count:
                    break
                table.append(c)
            for j in range(table_len):
                if len(table) >= count:
                    break
                t = f"{c}{table[j]}"
                if t not in table:
                    table.append(t)

    return (_table := [SEP + item for item in table])


def add_punctuations(s: str, options: Optional[Options] = None) -> str:
    options = options or Options()
    a = list(s)
    i = (ord(a[0]) % 60) + 1

    while i < len(a):
        a[i] += options.calls
        puncs = PUNCTUATIONS.get(i % 32)
        a[i] += (puncs[0] if options.halfwidth_symbol else puncs[1]) if puncs else ""
        i += (ord(a[i][0]) % 60) + 1

    return f"{options.calls}{''.join(a)}{'.' if options.halfwidth_symbol else '。'}"


def add_calls(s: str, options: Optional[Options] = None) -> str:
    result = add_punctuations(s, options)
    return result


def to_miao(s: str, options: Optional[Options] = None) -> str:
    encoded = base64.b64encode(s.encode()).decode()
    table = get_table()
    chars = "".join(table[BASE64_CHARS.index(char)] for char in encoded)
    return add_calls(chars, options)


def clean(s: str) -> str:
    return "".join(char for char in s if char in (SEP + CODE))


def from_miao(s: str) -> str:
    s = clean(s)
    for i, sym in reversed(list(enumerate(get_table()))):
        s = s.replace(sym, BASE64_CHARS[i])
    return base64.b64decode(s.encode()).decode()


def is_miao(s: str) -> bool:
    return bool(s) and len(clean(s)) > 0


@listener(command="enmiao", description="转换指定文本到喵语", parameters="[待转换文本] (支持回复消息)")
async def enmiao_cmd(message: Message):
    if not (text := message.obtain_message()):
        return await message.edit("请输入参数")
    try:
        miao = to_miao(text)
    except Exception:
        return await message.edit("呜呜呜 ~ 转换失败了，可能含有非法字符。")
    await message.edit(f"`{miao}`")


@listener(command="demiao", description="转换喵语到明文", parameters="[喵语] (支持回复消息)")
async def demiao_cmd(message: Message):
    if not (miao := message.obtain_message()):
        return await message.edit("请输入参数")
    try:
        text = from_miao(miao)
    except Exception:
        return await message.edit("呜呜呜 ~ 转换失败了，可能含有非法字符。")
    await message.edit(f"`{text}`")
