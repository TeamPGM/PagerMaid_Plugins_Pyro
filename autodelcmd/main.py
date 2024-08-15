import contextlib

from pagermaid.enums import Client, Message
from pagermaid.hook import Hook
from pagermaid.single_utils import sqlite

@Hook.command_postprocessor()
async def auto_delete(client: Client, message: Message, command: str, sub_command: str):
    if command in [
        "lang",
        "alias",
        "apt",
        "apt_source",
        "reload",
    ]:
        if message.parameter and message.parameter[0] in [
            "status",
            "list",
        ]:
            await message.delay_delete(60)
        else:
            await message.delay_delete(10)
    elif command in [
        "help",
        "help_raw",
        "id",
        "ping",
        "pingdc",
        "stats",
        "status",
        "sysinfo",
    ]:
        await message.delay_delete(120)
    elif command in [
        "speed",
        "speedtest",
        "v",
    ]:
        async for msg in client.get_chat_history(message.chat.id, limit=100):
            if msg.from_user and msg.from_user.is_self:
                await msg.delay_delete(120)
                break

@Hook.on_startup()
async def auto_delete_on_startup(client: Client):
    data = sqlite.get("exit_msg", {})
    cid, mid = data.get("cid", 0), data.get("mid", 0)
    if data and cid and mid:
        with contextlib.suppress(Exception):
            message: Message = await client.get_messages(cid, mid)
            if message:
                await message.delay_delete(10)
