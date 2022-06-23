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
    await context.edit("Please wait...")
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
    await context.delete()
    admin_part = 0
    if admins == 0:
        admin_part = "这个群没有管理吗???"
    else:
        admin_part = round((premium_admins/admins)*100, 2)
    await bot.send_message(context.chat.id, f"""**分遗产咯**

管理员:
> 大会员: **{premium_admins}** / 总管理数: **{admins}** 分遗产占比: **{admin_part}%**

用户:
> 大会员: **{premium_users}** / 总用户数: **{users}** 分遗产占比: **{round((premium_users/users)*100, 2)}%**""", parse_mode = ParseMode.MARKDOWN)

@listener(command="dc",
          description="查看本群dc分布, 查看你回复的人在哪个dc")
async def dc(bot: Client, context: Message):
    await context.edit("Please wait...")
    if context.reply_to_message:
        user = (
            context.reply_to_message.from_user
            or context.reply_to_message.sender_chat
        )

        if not user:
            return await context.edit("出错啦！")
        try:
            return await context.edit(f"您所在的位置: DC{user.dc_id}")
        except:
            return await context.edit("无法查询! 您是否设置了头像呢？我是否可以看到你的头像呢？")
    users = 0
    dc_ids = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "failed": 0}
    async for m in bot.get_chat_members(context.chat.id):
        if not m.user.is_bot and not m.user.is_deleted:
            users += 1
            try:
                dc_ids[str(m.user.dc_id)] += 1
            except:
                dc_ids["failed"] += 1
    await context.delete()
    await bot.send_message(context.chat.id, f"""DC:
> DC1用户: **{dc_ids["1"]}** 分遗产占比: **{round((dc_ids["1"]/users)*100, 2)}%**
> DC2用户: **{dc_ids["2"]}** 分遗产占比: **{round((dc_ids["2"]/users)*100, 2)}%**
> DC3用户: **{dc_ids["3"]}** 分遗产占比: **{round((dc_ids["3"]/users)*100, 2)}%**
> DC4用户: **{dc_ids["4"]}** 分遗产占比: **{round((dc_ids["4"]/users)*100, 2)}%**
> DC5用户: **{dc_ids["5"]}** 分遗产占比: **{round((dc_ids["5"]/users)*100, 2)}%**
> 无法获取在哪个DC的用户: **{dc_ids["failed"]}**""", parse_mode = ParseMode.MARKDOWN)