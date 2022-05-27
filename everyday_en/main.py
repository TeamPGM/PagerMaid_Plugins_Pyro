""" PagerMaid module that 每日英语 """

from os import sep
from os.path import isfile
from datetime import date
from typing import Optional, Dict

from pyrogram import Client
from pyrogram.enums.parse_mode import ParseMode
from pagermaid import scheduler
from pagermaid import bot
from pagermaid.group_manager import enforce_permission
from pagermaid.listener import listener
from pagermaid.modules.help import from_msg_get_sudo_uid
from pagermaid.utils import client, Message, from_self, edit_delete
from pagermaid.single_utils import safe_remove
from pagermaid.sub_utils import Sub

everyday_en_sub = Sub("everyday_en")
everyday_en_data_cache: Optional[Dict] = None
everyday_en_cache_time: Optional[date] = None


async def get_everyday_en() -> None:
    global everyday_en_data_cache, everyday_en_cache_time
    if everyday_en_cache_time == date.today() and everyday_en_data_cache and \
            isfile(f"data{sep}everyday_en.jpg") and isfile(f"data{sep}everyday_en.mp3"):
        return
    resp = await client.get("https://open.iciba.com/dsapi/")
    if resp.is_error:
        raise ValueError(f"每日英语获取失败，错误码：{resp.status_code}")
    everyday_en_data_cache = resp.json()
    everyday_en_cache_time = date.today()
    safe_remove(f"data{sep}everyday_en.jpg")
    safe_remove(f"data{sep}everyday_en.mp3")
    url = everyday_en_data_cache.get("fenxiang_img", "")
    if url:
        resp = await client.get(url, follow_redirects=True)
        with open(f"data{sep}everyday_en.jpg", "wb") as f:
            f.write(resp.content)
    url = everyday_en_data_cache.get("tts", "")
    if url:
        resp = await client.get(url, follow_redirects=True)
        with open(f"data{sep}everyday_en.mp3", "wb") as f:
            f.write(resp.content)


async def push_everyday_en(gid: int) -> None:
    reply = None
    if isfile(f"data{sep}everyday_en.jpg"):
        reply = await bot.send_photo(
            gid,
            f"data{sep}everyday_en.jpg",
            caption=f"【{everyday_en_data_cache['dateline']}】\n"
                    f"{everyday_en_data_cache['content']}\n"
                    f"释义：{everyday_en_data_cache['note']}"
        )
    if isfile(f"data{sep}everyday_en.mp3"):
        await bot.send_voice(
            gid,
            f"data{sep}everyday_en.mp3",
            reply_to_message_id=reply.id if reply else None,
        )


@scheduler.scheduled_job("cron", hour="8", id="everyday_en.push")
async def everyday_en_subscribe() -> None:
    await get_everyday_en()
    for gid in everyday_en_sub.get_subs():
        try:
            await push_everyday_en(gid)
        except Exception as e:  # noqa
            everyday_en_sub.del_id(gid)


@listener(command="everyday_en",
          parameters="订阅/退订",
          description="查看今日每日英语，支持订阅/退订每天上午八点定时发送")
async def everyday_en(_: Client, message: Message):
    """ 每日英语 """
    if not message.arguments:
        try:
            await get_everyday_en()
        except ValueError as e:
            return await message.edit(e.__str__())
        await message.safe_delete()
        await push_everyday_en(message.chat.id)
    elif message.arguments == "订阅":
        if from_self(message) or enforce_permission(from_msg_get_sudo_uid(message), "modules.manage_subs"):
            if everyday_en_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你已经订阅了每日英语", parse_mode=ParseMode.HTML)
            everyday_en_sub.add_id(message.chat.id)
            await message.edit("你已经成功订阅了每日英语")
        else:
            await edit_delete(message, "❌ 权限不足，无法订阅每日英语", parse_mode=ParseMode.HTML)
    elif message.arguments == "退订":
        if from_self(message) or enforce_permission(from_msg_get_sudo_uid(message), "modules.manage_subs"):
            if not everyday_en_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你还没有订阅每日英语", parse_mode=ParseMode.HTML)
            everyday_en_sub.del_id(message.chat.id)
            await message.edit("你已经成功退订了每日英语")
        else:
            await edit_delete(message, "❌ 权限不足，无法退订每日英语", parse_mode=ParseMode.HTML)
