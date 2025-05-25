""" PagerMaid module that 摸鱼日历 """

from os import sep

from pyrogram import Client
from pyrogram.enums.parse_mode import ParseMode

from pagermaid.dependence import client, scheduler
from pagermaid.enums import Message
from pagermaid.group_manager import enforce_permission
from pagermaid.listener import listener
from pagermaid.modules.help import from_msg_get_sudo_uid
from pagermaid.services import bot
from pagermaid.utils import Sub
from pagermaid.utils.bot_utils import edit_delete
from pagermaid.utils.listener import from_self

moyu_sub = Sub("moyu")


async def get_calendar() -> None:
    url = "https://api.52vmy.cn/api/wl/moyu"
    resp = await client.get(url, follow_redirects=True)
    if resp.is_error:
        raise ValueError(f"摸鱼日历获取失败，错误码：{resp.status_code}")
    with open(f"data{sep}moyu.png", "wb") as f:
        f.write(resp.content)


async def push_moyu(gid: int, delete: bool = False) -> None:
    msg: Message = await bot.send_photo(
        gid,
        f"data{sep}moyu.png",
    )
    if delete:
        await msg.delay_delete()


@scheduler.scheduled_job("cron", hour="8", id="moyu.push")
async def calendar_subscribe() -> None:
    await get_calendar()
    for gid in moyu_sub.get_subs():
        try:
            await push_moyu(gid)
        except Exception as e:  # noqa
            moyu_sub.del_id(gid)


@listener(command="moyu", parameters="订阅/退订", description="查看今日摸鱼日历，支持订阅/退订每天上午八点定时发送")
async def moyu(_: Client, message: Message):
    """摸鱼日历"""
    if not message.arguments:
        try:
            await get_calendar()
        except ValueError as e:
            return await message.edit(e.__str__())
        await message.safe_delete()
        await push_moyu(message.chat.id, delete=True)
    elif message.arguments == "订阅":
        if from_self(message) or enforce_permission(
            from_msg_get_sudo_uid(message), "modules.manage_subs"
        ):
            if moyu_sub.check_id(message.chat.id):
                return await edit_delete(
                    message, "❌ 你已经订阅了摸鱼日历", parse_mode=ParseMode.HTML
                )
            moyu_sub.add_id(message.chat.id)
            await message.edit("你已经成功订阅了摸鱼日历")
        else:
            await edit_delete(message, "❌ 权限不足，无法订阅摸鱼日历", parse_mode=ParseMode.HTML)
    elif message.arguments == "退订":
        if from_self(message) or enforce_permission(
            from_msg_get_sudo_uid(message), "modules.manage_subs"
        ):
            if not moyu_sub.check_id(message.chat.id):
                return await edit_delete(
                    message, "❌ 你还没有订阅摸鱼日历", parse_mode=ParseMode.HTML
                )
            moyu_sub.del_id(message.chat.id)
            await message.edit("你已经成功退订了摸鱼日历")
        else:
            await edit_delete(message, "❌ 权限不足，无法退订摸鱼日历", parse_mode=ParseMode.HTML)
