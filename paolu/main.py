""" PagerMaid Plugins Paolu """

import contextlib

from pyrogram.types import ChatPermissions

from pagermaid.listener import listener
from pagermaid.enums import Client, Message
from pagermaid.scheduler import add_delete_message_job


@listener(command="paolu",
          groups_only=True,
          need_admin=True,
          description="⚠一键跑路 删除群内消息并禁言⚠")
async def pao_lu(bot: Client, message: Message):
    """一键跑路 删除群内消息并禁言"""
    with contextlib.suppress(Exception):
        await bot.set_chat_permissions(
            message.chat.id,
            permissions=ChatPermissions(
                can_send_messages=False,
            ))
    reply = await message.edit("[paolu] 处理中...")
    with contextlib.suppress(Exception):
        await bot.delete_messages(message.chat.id, list(range(1, message.id)))
    await reply.edit("[paolu] Finished")
    add_delete_message_job(reply, delete_seconds=10)
