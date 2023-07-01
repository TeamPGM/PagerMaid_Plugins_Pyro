""" https://github.com/A-kirami/nonebot-plugin-chatgpt """

import contextlib
import threading
import uuid

from collections import defaultdict

from typing import Optional

from pagermaid.services import scheduler, sqlite
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.utils import pip_install

pip_install("revChatGPT", "==0.0.33.2")

from asyncChatGPT.asyncChatGPT import Chatbot


class AsyncChatbot:
    def __init__(self) -> None:
        self.config = {"session_token": self.get_token()} if self.get_token() else {}
        self.bot = Chatbot(config=self.config, refresh=False)

    def __call__(
        self, conversation_id: Optional[str] = None, parent_id: Optional[str] = None
    ):
        self.bot.conversation_id = conversation_id
        self.bot.parent_id = parent_id or self.id
        return self

    @property
    def id(self) -> str:
        return str(uuid.uuid4())

    def set_token(self, token: str) -> None:
        sqlite["chatgbt_token"] = token
        self.config["session_token"] = token

    @staticmethod
    def get_token() -> str:
        return sqlite.get("chatgbt_token", None)

    @staticmethod
    def del_token():
        del sqlite["chatgbt_token"]

    async def get_chat_response(self, prompt: str) -> str:
        return (await self.bot.get_chat_response(prompt)).get("message", "")

    async def refresh_session(self) -> None:
        if not self.get_token():
            return
        self.bot.refresh_session()
        self.set_token(self.bot.config["session_token"])


chat_bot = AsyncChatbot()
chat_bot_session = defaultdict(dict)
chat_bot_lock = threading.Lock()
chat_bot_help = (
    "使用 ChatGPT 聊天\n\n"
    "参数：\n\n- 无参数：进入聊天模式\n"
    "- reset：重置聊天状态\n"
    "- set <session_token>：设置 ChatGPT 会话令牌，获取令牌： https://t.me/PagerMaid_Modify/212 \n"
    "- del：删除 ChatGPT 会话令牌"
)


@scheduler.scheduled_job("interval", minutes=30)
async def refresh_session() -> None:
    await chat_bot.refresh_session()


@listener(
    command="chatgpt",
    description=chat_bot_help,
)
async def chat_bot_func(message: Message):
    if not message.arguments:
        return await message.edit(chat_bot_help)
    from_id = message.from_user.id if message.from_user else 0
    from_id = message.sender_chat.id if message.sender_chat else from_id
    if not from_id:
        from_id = message.chat.id
    if len(message.parameter) == 2 and message.parameter[0] == "set":
        token = message.parameter[1]
        if not token.startswith("ey"):
            return await message.edit("无效的 token。")
        chat_bot.set_token(message.parameter[1])
        try:
            await chat_bot.refresh_session()
        except Exception as e:
            return await message.edit(f"设置失败：{e}")
        return await message.edit("设置 Token 成功，可以开始使用了。")
    elif message.arguments == "reset":
        with contextlib.suppress(KeyError):
            del chat_bot_session[from_id]
        return await message.edit("已重置聊天状态。")
    elif message.arguments == "del":
        if not chat_bot.get_token():
            return await message.edit("没有设置 Token。")
        chat_bot.del_token()
        return await message.edit("已删除 Token。")
    if not chat_bot.get_token():
        return await message.edit("请先通过参数 `set [session_token]` 设置 OpenAI API Token。")
    with chat_bot_lock:
        try:
            msg = await chat_bot(**chat_bot_session[from_id]).get_chat_response(
                message.arguments
            )
        except Exception as e:
            msg = f"可能是 Session Token 过期了，请重新设置。\n{str(e)}"
        if not msg:
            msg = "无法获取到回复，可能是网络波动，请稍后再试。"
        with contextlib.suppress(Exception):
            await message.edit(msg)
        chat_bot_session[from_id]["conversation_id"] = chat_bot.bot.conversation_id
        chat_bot_session[from_id]["parent_id"] = chat_bot.bot.parent_id
