""" PagerMaid module that 60s 看世界新闻 """

from os import sep
from os.path import isfile
from datetime import date
from typing import Optional

from pyrogram.enums.parse_mode import ParseMode
from pagermaid import scheduler
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import bot, client
from pagermaid.utils import edit_delete, check_manage_subs
from pagermaid.single_utils import safe_remove
from pagermaid.sub_utils import Sub

news60s_sub = Sub("news60s")
news60s_cache_time: Optional[date] = None


async def get_news60s() -> None:
    global news60s_cache_time
    if news60s_cache_time == date.today() and isfile(f"data{sep}news60s.png"):
        return
    resp = await client.get("https://api.emoao.com/api/60s", follow_redirects=True)
    if resp.is_error:
        raise ValueError(f"获取失败，错误码：{resp.status_code}")
    news60s_cache_time = date.today()
    safe_remove(f"data{sep}news60s.png")
    with open(f"data{sep}news60s.png", "wb") as f:
        f.write(resp.content)


async def push_news60s(gid: int) -> None:
    if isfile(f"data{sep}news60s.png"):
        await bot.send_photo(
            gid,
            f"data{sep}news60s.png"
        )


@scheduler.scheduled_job("cron", hour="8", id="news60s.push")
async def news60s_subscribe() -> None:
    await get_news60s()
    for gid in news60s_sub.get_subs():
        try:
            await push_news60s(gid)
        except Exception as e:  # noqa
            news60s_sub.del_id(gid)


@listener(
    command="news60s",
    parameters="订阅/退订",
    description="查看 60s 看世界新闻，支持订阅/退订每天上午八点定时发送"
)
async def news60s(message: Message):
    if not message.arguments:
        try:
            await get_news60s()
        except ValueError as e:
            return await message.edit(e.__str__())
        await message.safe_delete()
        await push_news60s(message.chat.id)
    elif message.arguments == "订阅":
        if check_manage_subs(message):
            if news60s_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你已经订阅了 60s 看世界新闻", parse_mode=ParseMode.HTML)
            news60s_sub.add_id(message.chat.id)
            await message.edit("你已经成功订阅了 60s 看世界新闻")
        else:
            await edit_delete(message, "❌ 权限不足，无法订阅 60s 看世界新闻", parse_mode=ParseMode.HTML)
    elif message.arguments == "退订":
        if check_manage_subs(message):
            if not news60s_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你还没有订阅 60s 看世界新闻", parse_mode=ParseMode.HTML)
            news60s_sub.del_id(message.chat.id)
            await message.edit("你已经成功退订了 60s 看世界新闻")
        else:
            await edit_delete(message, "❌ 权限不足，无法退订 60s 看世界新闻", parse_mode=ParseMode.HTML)
