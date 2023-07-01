""" PagerMaid module that 历史上的今天 """

from pyrogram.enums import ParseMode

from pagermaid import scheduler, bot
from pagermaid.listener import listener
from pagermaid.utils import client, Message, check_manage_subs, edit_delete
from pagermaid.sub_utils import Sub

today_in_history_sub = Sub("today_in_history")


async def get_history() -> str:
    resp = await client.get("https://api.iyk0.com/lishi/")
    if resp.is_error:
        raise ValueError(f"历史上的今天 数据获取失败，错误码：{resp.status_code}")
    content = resp.json()
    text = f"历史上的今天 {list(content.keys())[0]}\n\n"
    for item in list(content.values())[0]:
        text += f"{item['year']} {item['title']}"
    return text


@scheduler.scheduled_job("cron", hour="8", id="today_in_history.push")
async def today_in_history_subscribe() -> None:
    text = await get_history()
    for gid in today_in_history_sub.get_subs():
        try:
            await bot.send_message(gid, text)
        except Exception as e:  # noqa
            today_in_history_sub.del_id(gid)


@listener(
    command="today_in_history",
    parameters="订阅/退订",
    description="查看历史上的今天，支持订阅/退订每天上午八点定时发送",
)
async def today_in_history(message: Message):
    if not message.arguments:
        try:
            text = await get_history()
        except ValueError as e:
            return await message.edit(e.__str__())
        await message.edit(text)
    elif message.arguments == "订阅":
        if check_manage_subs(message):
            if today_in_history_sub.check_id(message.chat.id):
                return await edit_delete(
                    message, "❌ 你已经订阅了历史上的今天", parse_mode=ParseMode.HTML
                )
            today_in_history_sub.add_id(message.chat.id)
            await message.edit("你已经成功订阅了历史上的今天")
        else:
            await edit_delete(message, "❌ 权限不足，无法订阅历史上的今天", parse_mode=ParseMode.HTML)
    elif message.arguments == "退订":
        if check_manage_subs(message):
            if not today_in_history_sub.check_id(message.chat.id):
                return await edit_delete(
                    message, "❌ 你还没有订阅摸历史上的今天", parse_mode=ParseMode.HTML
                )
            today_in_history_sub.del_id(message.chat.id)
            await message.edit("你已经成功退订了历史上的今天")
        else:
            await edit_delete(message, "❌ 权限不足，无法退订历史上的今天", parse_mode=ParseMode.HTML)
