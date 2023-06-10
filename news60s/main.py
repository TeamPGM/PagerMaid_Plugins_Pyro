""" PagerMaid module that 60s 看世界新闻 """

from datetime import date, datetime, timedelta, timezone
from os import sep
from os.path import isfile
from typing import Optional

from pagermaid import scheduler
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.services import bot, client
from pagermaid.sub_utils import Sub
from pagermaid.utils import check_manage_subs, edit_delete
from pyrogram.enums.parse_mode import ParseMode

CACHE_PATH = f"data{sep}news60s.png"

news60s_sub = Sub("news60s")
news60s_cache_time: Optional[date] = None


async def get_news60s() -> None:
    global news60s_cache_time
    today = datetime.now(timezone(timedelta(hours=8))).date()
    force_update = not isfile(CACHE_PATH)
    if news60s_cache_time == today and not force_update:
        return
    resp = await client.get("https://api.emoao.com/api/60s?type=json")
    res = resp.json()
    assert res["msg"] == "success", f"API 返回错误: {res['code']} ({res['msg']})"
    news_date = datetime.strptime(res["data"]["date"], "%Y-%m-%d").date()
    if news_date == news60s_cache_time and not force_update:
        return
    image = await client.get(res["data"]["image"])
    with open(CACHE_PATH, "wb") as fp:
        fp.write(image.content)
    news60s_cache_time = today


async def push_news60s(gid: int) -> None:
    if isfile(CACHE_PATH):
        await bot.send_photo(gid, CACHE_PATH)


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
    description="查看 60s 看世界新闻，支持订阅/退订每天上午八点定时发送",
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
