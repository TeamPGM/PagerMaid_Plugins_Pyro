import re
import time

from pagermaid.listener import listener
from pagermaid.enums import Message


def time_to_unix(t: str) -> int:
    """将时间转换为Unix时间戳"""
    return int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))


def unix_to_time(t: int) -> str:
    """将Unix时间戳转换为时间"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(t)))


def match_datetime(text):
    """正则表达式提取文本所有日期+时间"""
    pattern = r"(\d{4}-\d{1,2}-\d{1,2}\s\d{1,2}:\d{1,2}:\d{1,2})"
    pattern = re.compile(pattern)
    return pattern.findall(text)


def format_time(t):
    if not t:
        t = time.time()
    try:
        t = int(t)
    except ValueError as e:
        if match := match_datetime(t):
            t = time_to_unix(match[0])
        else:
            raise ValueError from e
    return f"时间：`{unix_to_time(t)}`\n\n时间戳：`{t}`"


@listener(
    command="unixtime",
    description="Unix时间戳转换\n参数缺省将当前服务器时间转换为Unix时间戳\n时间格式: `YYYY-MM-DD HH:MM:SS`",
    parameters="[缺省 / 时间 / Unix时间戳]",
)
async def unix_time(message: Message):
    try:
        return await message.edit(format_time(message.arguments))
    except Exception as e:
        return await message.edit(f"出错了呜呜呜 ~ 无效的参数：{e}")
