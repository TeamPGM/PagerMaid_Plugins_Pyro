import contextlib
from pagermaid.enums import Client, Message
from pagermaid.listener import listener


async def clear_sticker_func(bot: Client, cid: int, count: int):
    real_del = 0
    msgs = []
    async for message in bot.get_chat_history(cid):
        if message.sticker:
            msgs.append(message.id)
            real_del += 1
            if real_del >= count:
                break
        if len(msgs) >= 100:
            with contextlib.suppress(Exception):
                await bot.delete_messages(cid, msgs)
            msgs.clear()
    if len(msgs) > 0:
        with contextlib.suppress(Exception):
            await bot.delete_messages(cid, msgs)
    return real_del


@listener(
    command="clear_sticker",
    description="清理群组中的贴纸消息。",
    parameters="[需要清理的贴纸数]",
    groups_only=True,
)
async def clear_sticker(bot: Client, message: Message):
    count = message.obtain_message()
    if not count:
        await message.edit("请输入需要清理的贴纸数，例如 99999999")
        return
    try:
        count = int(count)
        if count < 1:
            raise ValueError
    except ValueError:
        await message.edit("请输入需要清理的贴纸数，例如 99999999")
        return
    msg = await message.edit("正在清理贴纸消息...")
    real_count = await clear_sticker_func(bot, message.chat.id, count)
    await msg.edit(f"已清理 {real_count} 条贴纸消息。")
    await msg.delay_delete()
