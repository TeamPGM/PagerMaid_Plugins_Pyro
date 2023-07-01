import asyncio
import contextlib
import re
import random
from pyrogram import Client

from pagermaid.enums import Message
from pagermaid.services import sqlite, bot
from pagermaid.listener import listener
from pagermaid.utils import edit_delete, pip_install, lang

pip_install("snownlp")

from snownlp import SnowNLP


def from_msg_get_cid(message: Message) -> int:
    if reply := message.reply_to_message:
        return reply.from_user.id if reply.from_user else reply.sender_chat.id
    else:
        return message.chat.id


class Setting:
    def __init__(self, key_name: str):
        self.key_name = key_name
        sqlite[self.key_name] = sqlite.get(self.key_name, [])

    def toggle(self):
        return sqlite.get(f"{self.key_name}.toggle", False)

    def chats(self):
        return sqlite.get(f"{self.key_name}.chats", [])


ai_setting = Setting("aireply")


@listener(
    command="aireply",
    need_admin=True,
    parameters="{on|off|add|del|list}",
    description="通过预设根据语义分析进行应答，支持设置白名单并全局开关",
)
async def ai_reply(_: Client, message: Message):
    input_str = message.arguments
    chats = ai_setting.chats()

    if input_str == "on":
        sqlite[f"{ai_setting.key_name}.toggle"] = True
        await edit_delete(message, "已启用自动回复")
    elif input_str == "off":
        sqlite[f"{ai_setting.key_name}.toggle"] = False
        await edit_delete(message, "已禁用自动回复")
    elif input_str == "add":
        if not message.reply_to_message:
            return await message.edit("你需要回复某人的消息")
        chatid = from_msg_get_cid(message)
        if chatid < 0:
            return await edit_delete(message, "仅支持对私聊启用自动回复")
        chats.append(chatid)
        sqlite[f"{ai_setting.key_name}.chats"] = chats
        await edit_delete(message, "已为他启用自动回复")
    elif input_str == "del":
        if not message.reply_to_message:
            return await message.edit("你需要回复某人的消息")
        chatid = from_msg_get_cid(message)
        chats.remove(chatid)
        sqlite[f"{ai_setting.key_name}.chats"] = chats
        await edit_delete(message, "已为他禁用自动回复")
    elif input_str == "list":
        text = "已对以下用户启用自动回复：\n\n"
        for chatid in chats:
            try:
                user = await bot.get_users(chatid)
                text += f"• {user.mention()}\n"
            except Exception:
                text += f"• `{chatid}`\n"
        await message.edit(text)
    else:
        await edit_delete(message, lang("arg_error"))


@listener(incoming=True, outgoing=True, privates_only=True)
async def replay_listener(_, message: Message):
    with contextlib.suppress(Exception):
        if ai_setting.toggle() and ai_setting.chats().index(message.from_user.id) > 0:
            msg = message.text
            s = SnowNLP(msg)
            reply = 0
            if s.sentiments > 0.65:
                reply = random.choice(["wc", "🐮", "!", "?"])
            elif s.sentiments < 0.25:
                reply = random.choice(["az", "嘶", "。", "正常", ".", "啊？"])
            elif 5 < len(msg) < 30:
                if re.search("怎|吗|咋|.不.|何|什么", msg):
                    body = re.search(r"(?:这|那|你|我|他|有啥|.不.)?(.+?)[？\?]?$", msg)
                    await asyncio.sleep(random.uniform(1, 2))
                    reply = f"{body[1]}?"
            elif random.random() < 0.2:
                reply = random.choice(["啊", "哦"])
            if reply != 0:
                await asyncio.sleep(random.uniform(0, 1))
                await bot.send_message(message.from_user.id, reply)
                print(
                    f"aireply: AI Reply to '{message.from_user.mention()}' by '{reply}'"
                )
