""" https://github.com/A-kirami/nonebot-plugin-chatgpt """

import contextlib
import uuid
import json

from collections import defaultdict

from typing import Any, Dict, Optional

from pagermaid.services import client, scheduler, sqlite
from pagermaid.enums import Message
from pagermaid.listener import listener

SESSION_TOKEN = "__Secure-next-auth.session-token"


class Chatbot:
    def __init__(self) -> None:
        self.conversation_id = None
        self.parent_id = None
        self.session_token = self.get_token()
        self.authorization = None

    def __call__(
            self, conversation_id: Optional[str] = None, parent_id: Optional[str] = None
    ):
        self.conversation_id = conversation_id
        self.parent_id = parent_id or self.id
        return self

    @property
    def id(self) -> str:
        return str(uuid.uuid4())

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.authorization}",
            "Content-Type": "application/json",
        }

    def reset_chat(self) -> None:
        self.conversation_id = None
        self.parent_id = self.id

    def generate_data(self, prompt: str) -> Dict[str, Any]:
        return {
            "action": "next",
            "messages": [
                {
                    "id": self.id,
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_id,
            "model": "text-davinci-002-render",
        }

    def set_token(self, token: str) -> None:
        sqlite["chatgbt_token"] = token
        self.session_token = token

    @staticmethod
    def get_token() -> str:
        return sqlite.get("chatgbt_token", None)

    @staticmethod
    def del_token():
        del sqlite["chatgbt_token"]

    async def get_chat_response(self, prompt: str) -> str:
        if not self.session_token:
            raise RuntimeError("No session token")
        if not self.authorization:
            await self.refresh_session()
        response = await client.post(
            "https://chat.openai.com/backend-api/conversation",
            headers=self.headers,
            data=json.dumps(self.generate_data(prompt)),  # type: ignore
            timeout=10,
        )
        try:
            response = response.text.splitlines()[-4]
            response = response[6:]
        except Exception as e:
            raise RuntimeError(f"Abnormal response content: {response.text}") from e
        response = json.loads(response)
        self.parent_id = response["message"]["id"]
        self.conversation_id = response["conversation_id"]
        return response["message"]["content"]["parts"][0]

    async def refresh_session(self) -> None:
        if not self.session_token:
            return
        cookies = {SESSION_TOKEN: self.session_token}
        response = await client.get("https://chat.openai.com/api/auth/session", cookies=cookies, timeout=10)
        try:
            self.session_token = response.cookies.get(SESSION_TOKEN, "")
            self.authorization = response.json()["accessToken"]
        except Exception as e:
            raise RuntimeError("Error refreshing session") from e


chat_bot = Chatbot()
chat_bot_session = defaultdict(dict)
chat_bot_help = "使用 ChatGPT 聊天\n\n" \
                "参数：\n\n- 无参数：进入聊天模式\n" \
                "- reset：重置聊天状态\n" \
                "- set <session_token>：设置 ChatGPT 会话令牌\n" \
                "- del：删除 ChatGPT 会话令牌"


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
    try:
        msg = await chat_bot(**chat_bot_session[from_id]).get_chat_response(message.arguments)
    except Exception as e:
        msg = str(e)
    with contextlib.suppress(Exception):
        await message.edit(msg)
    chat_bot_session[from_id]["conversation_id"] = chat_bot.conversation_id
    chat_bot_session[from_id]["parent_id"] = chat_bot.parent_id
