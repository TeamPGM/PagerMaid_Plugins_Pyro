# -*- coding: UTF-8 -*-
"""
@File    ：main.py
@Author  ：汐洛 @guimc233
@Date    ：2022/6/23 2:49
"""

from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message
from pyrogram.enums import ParseMode


@listener(command="dc", description="查看本群dc分布, 查看你回复的人在哪个dc")
async def dc(bot: Client, context: Message):
    context = await context.edit("Please wait...")
    if context.reply_to_message:
        user = (
            context.reply_to_message.from_user or context.reply_to_message.sender_chat
        )
        if not user:
            return await context.edit("出错啦！")
        try:
            return await context.edit(f"您所在的位置: DC{user.dc_id}")
        except:
            return await context.edit("无法查询! 您是否设置了头像呢？我是否可以看到你的头像呢？")
    if context.chat.id > 0:
        try:
            user = await bot.get_users(context.chat.id)
            return await context.edit(f"他所在的位置: DC{user.dc_id}")
        except:
            return await context.edit("无法查询! 您是否设置了头像呢？我是否可以看到你的头像呢？")
    count = await bot.get_chat_members_count(context.chat.id)
    if count >= 10000 and context.arguments != "force":
        return await context.edit(
            "太...太多人了... 我会...会...会坏掉的...\n\n如果您执意要运行的的话，您可以使用指令 ,dc force"
        )
    users = bots = deleted = 0
    dc_ids = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "failed": 0}
    async for m in bot.get_chat_members(context.chat.id, limit=9999):
        if not m.user.is_bot and not m.user.is_deleted:
            users += 1
            try:
                dc_ids[str(m.user.dc_id)] += 1
            except:
                dc_ids["failed"] += 1
        elif m.user.is_bot:
            bots += 1
        else:
            deleted += 1
    await context.edit(
        f"""DC:
> DC1用户: **{dc_ids["1"]}** 分遗产占比: **{round((dc_ids["1"]/users)*100, 2)}%**
> DC2用户: **{dc_ids["2"]}** 分遗产占比: **{round((dc_ids["2"]/users)*100, 2)}%**
> DC3用户: **{dc_ids["3"]}** 分遗产占比: **{round((dc_ids["3"]/users)*100, 2)}%**
> DC4用户: **{dc_ids["4"]}** 分遗产占比: **{round((dc_ids["4"]/users)*100, 2)}%**
> DC5用户: **{dc_ids["5"]}** 分遗产占比: **{round((dc_ids["5"]/users)*100, 2)}%**
> 无法获取在哪个DC的用户: **{dc_ids["failed"]}**
> 已自动过滤掉 **{bots}** 个 Bot, **{deleted}** 个 死号

{'***请注意: 由于tg限制 我们只能遍历前10k人 此次获得到的数据并不完整***' if count >= 10000 else ''}""",
        parse_mode=ParseMode.MARKDOWN,
    )
