from asyncio import sleep

from pyrogram.enums import ChatType
from pyrogram.errors import ChatAdminRequired, FloodWait, PeerIdInvalid, UserAdminInvalid, UsernameInvalid
from pyrogram.types import Chat

from pagermaid import log, bot
from pagermaid.listener import listener
from pagermaid.single_utils import Message
from pagermaid.utils import lang


def mention_group(chat: Chat):
    return f'<a href="https://t.me/{chat.username}">{chat.title}</a>' if chat.username else f'<code>{chat.title}</code>'


async def ban_one(chat: Chat, uid):
    await bot.ban_chat_member(chat.id, uid)


async def delete_all_messages(chat: Chat, uid):
    await bot.delete_user_history(chat.id, uid)


async def check_uid(uid: str):
    channel = False
    try:
        uid = int(uid)
        if uid < 0:
            channel = True
        await bot.get_chat(uid)
    except ValueError:
        chat = await bot.get_chat(uid)
        uid = chat.id
        if chat.type in [ChatType.CHANNEL, ChatType.SUPERGROUP, ChatType.GROUP]:
            channel = True
    return uid, channel


async def get_uid(message: Message):
    uid = None
    channel = False
    delete_all = True
    if reply := message.reply_to_message:
        if sender := reply.from_user:
            uid = sender.id
        if sender := reply.sender_chat:
            uid = sender.id
            channel = True
        if message.arguments:
            delete_all = False
    elif len(message.parameter) == 2:
        uid, channel = await check_uid(message.parameter[0])
        delete_all = False
    elif len(message.parameter) == 1:
        uid, channel = await check_uid(message.arguments)
    return uid, channel, delete_all


@listener(command="sb",
          description=lang('sb_des'),
          need_admin=True,
          parameters="<reply|id|username> <do_not_del_all>")
async def super_ban(message: Message):
    chat = message.chat
    try:
        uid, channel, delete_all = await get_uid(message)
    except (ValueError, PeerIdInvalid, UsernameInvalid, FloodWait):
        return await message.edit(lang("arg_error"))
    if not uid:
        return await message.edit(lang("arg_error"))
    if channel:
        if uid == chat.id:
            return await message.edit(lang("arg_error"))
        try:
            await ban_one(chat, uid)
        except ChatAdminRequired:
            return await message.edit(lang("sb_no_per"))
        except Exception as e:
            return await message.edit(f"出现错误：{e}")
        return await message.edit(lang("sb_channel"))
    common = await bot.get_common_chats(uid)
    count, groups = 0, []
    for i in common:
        try:
            await ban_one(i, uid)
            if delete_all:
                await delete_all_messages(i, uid)
            count += 1
            groups.append(mention_group(i))
        except ChatAdminRequired:
            continue
        except UserAdminInvalid:
            continue
        except FloodWait as e:
            await sleep(e.value)
            await ban_one(i, uid)
            if delete_all:
                await delete_all_messages(i, uid)
            count += 1
            groups.append(mention_group(i))
        except Exception:  # noqa
            pass
    user = await bot.get_users(uid)
    if count == 0:
        text = f'{lang("sb_no")} {user.mention}'
    else:
        text = f'{lang("sb_per")} {count} {lang("sb_in")} {user.mention}'
    await message.edit(text)
    groups = f'\n{lang("sb_pro")}\n' + "\n".join(groups) if groups else ''
    await log(f'{text}\nuid: `{uid}` {groups}')
