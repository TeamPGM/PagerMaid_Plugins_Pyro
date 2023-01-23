import contextlib

from pagermaid import log
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.scheduler import add_delete_message_job
from pagermaid.utils import alias_command


@listener(command="da",
          groups_only=True,
          need_admin=True,
          description="删除群内所有消息。（非群组管理员只删除自己的消息）",
          parameters="[true]")
async def da(bot: Client, message: Message):
    if message.arguments != "true":
        return await message.edit(f"[da] 呜呜呜，请执行 `,{alias_command('da')} true` 来删除所有消息。")
    await message.edit('[da] 正在删除所有消息 . . .')
    messages = []
    count = 0
    async for message in bot.get_chat_history(message.chat.id):
        messages.append(message.id)
        count += 1
        if count % 100 == 0:
            with contextlib.suppress(Exception):
                await bot.delete_messages(message.chat.id, messages)
            messages = []

    if messages:
        with contextlib.suppress(Exception):
            await bot.delete_messages(message.chat.id, messages)
    await log(f"批量删除了 {str(count)} 条消息。")
    with contextlib.suppress(Exception):
        reply = await bot.send_message(message.chat.id, f"批量删除了 {str(count)} 条消息。")
        add_delete_message_job(reply, delete_seconds=5)
