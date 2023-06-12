""" PagerMaid module for channel help. """

import contextlib
from asyncio import sleep
from functools import partial
from random import uniform
from typing import Any

from pagermaid import log
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite
from pagermaid.utils import lang
from pyrogram.enums.chat_type import ChatType
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.types import Chat

WHITELIST = [-1001441461877]
AVAILABLE_OPTIONS = {"nosender", "nocaption", "silent"}


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
    parameters="set [from channel] [to channel] (nosender|nocaption|silent) 自动转发频道新消息（可以使用频道用户名或者 id）\n"
    "del [from channel] 删除转发\n"
    "backup [from channel] [to channel] (nosender|nocaption|silent) 备份频道（可以使用频道用户名或者 id）\n"
    "（选项：nocaption: 图像不带说明, nosender: 转发不带发送者信息, silent: 禁用通知）\n"
    "（注意：nocaption 需要与 nosender 一起使用）",
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
                as_copy="nosender" in options,
                disable_notification="silent" in options,
                remove_caption="nocaption" in options,
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
        await forward(
            message,
            target,
            as_copy="nosender" in options,
            disable_notification="silent" in options,
            remove_caption="nocaption" in options,
        )


async def loosely_forward(
    notifier: Message,
    message: Message,
    chat_id: int,
    as_copy: bool = False,
    disable_notification: bool = False,
    remove_caption: bool = False,
):
    try:
        await forward(message, chat_id, as_copy, disable_notification, remove_caption)
    except FloodWait as ex:
        min: int = ex.value  # type: ignore
        delay = min + uniform(0.5, 1.0)
        await notifier.edit(f"触发 Flood ，暂停 {delay} 秒。")
        await sleep(delay)
        await loosely_forward(
            notifier, message, chat_id, as_copy, disable_notification, remove_caption
        )
    except Exception:
        pass  # drop other errors


# no_copy solution is adapted from https://github.com/pyrogram/pyrogram/pull/227
def forward(
    message: Message,
    chat_id: int,
    as_copy: bool = False,
    disable_notification: bool = False,
    remove_caption: bool = False,
):
    if not as_copy:
        return message.forward(chat_id, disable_notification)

    if message.service:
        raise ValueError("Unable to copy service messages")

    if message.game:
        raise ValueError("Users cannot send messages with Game media type")

    # TODO: Improve markdown parser. Currently html appears to be more stable, thus we use it here because users
    #       can"t choose.

    if message.text:
        return message._client.send_message(
            chat_id,
            text=message.text.html,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=not message.web_page,
            disable_notification=disable_notification,
        )
    elif message.media:
        caption = (
            message.caption.html if message.caption and not remove_caption else None
        )

        send_media = partial(
            message._client.send_cached_media,
            chat_id=chat_id,
            disable_notification=disable_notification,
        )

        if message.photo:
            file_id = message.photo.file_id
        elif message.audio:
            file_id = message.audio.file_id
        elif message.document:
            file_id = message.document.file_id
        elif message.video:
            file_id = message.video.file_id
        elif message.animation:
            file_id = message.animation.file_id
        elif message.voice:
            file_id = message.voice.file_id
        elif message.sticker:
            file_id = message.sticker.file_id
        elif message.video_note:
            file_id = message.video_note.file_id
        elif message.contact:
            return message._client.send_contact(
                chat_id,
                phone_number=message.contact.phone_number,
                first_name=message.contact.first_name,
                last_name=message.contact.last_name,
                vcard=message.contact.vcard,
                disable_notification=disable_notification,
            )
        elif message.location:
            return message._client.send_location(
                chat_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
                disable_notification=disable_notification,
            )
        elif message.venue:
            return message._client.send_venue(
                chat_id,
                latitude=message.venue.location.latitude,
                longitude=message.venue.location.longitude,
                title=message.venue.title,
                address=message.venue.address,
                foursquare_id=message.venue.foursquare_id,
                foursquare_type=message.venue.foursquare_type,
                disable_notification=disable_notification,
            )
        elif message.poll:
            return message._client.send_poll(
                chat_id,
                question=message.poll.question,
                options=[opt.text for opt in message.poll.options],
                disable_notification=disable_notification,
            )
        elif message.game:
            return message._client.send_game(
                chat_id,
                game_short_name=message.game.short_name,
                disable_notification=disable_notification,
            )
        else:
            raise ValueError("Unknown media type")

        if (
            message.sticker or message.video_note
        ):  # Sticker and VideoNote should have no caption
            return send_media(file_id)
        else:
            return send_media(file_id=file_id, caption=caption, parse_mode=ParseMode.HTML)  # type: ignore
    else:
        raise ValueError("Can't copy this message")
