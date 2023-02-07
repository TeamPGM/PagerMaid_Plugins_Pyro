""" PagerMaid module for channel help. """
from asyncio import sleep
from random import uniform
from pyrogram.enums.chat_type import ChatType
from pyrogram.errors.exceptions.flood_420 import FloodWait

from pagermaid import log
from pagermaid.single_utils import sqlite
from pagermaid.enums import Client, Message
from pagermaid.utils import lang
from pagermaid.listener import listener

import contextlib


@listener(command="shift",
          description='开启转发频道新消息功能',
          parameters="set [from channel] [to channel] 自动转发频道新消息（可以使用频道用户名或者 id）\n"
                     "del [from channel] 删除转发\n"
                     "backup [from channel] [to channel] 备份频道（可以使用频道用户名或者 id）")
async def shift_set(client: Client, message: Message):
    if not 1 < len(message.parameter) < 4:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return
    if message.parameter[0] == "set":
        if len(message.parameter) != 3:
            return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        # 检查来源频道
        try:
            channel = await client.get_chat(int(message.parameter[1]))
            if channel.type != ChatType.CHANNEL:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
            if channel.has_protected_content:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        except Exception:
            try:
                channel = await client.get_chat(message.parameter[1])
                if channel.type != ChatType.CHANNEL:
                    return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
                if channel.has_protected_content:
                    return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
            except Exception:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        if channel.id in [-1001441461877]:
            return await message.edit('出错了呜呜呜 ~ 此对话位于白名单中。')
        # 检查目标频道
        try:
            to = await client.get_chat(int(message.parameter[2]))
        except Exception:
            try:
                to = await client.get_chat(message.parameter[2])
            except Exception:
                return await message.edit("出错了呜呜呜 ~ 无法识别的目标对话。")
        if to.id in [-1001441461877]:
            await message.edit('出错了呜呜呜 ~ 此对话位于白名单中。')
            return
        sqlite[f"shift.{channel.id}"] = to.id
        await message.edit(f"已成功配置将对话 {channel.id} 的新消息转发到 {to.id} 。")
        await log(f"已成功配置将对话 {channel.id} 的新消息转发到 {to.id} 。")
    elif message.parameter[0] == "del":
        if len(message.parameter) != 2:
            return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        # 检查来源频道
        try:
            channel = await client.get_chat(int(message.parameter[1]))
        except Exception:
            try:
                channel = await client.get_chat(message.parameter[1])
            except Exception:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        try:
            del sqlite[f"shift.{channel.id}"]
        except Exception as e:
            return await message.edit('emm...当前对话不存在于自动转发列表中。')
        await message.edit(f"已成功关闭对话 {str(channel.id)} 的自动转发功能。")
        await log(f"已成功关闭对话 {str(channel.id)} 的自动转发功能。")
    elif message.parameter[0] == "backup":
        if len(message.parameter) != 3:
            return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        # 检查来源频道
        try:
            channel = await client.get_chat(int(message.parameter[1]))
            if channel.type != ChatType.CHANNEL:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
            if channel.has_protected_content:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        except Exception:
            try:
                channel = await client.get_chat(message.parameter[1])
                if channel.type != ChatType.CHANNEL:
                    return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
                if channel.has_protected_content:
                    return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
            except Exception:
                return await message.edit("出错了呜呜呜 ~ 无法识别的来源对话。")
        if channel.id in [-1001441461877]:
            return await message.edit('出错了呜呜呜 ~ 此对话位于白名单中。')
        # 检查目标频道
        try:
            to = await client.get_chat(int(message.parameter[2]))
        except Exception:
            try:
                to = await client.get_chat(message.parameter[2])
            except Exception:
                return await message.edit("出错了呜呜呜 ~ 无法识别的目标对话。")
        if to.id in [-1001441461877]:
            return await message.edit('出错了呜呜呜 ~ 此对话位于白名单中。')
        # 开始遍历消息
        await message.edit(f'开始备份频道 {channel.id} 到 {to.id} 。')
        async for msg in client.search_messages(channel.id):
            await sleep(uniform(0.5, 1.0))
            await forward_msg(message, msg, to.id)
        await message.edit(f'备份频道 {channel.id} 到 {to.id} 已完成。')
    else:
        await message.edit(f"{lang('error_prefix')}{lang('arg_error')}")
        return


@listener(is_plugin=True, incoming=True, ignore_edited=True)
async def shift_channel_message(message):
    """ Event handler to auto forward channel messages. """
    cid = sqlite.get(f"shift.{message.chat.id}", None)
    if not cid:
        return
    if message.chat.id in [-1001441461877]:
        return
    if message.chat.has_protected_content:
        del sqlite[f"shift.{message.chat.id}"]
        return
    with contextlib.suppress(Exception):
        await message.forward(cid)


async def forward_msg(message, msg, cid):
    try:
        await msg.forward(msg, cid)
    except FloodWait as e:
        await message.edit(f'触发 Flood ，暂停 {e.value + uniform(0.5, 1.0)} 秒。')
        try:
            await sleep(e.value + uniform(0.5, 1.0))
        except Exception as e:
            print(f"Wait flood error: {e}")
            return
        await forward_msg(message, msg, cid)
