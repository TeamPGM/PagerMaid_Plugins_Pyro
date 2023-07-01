from asyncio import sleep

from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait
from pyrogram.raw.functions.messages import DeleteHistory

from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import bot


async def delete_private_chat(cid: int):
    try:
        await bot.invoke(
            DeleteHistory(
                just_clear=False,
                revoke=False,
                peer=await bot.resolve_peer(cid),
                max_id=0,
            )
        )
    except FloodWait as e:
        await sleep(e.value)
        await delete_private_chat(cid)
    except Exception:
        pass


@listener(
    command="clear_private_chat",
    need_admin=True,
    description="通过指定关键词清除私聊",
    parameters="[关键词]",
)
async def clear_private_chat(message: Message):
    """通过指定关键词清除私聊记录"""
    if not message.arguments:
        await message.edit("请输入关键词来清除指定的私聊对话，为了保证速度，仅匹配每个对话的最后一条消息")
        return
    count = 0
    keywords = message.arguments.split(" ")
    message: Message = await message.edit("清除私聊对话中。。。")
    async for dialog in bot.get_dialogs():
        if dialog.chat.type != ChatType.PRIVATE:
            continue
        if dialog.top_message is None:
            continue
        if dialog.top_message.text is None:
            continue
        for i in keywords:
            if i in dialog.top_message.text:
                await delete_private_chat(dialog.chat.id)
                count += 1
                break
    await message.edit(f"成功清除了 {count} 个私聊对话")
