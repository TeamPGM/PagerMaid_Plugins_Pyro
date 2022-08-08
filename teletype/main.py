from asyncio import sleep
from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import lang, Message

@listener(is_plugin=False, incoming=True, command="teletype",
            description=lang('teletype_des'),
            parameters="<message>")
async def teletype(_: Client, context: Message):
    if not context.arguments:
        return await context.edit("出错了呜呜呜 ~ 空白的参数。")
    try:
        message = context.arguments
    except ValueError:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    interval = 0.05
    cursor = "█"
    buffer = ''
    msg = await context.edit(cursor)
    await sleep(interval)
    for character in message:
        buffer = f"{buffer}{character}"
        buffer_commit = f"{buffer}{cursor}"
        await msg.edit(buffer_commit)
        await sleep(interval)
        try:
            await msg.edit(buffer)
        except MessageNotModifiedError:
            pass
        await sleep(interval)
