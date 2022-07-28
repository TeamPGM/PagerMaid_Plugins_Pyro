""" PagerMaid module that 鲁小迅 报时 """

from datetime import datetime
from typing import Optional

from pyrogram import Client
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.raw.types.messages import StickerSet
from pyrogram.types import Document

from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.scheduler import add_delete_message_job
from pagermaid.services import bot, scheduler
from pagermaid.utils import edit_delete, check_manage_subs
from pagermaid.sub_utils import Sub

lu_xiao_xun_bs_sub = Sub("luxiaoxunbs")
lu_xiao_xun_sticker: Optional[StickerSet] = None


@Hook.on_startup()
async def load_bs_sticker():
    global lu_xiao_xun_sticker
    try:
        lu_xiao_xun_sticker = await bot.invoke(GetStickerSet(
            stickerset=InputStickerSetShortName(short_name="luxiaoxunbs"),
            hash=0
        ))
    except Exception:
        lu_xiao_xun_sticker = None


async def get_bs_sticker():
    if not lu_xiao_xun_sticker:
        await load_bs_sticker()
    if not lu_xiao_xun_sticker:
        return None
    now = datetime.now()
    hour = now.hour - 1
    if now.minute > 30:
        hour += 1
    hour %= 12
    if hour == -1:
        hour = 11
    return Document._parse(bot, lu_xiao_xun_sticker.documents[hour % 12], "sticker.webp")  # noqa


@scheduler.scheduled_job("cron", minute="0", id="lu_xiao_xun_bs.push")
async def lu_xiao_xun_bs_subscribe() -> None:
    sticker = await get_bs_sticker()
    if not sticker:
        return
    for gid in lu_xiao_xun_bs_sub.get_subs():
        try:
            msg = await bot.send_document(gid, sticker.file_id)
            add_delete_message_job(msg, delete_seconds=3600)
        except Exception:
            lu_xiao_xun_bs_sub.del_id(gid)


@listener(command="luxiaoxunbs",
          parameters="订阅/退订",
          description="整点报时，每小时定时发送，自动删除上一条消息")
async def lu_xiao_xun_bs(_: Client, message: Message):
    if not message.arguments:
        return await message.edit("请输入订阅/退订")
    if not check_manage_subs(message):
        return await edit_delete(message, "❌ 权限不足，无法操作整点报时", parse_mode=ParseMode.HTML)
    if message.arguments == "订阅":
        if lu_xiao_xun_bs_sub.check_id(message.chat.id):
            return await edit_delete(message, "❌ 你已经订阅了整点报时", parse_mode=ParseMode.HTML)
        lu_xiao_xun_bs_sub.add_id(message.chat.id)
        await message.edit("你已经成功订阅了整点报时")
    elif message.arguments == "退订":
        if not lu_xiao_xun_bs_sub.check_id(message.chat.id):
            return await edit_delete(message, "❌ 你还没有订阅整点报时", parse_mode=ParseMode.HTML)
        lu_xiao_xun_bs_sub.del_id(message.chat.id)
        await message.edit("你已经成功退订了整点报时")
    else:
        return await message.edit("请输入订阅/退订")
