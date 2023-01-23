""" PagerMaid module for different ways to avoid users. """
import contextlib
from asyncio import sleep

from pyrogram import ContinuePropagation
from pyrogram.errors import FloodWait
from pyrogram.raw.base import Update
from pyrogram.raw.functions.messages import ReadReactions
from pyrogram.raw.types import UpdateMessageReactions, PeerChannel, PeerChat, PeerUser

from pagermaid.services import bot
from pagermaid.sub_utils import Sub
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.utils import lang

no_reactions_sub = Sub("no_reactions")


@listener(command="no_reactions",
          description="自动已读某个对话的消息表态",
          parameters="[true|false|status]")
async def no_reactions(_: Client, message: Message):
    if len(message.parameter) != 1:
        await message.edit(f"[no_reactions] {lang('error_prefix')}{lang('arg_error')}")
        return
    status = message.parameter[0].lower()
    if status == "true":
        if no_reactions_sub.add_id(message.chat.id):
            return await message.edit("[no_reactions] 成功在这个对话开启")
        else:
            return await message.edit("[no_reactions] 这个对话已经开启了")
    elif status == "false":
        if no_reactions_sub.del_id(message.chat.id):
            return await message.edit("[no_reactions] 成功在这个对话关闭")
        else:
            return await message.edit("[no_reactions] 这个对话未开启")
    elif message.parameter[0] == "status":
        if no_reactions_sub.check_id(message.chat.id):
            await message.edit("[no_reactions] 这个对话已经开启了")
        else:
            await message.edit("[no_reactions] 这个对话未开启")
    else:
        await message.edit(f"[no_reactions] {lang('error_prefix')}{lang('arg_error')}")


async def read_reactions(cid: int, top_msg_id: int):
    with contextlib.suppress(Exception):
        await bot.invoke(
            ReadReactions(
                peer=await bot.resolve_peer(cid),
                top_msg_id=top_msg_id,
            )
        )


@bot.on_raw_update()
async def no_reactions_handler(client: Client, update: Update, _, __: dict):
    while True:
        try:
            if not isinstance(update, UpdateMessageReactions):
                raise ContinuePropagation

            # Basic data
            if isinstance(update.peer, PeerChannel):
                chat_id = int(f"-100{update.peer.channel_id}")
            elif isinstance(update.peer, PeerChat):
                chat_id = update.peer.chat_id
            elif isinstance(update.peer, PeerUser):
                chat_id = update.peer.user_id
            else:
                raise ContinuePropagation

            # Check if open
            if not no_reactions_sub.check_id(chat_id):
                raise ContinuePropagation

            # Read reactions
            await client.invoke(
                ReadReactions(
                    peer=await client.resolve_peer(chat_id),
                    top_msg_id=update.top_msg_id,
                )
            )
            raise ContinuePropagation
        except FloodWait as e:
            await sleep(e.value)
        except BaseException as e:
            raise ContinuePropagation from e
