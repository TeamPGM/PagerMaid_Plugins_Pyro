""" PagerMaid module for channel help. """

import contextlib
from asyncio import sleep
from random import uniform
from typing import Any, List, Union, Set

from pyrogram.enums.chat_type import ChatType
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.types import Chat

from pagermaid import log, logs
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite
from pagermaid.utils import lang

WHITELIST = [-1001441461877]
AVAILABLE_OPTIONS = {"silent", "text", "all", "photo", "document", "video"}


def try_cast_or_fallback(val: Any, t: type) -> Any:
    try:
        return t(val)
    except:
        return val


def check_chat_available(chat: Chat):
    assert (
        chat.type in [ChatType.CHANNEL, ChatType.GROUP,ChatType.SUPERGROUP,ChatType.BOT,ChatType.PRIVATE]
        and not chat.has_protected_content
    )


@listener(
    command="shift",
    description="开启转发频道新消息功能",
    parameters="set [from channel] [to channel] (silent) 自动转发频道新消息（可以使用频道用户名或者 id）\n"
    "del [from channel] 删除转发\n"
    "backup [from channel] [to channel] (silent) 备份频道（可以使用频道用户名或者 id）\n"
    "list 顯示目前轉發的頻道\n\n"
    "选项说明：\n"
    "silent: 禁用通知, text: 文字, all: 全部訊息都傳, photo: 圖片, document: 檔案, video: 影片",
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
            message.parameter[3:] if len(message.parameter) > 3 else ["all"]
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

        # 如果有把get_chat_history方法merge進去就可以實現從舊訊息到新訊息,https://github.com/pyrogram/pyrogram/pull/1046
        # async for msg in client.get_chat_history(source.id,reverse=True):

        async for msg in client.search_messages(source.id):  # type: ignore
            await sleep(uniform(0.5, 1.0))
            await loosely_forward(
                message,
                msg,
                target.id,
                options,
                disable_notification="silent" in options,
            )
        await message.edit(f"备份频道 {source.id} 到 {target.id} 已完成。")
    # 列出要轉存的頻道
    elif message.parameter[0] == "list":
        from_ids = list(
            filter(
                lambda x: (x.startswith("shift.") and (not x.endswith("options"))),
                list(sqlite.keys()),
            )
        )
        if not from_ids:
            return await message.edit("沒有要轉存的頻道")
        output = "總共有 %d 個頻道要轉存\n\n" % len(from_ids)
        for from_id in from_ids:
            to_id = sqlite[from_id]
            output += "%s -> %s\n" % (
                format_channel_id(from_id[6:]),
                format_channel_id(to_id),
            )
        await message.edit(output)
    else:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return


def format_channel_id(channel_id: str):
    short_channel_id = str(channel_id)[4:]
    return f"[{channel_id}](https://t.me/c/{short_channel_id})"


@listener(is_plugin=True, incoming=True, ignore_edited=True)
async def shift_channel_message(message: Message):
    """Event handler to auto forward channel messages."""
    d = dict(sqlite)
    source = message.chat.id

    # 找訊息類型video、document...
    media_type = message.media.value if message.media else "text"
    target = d.get(f"shift.{source}")
    if not target:
        return
    if message.chat.has_protected_content:
        del sqlite[f"shift.{source}"]
        return
    options = d.get(f"shift.{source}.options") or []

    with contextlib.suppress(Exception):
        if (not options) or "all" in options:
            await message.forward(
                target,
                disable_notification="silent" in options,
            )
        elif media_type in options:
            await message.forward(
                target,
                disable_notification="silent" in options,
            )
        else:
            logs.debug("skip message type: %s", media_type)


async def loosely_forward(
    notifier: Message,
    message: Message,
    chat_id: int,
    options: Union[List[str], Set[str]],
    disable_notification: bool = False,
):
    # 找訊息類型video、document...
    media_type = message.media.value if message.media else "text"
    try:
        if (not options) or "all" in options:
            await message.forward(
                chat_id,
                disable_notification=disable_notification,
            )
        elif media_type in options:
            await message.forward(
                chat_id,
                disable_notification=disable_notification,
            )
        else:
            logs.debug("skip message type: %s", media_type)
        # await message.forward(chat_id, disable_notification=disable_notification)
    except FloodWait as ex:
        min: int = ex.value  # type: ignore
        delay = min + uniform(0.5, 1.0)
        await notifier.edit(f"触发 Flood ，暂停 {delay} 秒。")
        await sleep(delay)
        await loosely_forward(notifier, message, chat_id, options, disable_notification)
    except Exception:
        pass  # drop other errors
