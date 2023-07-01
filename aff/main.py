import contextlib

from typing import Tuple

from pagermaid.enums import Message
from pagermaid.services import sqlite
from pagermaid.listener import listener


def get_aff() -> Tuple[str, bool]:
    return sqlite.get("aff.text", ""), sqlite.get("aff.web_page", False)


def set_aff(text: str, web_page: bool = False) -> None:
    sqlite.update({"aff.text": text, "aff.web_page": web_page})


def del_aff() -> None:
    text, web_page = get_aff()
    if text:
        del sqlite["aff.text"]
    if web_page:
        del sqlite["aff.web_page"]


@listener(
    command="aff",
    description="在别人要打算买机场的时候光速发出自己的aff信息(请尽量配合短链接)",
    parameters="[save|remove] (可选，回复一条消息，用于保存|删除aff信息)",
)
async def aff(message: Message):
    if not message.parameter:
        msg, web_page = get_aff()
        if not msg:
            return await message.edit("出错了呜呜呜 ~ Aff消息不存在。\n(你有提前保存好嘛？)")
        with contextlib.suppress(Exception):
            await message.edit(msg, disable_web_page_preview=not web_page)
    elif message.parameter[0] == "save":
        if not message.reply_to_message:
            return await message.edit("出错了呜呜呜 ~ 请回复一条消息以保存新的Aff信息。")
        text = message.reply_to_message.text or message.reply_to_message.caption
        web_page = message.reply_to_message.web_page or False
        if not text:
            return await message.edit("出错了呜呜呜 ~ 请回复一条消息以保存新的Aff信息。")
        set_aff(text.html, web_page)
        await message.edit("好耶 ！ Aff信息保存成功。")
    elif message.parameter[0] == "remove":
        del_aff()
        await message.edit("好耶 ！ Aff信息删除成功。")
    else:
        await message.edit("出错了呜呜呜 ~ 无效的参数。")
