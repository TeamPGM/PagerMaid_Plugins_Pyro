import secrets

from pagermaid import bot, scheduler
from pagermaid.listener import listener
from pagermaid.utils import Message, edit_delete, check_manage_subs
from pagermaid.sub_utils import Sub

everyday_greet_sub = Sub("everyday_greet")
everyday_greet_data = {
    "breakfast": [
        "早上7点啦，吃早餐啦！",
        "起床啦起床啦！现在还没起床的都是懒狗！",
        "哦哈哟米娜桑！今日も元気でね！🥳",
        "新的一天又是全气满满哦！",
        "一日之计在于晨，懒狗还不起床？"
    ],
    "lunch": [
        "中午12点啦，吃午餐啦！",
        "恰饭啦恰饭啦！再不去食堂就没吃的啦！",
        "中午还不恰点好的？整点碳水大餐嗯造吧！"
    ],
    "snack": [
        "下午三点了，饮茶了先！",
        "摸鱼时刻，整点恰滴先~",
        "做咩啊做，真给老板打工啊！快来摸鱼！"
    ],
    "dinner": [
        "下午6点了！不会真有人晚上加班恰外卖吧？",
        "下班咯，这不开造？",
        "当务之急是下班！"
    ],
    "midnight": [
        "晚上10点啦，整个夜宵犒劳自己吧！",
        "夜宵这不来个外卖？",
        "夜宵这不整点好的？"
    ],
}


async def everyday_do_greet(when: str):
    for gid in everyday_greet_sub.get_subs():
        msg = secrets.choice(everyday_greet_data[when])
        try:
            await bot.send_message(gid, msg)
        except Exception as e:  # noqa
            everyday_greet_sub.del_id(gid)


@scheduler.scheduled_job("cron", hour="7", id="everyday_greet.breakfast")
async def everyday_greet_breakfast() -> None:
    await everyday_do_greet("breakfast")


@scheduler.scheduled_job("cron", hour="12", id="everyday_greet.lunch")
async def everyday_greet_lunch() -> None:
    await everyday_do_greet("lunch")


@scheduler.scheduled_job("cron", hour="15", id="everyday_greet.snack")
async def everyday_greet_snack() -> None:
    await everyday_do_greet("snack")


@scheduler.scheduled_job("cron", hour="18", id="everyday_greet.dinner")
async def everyday_greet_dinner() -> None:
    await everyday_do_greet("dinner")


@scheduler.scheduled_job("cron", hour="22", id="everyday_greet.midnight")
async def everyday_greet_midnight() -> None:
    await everyday_do_greet("midnight")


@listener(command="everyday_greet",
          parameters="订阅/退订",
          groups_only=True,
          description="订阅/退订每日问候，仅支持群组")
async def everyday_greet(message: Message):
    if not message.arguments:
        return await message.edit("请输入 `订阅/退订` 参数")
    elif message.arguments == "订阅":
        if check_manage_subs(message):
            if everyday_greet_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你已经订阅了每日问候")
            everyday_greet_sub.add_id(message.chat.id)
            await message.edit("你已经成功订阅了每日问候")
        else:
            await edit_delete(message, "❌ 权限不足，无法订阅每日问候")
    elif message.arguments == "退订":
        if check_manage_subs(message):
            if not everyday_greet_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你还没有订阅每日问候")
            everyday_greet_sub.del_id(message.chat.id)
            await message.edit("你已经成功退订了每日问候")
        else:
            await edit_delete(message, "❌ 权限不足，无法退订每日问候")
    else:
        await message.edit("请输入 `订阅/退订` 参数")
