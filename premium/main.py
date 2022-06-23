# -*- coding: UTF-8 -*-
'''
@File    ：main.py
@Author  ：汐洛 @guimc233
@Date    ：2022/6/23 2:49
'''

from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, client
from pyrogram.enums import ChatMemberStatus, ParseMode


@listener(command="premium",
          description="分遗产咯")
async def premium(bot: Client, context: Message):
    context = await context.edit("Please wait...")
    premium_users = 0
    users = 0
    premium_admins = 0
    admins = 0
    dc_ids = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "failed": 0}
    async for m in bot.get_chat_members(context.chat.id):
        if not m.user.is_bot and not m.user.is_deleted:
            users += 1
            try:
                dc_ids[str(m.user.dc_id)] += 1
            except:
                dc_ids["failed"] += 1
            if m.user.is_premium:
                premium_users += 1
                if m.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                    premium_admins += 1
            if m.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
                admins += 1
    admin_part = 0
    if admins == 0:
        admin_part = "这个群没有管理吗???"
    else:
        admin_part = round((premium_admins/admins)*100, 2)
    await context.edit(f"""**分遗产咯**

管理员:
> 大会员: **{premium_admins}** / 总管理数: **{admins}** 分遗产占比: **{admin_part}%**

用户:
> 大会员: **{premium_users}** / 总用户数: **{users}** 分遗产占比: **{round((premium_users/users)*100, 2)}%**""", parse_mode = ParseMode.MARKDOWN)
