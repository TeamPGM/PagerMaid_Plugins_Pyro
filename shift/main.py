""" PagerMaid module for channel help. """

import contextlib
from asyncio import sleep
from random import uniform
from typing import Any

from pagermaid import log
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite
from pagermaid.utils import lang
from pyrogram.enums.chat_type import ChatType
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.types import Chat

WHITELIST = [-1001441461877]
AVAILABLE_OPTIONS = {"silent"}


def try_cast_or_fallback(val: Any, t: type) -> Any:
    try:
        return t(val)
    except:
        return val


def check_chat_available(chat: Chat):
    assert chat.type == ChatType.CHANNEL and not chat.has_protected_content


@listener(
    command="shift",
    description="开启转发频道新消息功能",
    parameters="set [from channel] [to channel] (silent) 自动转发频道新消息（可以使用频道用户名或者 id）\n"
    "del [from channel] 删除转发\n"
    "backup [from channel] [to channel] (silent) 备份频道（可以使用频道用户名或者 id）\n\n"
    "选项说明：\n"
    "silent: 禁用通知",
)
async def shift_set(client: Client, message: Message):
    if not message.parameter:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    if message.parameter[0] == "set":
        if len(message.parameter) < 3:
            return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        options = set(message.parameter[3:] if len(message.parameter) > 3 else ())
        if set(options).difference(AVAILABLE_OPTIONS):
            return await message.edit("出错了呜呜呜 ~ 无法识别的选项。")
        # 检查来源频道
        try:
            source = await client.get_chat(
                try_cast_or_fallback(message.parameter[1], int)
            )
            assert isinstance(source, Chat)
            check_chat_available(source)
        except Exception:
            return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        if source.id in WHITELIST:
            return await message.edit("出错了呜呜呜 ~ 此对话位于白名单中。")
        # 检查目标频道
        try:
            target = await client.get_chat(
                try_cast_or_fallback(message.parameter[2], int)
            )
            assert isinstance(target, Chat)
        except Exception:
            return await message.edit("出错了呜呜呜 ~ 无法识别的目标对话。")
        if target.id in WHITELIST:
            await message.edit("出错了呜呜呜 ~ 此对话位于白名单中。")
            return
        sqlite[f"shift.{source.id}"] = target.id
        sqlite[f"shift.{source.id}.options"] = (
            message.parameter[3:] if len(message.parameter) > 3 else []
        )
        await message.edit(f"已成功配置将对话 {source.id} 的新消息转发到 {target.id} 。")
        await log(f"已成功配置将对话 {source.id} 的新消息转发到 {target.id} 。")
    elif message.parameter[0] == "del":
        if len(message.parameter) != 2:
            return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        # 检查来源频道
        try:
            source = await client.get_chat(
                try_cast_or_fallback(message.parameter[1], int)
            )
            assert isinstance(source, Chat)
        except Exception:
            return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        try:
            del sqlite[f"shift.{source.id}"]
            with contextlib.suppress(Exception):
                del sqlite[f"shift.{source.id}.options"]
        except Exception:
            return await message.edit("emm...当前对话不存在于自动转发列表中。")
        await message.edit(f"已成功关闭对话 {str(source.id)} 的自动转发功能。")
        await log(f"已成功关闭对话 {str(source.id)} 的自动转发功能。")
    elif message.parameter[0] == "backup":
        if len(message.parameter) < 3:
            return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        options = set(message.parameter[3:] if len(message.parameter) > 3 else ())
        if set(options).difference(AVAILABLE_OPTIONS):
            return await message.edit("出错了呜呜呜 ~ 无法识别的选项。")
        # 检查来源频道
        try:
            source = await client.get_chat(
                try_cast_or_fallback(message.parameter[1], int)
            )
            assert isinstance(source, Chat)
            check_chat_available(source)
        except Exception:
            return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        if source.id in WHITELIST:
            return await message.edit("出错了呜呜呜 ~ 此对话位于白名单中。")
        # 检查目标频道
        try:
            target = await client.get_chat(
                try_cast_or_fallback(message.parameter[2], int)
            )
            assert isinstance(target, Chat)
        except Exception:
            return await message.edit("出错了呜呜呜 ~ 无法识别的目标对话。")
        if target.id in WHITELIST:
            return await message.edit("出错了呜呜呜 ~ 此对话位于白名单中。")
        # 开始遍历消息
        await message.edit(f"开始备份频道 {source.id} 到 {target.id} 。")
        async for msg in client.search_messages(source.id):  # type: ignore
            await sleep(uniform(0.5, 1.0))
            await loosely_forward(
                message,
                msg,
                target.id,
                disable_notification="silent" in options,
            )
        await message.edit(f"备份频道 {source.id} 到 {target.id} 已完成。")
    else:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return


@listener(is_plugin=True, incoming=True, ignore_edited=True)
async def shift_channel_message(message: Message):
    """Event handler to auto forward channel messages."""
    d = dict(sqlite)
    source = message.chat.id
    target = d.get(f"shift.{source}")
    if not target:
        return
    if message.chat.has_protected_content:
        del sqlite[f"shift.{source}"]
        return
    options = d.get(f"shift.{source}.options") or []

    with contextlib.suppress(Exception):
        await message.forward(
            target,
            disable_notification="silent" in options,
        )


async def loosely_forward(
    notifier: Message,
    message: Message,
    chat_id: int,
    disable_notification: bool = False,
):
    try:
        await message.forward(chat_id, disable_notification=disable_notification)
    except FloodWait as ex:
        min: int = ex.value  # type: ignore
        delay = min + uniform(0.5, 1.0)
        await notifier.edit(f"触发 Flood ，暂停 {delay} 秒。")
        await sleep(delay)
        await loosely_forward(notifier, message, chat_id, disable_notification)
    except Exception:
        pass  # drop other errors
