from asyncio import sleep

from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified

from pagermaid.listener import listener
from pagermaid.utils import lang, Message


@listener(is_plugin=False, command="teletype",
          description=lang('teletype_des'),
          parameters="<message>")
async def teletype(message: Message):
    if not message.arguments:
        return await message.edit("出错了呜呜呜 ~ 空白的参数。")
    try:
        text = message.arguments
    except ValueError:
        await message.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    interval = 0.05
    cursor = "█"
    buffer = ''
    msg = await message.edit(cursor)
    await sleep(interval)
    for character in text:
        buffer = f"{buffer}{character}"
        buffer_commit = f"{buffer}{cursor}"
        await msg.edit(buffer_commit)
        await sleep(interval)
        try:
            await msg.edit(buffer)
        except MessageNotModified:
            pass
        except Exception:
            return
        await sleep(interval)
