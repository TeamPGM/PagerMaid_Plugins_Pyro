import contextlib

from pagermaid.services import sqlite
from pagermaid.scheduler import add_delete_message_job
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.utils import alias_command


class DelTask:
    @staticmethod
    def check_time(time: str, min_value: int = None, max_value: int = None) -> str:
        if max_value and int(time) > max_value:
            raise ValueError(f"Time value {time} is too large")
        if min_value and int(time) < min_value:
            raise ValueError(f"Time value {time} is too small")
        if int(time) < 0:
            raise ValueError(f"Time value {time} is too small")
        return time

    @staticmethod
    def parse_time(text: str) -> int:
        data = text.strip().split(" ")
        second, minute, hour, day = 0, 0, 0, 0
        if len(data) % 2:
            raise ValueError("Invalid task format")
        for i in range(1, len(data)):
            if data[i] == "seconds":
                second = DelTask.check_time(data[i - 1], 0, 60)
            elif data[i] == "minutes":
                minute = DelTask.check_time(data[i - 1], 0, 60)
            elif data[i] == "hours":
                hour = DelTask.check_time(data[i - 1], 0, 24)
            elif data[i] == "days":
                day = DelTask.check_time(data[i - 1], 0, 31)
        if (
            second := int(second)
            + int(minute) * 60
            + int(hour) * 3600
            + int(day) * 86400
        ):
            return second
        else:
            raise ValueError("Invalid task format")

    @staticmethod
    def get_del_seconds(cid: int):
        return sqlite.get(f"autodel.{cid}", 0)

    @staticmethod
    async def parse_task(message: Message):
        cid = message.chat.id
        text = message.arguments
        if not text:
            raise ValueError("Invalid task format")
        if "global" in text:
            cid = 0
            text = text.replace("global", "")
        if "cancel" in text:
            del sqlite[f"autodel.{cid}"]
            return
        seconds = DelTask.parse_time(text)
        sqlite[f"autodel.{cid}"] = seconds

    @staticmethod
    def add_task(message: Message):
        if seconds := DelTask.get_del_seconds(0) or DelTask.get_del_seconds(
            message.chat.id
        ):
            add_delete_message_job(message, seconds)

    @staticmethod
    def get_list(cid: int):
        seconds = DelTask.get_del_seconds(cid)
        global_seconds = DelTask.get_del_seconds(0)
        if seconds:
            return f"Current chat autodel time is {seconds} seconds"
        elif global_seconds:
            return f"Current chat autodel time is global {global_seconds} seconds"
        return "Current chat autodel time is not set"


auto_del_help_msg = f"""
定时删除消息。

,{alias_command("autodel")} 1 seconds
,{alias_command("autodel")} 1 minutes
,{alias_command("autodel")} 1 hours
,{alias_command("autodel")} 1 days
,{alias_command("autodel")} 1 seconds global
,{alias_command("autodel")} cancel

,{alias_command("autodel")} l - 查看自动删除任务
"""


@listener(
    command="autodel",
    need_admin=True,
    description=f"定时删除消息\n请使用 ,{alias_command('autodel')} h 查看可用命令",
)
async def auto_del(message: Message):
    if message.arguments == "h" or len(message.parameter) == 0:
        return await message.edit(auto_del_help_msg)
    elif message.arguments == "l":
        return await message.edit(DelTask.get_list(message.chat.id))
    try:
        await DelTask.parse_task(message)
        await message.edit(
            "设置自动删除任务成功。" if message.arguments != "cancel" else "取消自动删除任务成功。"
        )
    except ValueError as e:
        await message.edit(f"开启失败：{str(e)}")
    except KeyError:
        await message.edit("未开启自动删除")


@listener(incoming=False, outgoing=True)
async def auto_del_task(message: Message):
    with contextlib.suppress(Exception):
        DelTask.add_task(message)
