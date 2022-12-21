# yapppbc
# Hello 2023

from os.path import getmtime, exists
from os import listdir
from time import time
from pyrogram.enums import ChatType
from pyrogram.raw.functions.contacts import GetBlocked
from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient, Client
from pagermaid.services import bot
from pagermaid.single_utils import sqlite


@listener(command="annualreport", description="TG年度报告")
async def annualreport(client: Client, message: Message, request: AsyncClient):
    await message.edit("请稍候")
    private, group, bots, channel = 0, 0, 0, 0
    async for dialog in bot.get_dialogs():
        if dialog.chat.type == ChatType.BOT:
            bots += 1
        if dialog.chat.type == ChatType.CHANNEL:
            channel += 1
        if dialog.chat.type == ChatType.GROUP or ChatType.SUPERGROUP:
            group += 1
        if dialog.chat.type == ChatType.PRIVATE:
            private += 1
    days = int((time()-getmtime("LICENSE"))/86400)
    plg=len(listdir("./plugins"))
    blocked = (await client.invoke(GetBlocked(offset=0, limit=0))).count
    if blocked < 20:
        blt = "你的账户真的很干净"
    else:
        blt = f"愿{'明' if time()<1672502400 else '今'}年的spam少一些"
    u = await client.get_me()
    if u.username == None:
        user = u.first_name+" "+u.last_name
    else:
        user = "@"+u.username
    if u.is_premium:
        pre = '''
你已成为TG大会员用户,不知遗产分到没有

'''
    else:
        pre = ''
    pmc = sqlite.get("pmcaptcha", False)
    if pmc != False:
        if not exists("./plugins/pmcaptcha.py"):
            pmcu = "不过此插件已经被卸载了,是spam变少了吗?\n"
        else:
            pmcu = ""
        pmct = f'''
pmcaptcha已帮助你拦截了 {pmc["banned"]} 次私聊
你的清净,pagermaid守护
{pmcu}'''
    try:
        htk = (await request.get("https://v1.hitokoto.cn/?charset=utf-8")).json()
        htks = f"\"{htk['hitokoto']}\" —— {htk['from_who']}「{htk['from']}」"
    except:
        htks = "\"用代码表达言语的魅力，用代码书写山河的壮丽。\" —— 一言「一言开发者中心」"
    msg = f"""{user} 的年度报告
2022一路上,你充实而满足
此Pagermaid-Pyro实例陪伴了你的TG {days} 天,安装了 {plg} 个插件
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
