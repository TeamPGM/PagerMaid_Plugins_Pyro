import time

from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message


def time_to_unix(t):
    """将时间转换为Unix时间戳"""
    return int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))


def unix_to_time(t):
    """将Unix时间戳转换为时间"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(t)))


@listener(command="unixtime",
          description="Unix时间戳转换\n参数缺省将当前服务器时间转换为Unix时间戳\n时间格式: `YYYY-MM-DD HH:MM:SS`",
          parameters="<缺省 / 时间 / Unix时间戳>"
          )
async def unixtime(_: Client, message: Message):
    msg = message.arguments
    if not msg:
        return await message.edit(f"`{int(time.time())}`")
    if ":" in msg:
        try:
            return await message.edit(f"`{time_to_unix(msg)}`")
        except ValueError:
            return await message.edit("`出错了呜呜呜 ~ 无效的参数。`")
    try:
        return await message.edit(f"`{unix_to_time(msg)}`")
    except ValueError:
        return await message.edit("`出错了呜呜呜 ~ 无效的参数。`")
