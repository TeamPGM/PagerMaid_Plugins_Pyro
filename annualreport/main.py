# yapppbc
# Hello 2023

from os.path import getmtime
from datetime import datetime
from time import time

from pyrogram.enums import ChatType
from pyrogram.raw.functions.contacts import GetBlocked
from pyrogram.raw.types.contacts import BlockedSlice

from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient, Client
from pagermaid.modules import __list_plugins
from pagermaid.services import bot, sqlite


async def get_chat_count():
    private, group, bots, channel = 0, 0, 0, 0
    for dialog in await bot.get_dialogs_list():
        if dialog.chat.type == ChatType.BOT:
            bots += 1
        if dialog.chat.type == ChatType.CHANNEL:
            channel += 1
        if dialog.chat.type == ChatType.GROUP or ChatType.SUPERGROUP:
            group += 1
        if dialog.chat.type == ChatType.PRIVATE:
            private += 1
    return private, group, bots, channel


async def get_blocked_count():
    blocked = await bot.invoke(GetBlocked(offset=0, limit=1))
    if isinstance(blocked, BlockedSlice):
        return blocked.count
    elif blocked.users:
        return len(blocked.users)
    else:
        return 0


async def get_hitokoto(request: AsyncClient):
    try:
        htk = (await request.get("https://v1.hitokoto.cn/?charset=utf-8")).json()
        text = f"\"{htk['hitokoto']}\" —— "
        if htk["from_who"]:
            text += f"{htk['from_who']}"
        if htk["from"]:
            text += f"「{htk['from']}」"
    except Exception:
        text = '"用代码表达言语的魅力，用代码书写山河的壮丽。" —— 一言「一言开发者中心」'
    return text


async def get_year() -> str:
    now = datetime.now()
    year = now.year
    if now.month == 1:
        year -= 1
    return str(year)


@listener(command="annualreport", description="TG年度报告")
async def annualreport(client: Client, message: Message, request: AsyncClient):
    await message.edit("加载中请稍候。。。")
    year = await get_year()
    private, group, bots, channel = await get_chat_count()
    days = int((time() - getmtime("LICENSE")) / 86400)
    plg = sorted(__list_plugins())
    blocked = await get_blocked_count()
    blt = "你的账户真的很干净" if blocked < 20 else "愿明年的spam少一些"
    u = await client.get_me()
    if u.username:
        user = f"@{u.username}"
    elif u.last_name:
        user = f"{u.first_name} {u.last_name}"
    else:
        user = u.first_name
    pre = "你已成为TG大会员用户,不知遗产分到没有" if u.is_premium else ""
    pmct = ""
    if pmc := sqlite.get("pmcaptcha", {}):
        pmcu = "" if "pmcaptcha" in plg else "不过此插件已经被卸载了,是spam变少了吗?\n"
        pmct = (
            f'pmcaptcha 已帮助你拦截了 {pmc.get("banned", 0)} 次私聊\n你的清净由 pagermaid 守护\n{pmcu}'
        )
    htks = await get_hitokoto(request)
    msg = f"""{user} 的年度报告
{year} 一路上,你充实而满足
此Pagermaid-Pyro实例陪伴了你的TG {days} 天,安装了 {len(plg)} 个插件
为你的TG使用体验增光添彩

每次遇见,皆需万般幸运
你邂逅了 {channel} 个频道, {group} 个群组, 遇见了 {private} 个有趣的灵魂, 使用了 {bots} 个机器人
愿你的生活每天都像庆典一样开心

你的黑名单里有 {blocked} 人
{blt}
{pmct}
{pre}
{htks}"""
    await message.edit(msg)
