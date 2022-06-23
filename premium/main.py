# -*- coding: UTF-8 -*-
'''
@File    ：main.py
@Author  ：汐洛 @guimc233
@Date    ：2022/6/23 21:57
'''

from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, client
from pyrogram.enums import ChatMemberStatus, ParseMode


@listener(command="premium",
          description="分遗产咯")
async def premium(bot: Client, context: Message):
    context = await context.edit("Please wait...")
    premium_users = users = admins = premium_admins = bots_deleted = 0
    dc_ids = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "failed": 0}
    count = await bot.get_chat_members_count(context.chat.id)
    if count >= 10000 and context.arguments != "force":
        return await context.edit("太...太多人了... 我会...会...会坏掉的...\n\n如果您执意要运行的的话，您可以使用指令 ,premium force")
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
        else:
            bots_deleted += 1
    await context.edit(f"""**分遗产咯**

管理员:
> 大会员: **{premium_admins}** / 总管理数: **{admins}** 分遗产占比: **{round((premium_admins/admins)*100, 2) if admins != 0 else '你群管理员全死号?'}%**

用户:
> 大会员: **{premium_users}** / 总用户数: **{users}** 分遗产占比: **{round((premium_users/users)*100, 2)}%**

> 已自动过滤掉 **{bots_deleted}** 个 Bot / 死号

{'***请注意: 由于tg限制 我们只能遍历前10k人 此次获得到的数据并不完整***' if count >= 10000 else ''}""", parse_mode = ParseMode.MARKDOWN)
