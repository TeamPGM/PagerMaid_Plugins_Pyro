""" PagerMaid module that 摸鱼日历 """

from os import sep

from pyrogram import Client
from pagermaid import scheduler
from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.utils import client, Message
from pagermaid.sub_utils import Sub

moyu_sub = Sub("moyu")


async def get_calendar() -> None:
    resp = await client.get("https://api.j4u.ink/proxy/remote/moyu.json")
    if resp.is_error:
        raise ValueError(f"摸鱼日历获取失败，错误码：{resp.status_code}")
    content = resp.json()
    url = content.get("data", {}).get("moyu_url", "")
    if not url:
        raise ValueError("摸鱼日历获取失败，无法获取摸鱼日历链接")
    resp = await client.get(url, follow_redirects=True)
    with open(f"data{sep}moyu.png", "wb") as f:
        f.write(resp.content)


async def push_moyu(gid: int) -> None:
    await bot.send_photo(
        gid,
        f"data{sep}moyu.png",
    )


@scheduler.scheduled_job("cron", hour="8", id="moyu.push")
async def calendar_subscribe() -> None:
    await get_calendar()
    for gid in moyu_sub.get_subs():
        try:
            await push_moyu(gid)
        except Exception as e:  # noqa
            moyu_sub.del_id(gid)


@listener(command="moyu",
          parameters="订阅/退订",
          description="查看今日摸鱼日历，支持订阅/退订每天上午八点定时发送")
async def moyu(_: Client, message: Message):
    """ 摸鱼日历 """
    if not message.arguments:
        try:
            await get_calendar()
        except ValueError as e:
            return await message.edit(e.__str__())
        await message.safe_delete()
        await push_moyu(message.chat.id)
    elif message.arguments == "订阅":
        if moyu_sub.check_id(message.chat.id):
            return await message.edit("你已经订阅了摸鱼日历")
        moyu_sub.add_id(message.chat.id)
        await message.edit("你已经成功订阅了摸鱼日历")
    elif message.arguments == "退订":
        if not moyu_sub.check_id(message.chat.id):
            return await message.edit("你还没有订阅摸鱼日历")
        moyu_sub.del_id(message.chat.id)
        await message.edit("你已经成功退订了摸鱼日历")
