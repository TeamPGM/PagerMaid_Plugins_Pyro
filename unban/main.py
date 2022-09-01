from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChatAdminRequired, FloodWait, PeerIdInvalid, UsernameInvalid, UserNotParticipant
from pyrogram.types import Chat

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.enums import Client, Message
from pagermaid.utils import lang


async def check_uid(chat: Chat, uid: str):
    member = None
    try:
        uid = int(uid)
        member = await bot.get_chat_member(chat.id, uid)
    except ValueError:
        try:
            chat = await bot.get_chat(uid)
            uid = chat.id
        except PeerIdInvalid:
            member = await bot.get_chat_member(chat.id, uid)
            uid = member.user.id
    if not member:
        member = await bot.get_chat_member(chat.id, uid)
    return uid, member


async def get_uid(chat: Chat, message: Message):
    uid = None
    member = None
    if reply := message.reply_to_message:
        if sender := reply.from_user:
            uid = sender.id
        if sender := reply.sender_chat:
            uid = sender.id
        member = await bot.get_chat_member(chat.id, uid)
    elif len(message.parameter) == 1:
        uid, member = await check_uid(chat, message.arguments)
    return uid, member


@listener(command="unban",
          description="解除封禁一位用户",
          need_admin=True,
          groups_only=True,
          parameters="<reply|id|username>")
async def unban(client: Client, message: Message):
    chat = message.chat
    try:
        uid, member = await get_uid(chat, message)
    except (ValueError, PeerIdInvalid, UsernameInvalid, FloodWait):
        return await message.edit(lang("arg_error"))
    except UserNotParticipant:
        return await message.edit("此用户未被限制。")
    if not uid:
        return await message.edit(lang("arg_error"))
    if uid == chat.id:
        return await message.edit(lang("arg_error"))
    try:
        if not member:
            member = await bot.get_chat_member(chat.id, uid)
        if member.status in [ChatMemberStatus.RESTRICTED, ChatMemberStatus.BANNED]:
            await client.unban_chat_member(chat.id, uid)
        else:
            return await message.edit("此用户未被限制。")
    except UserNotParticipant:
        return await message.edit("此用户未被限制。")
    except ChatAdminRequired:
        return await message.edit(lang("sb_no_per"))
    except Exception as e:
        return await message.edit(f"出现错误：{e}")
    await message.edit("已解封此用户。")
