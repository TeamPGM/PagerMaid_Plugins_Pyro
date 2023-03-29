# pyright: basic

# Solution is adapted from https://github.com/hustcc/xmorse.

from pagermaid.enums import Message
from pagermaid.listener import listener

MORSE_DICT = {
    "A": "01",
    "B": "1000",
    "C": "1010",
    "D": "100",
    "E": "0",
    "F": "0010",
    "G": "110",
    "H": "0000",
    "I": "00",
    "J": "0111",
    "K": "101",
    "L": "0100",
    "M": "11",
    "N": "10",
    "O": "111",
    "P": "0110",
    "Q": "1101",
    "R": "010",
    "S": "000",
    "T": "1",
    "U": "001",
    "V": "0001",
    "W": "011",
    "X": "1001",
    "Y": "1011",
    "Z": "1100",
    "0": "11111",
    "1": "01111",
    "2": "00111",
    "3": "00011",
    "4": "00001",
    "5": "00000",
    "6": "10000",
    "7": "11000",
    "8": "11100",
    "9": "11110",
    ".": "010101",
    ",": "110011",
    "?": "001100",
    "'": "011110",
    "!": "101011",
    "/": "10010",
    "(": "10110",
    ")": "101101",
    "&": "01000",
    ":": "111000",
    ";": "101010",
    "=": "10001",
    "+": "01010",
    "-": "100001",
    "_": "001101",
    '"': "010010",
    "$": "0001001",
    "@": "011010",
}

REVERSED_MORSE_DICT = {v: k for k, v in MORSE_DICT.items()}

MORSE_SHORTS = ["."]
MORSE_LONGS = ["-", "_"]
MORSE_SPLITTERS = [" ", "/"]


def encode(text: str) -> str:
    return MORSE_SPLITTERS[0].join(
        (MORSE_DICT.get(char.strip().upper()) or bin((ord(char)))[2:])
        .replace("0", MORSE_SHORTS[0])
        .replace("1", MORSE_LONGS[0])
        for char in text
    )


def decode(morse: str) -> str:
    assert set(morse) <= frozenset(MORSE_SHORTS + MORSE_LONGS + MORSE_SPLITTERS)
    return "".join(
        REVERSED_MORSE_DICT.get(word) or chr(int(word, 2))
        for word in "".join(
            (
                " " if char in MORSE_SPLITTERS else str(int(char in MORSE_LONGS))
                for char in morse
            )
        ).split(" ")
    )


@listener(command="enmorse", description="转换指定文本到摩斯密码", parameters="[待转换文本] (支持回复消息)")
async def enmorse(message: Message):
    text = (message.reply_to_message or message).text
    if text:
        try:
            result = encode(text)
        except Exception:
            result = "呜呜呜 ~ 转换失败了，可能含有非法字符。"
    else:
        result = "请输入参数"
    await message.edit(f"`{result}`")


@listener(command="demorse", description="转换摩斯密码到明文", parameters="[摩斯密码] (支持回复消息)")
async def demorse(message: Message):
    text = (message.reply_to_message or message).text
    if text:
        try:
            result = decode(text)
        except Exception:
            result = "呜呜呜 ~ 转换失败了，可能含有非法字符。"
    else:
        result = "请输入参数"
    await message.edit(f"`{result}`")
