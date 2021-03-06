import contextlib
from asyncio import sleep

from pyrogram.enums import ChatMemberStatus
from pyrogram import filters
from pyrogram.errors import ChatAdminRequired, FloodWait, UserAdminInvalid, PeerIdInvalid

from datetime import datetime, timedelta

from pagermaid.listener import listener
from pagermaid.enums import Message, Client
from pagermaid.services import bot


async def check_self_and_from(message: Message):
    cid = message.chat.id
    data = await bot.get_chat_member(cid, (await bot.get_me()).id)
    if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return False
    if message.outgoing:
        return True
    if not message.from_user:
        return False
    data = await bot.get_chat_member(cid, message.from_user.id)
    if data.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return False
    return True


async def kick_chat_member(cid, uid, only_search: bool = False):
    if only_search:
        return
    with contextlib.suppress(UserAdminInvalid, PeerIdInvalid):
        await bot.ban_chat_member(
            cid,
            uid,
            datetime.now() + timedelta(minutes=5))


async def process_clean_member(message: Message, mode: str, day: int, only_search: bool = False):
    member_count = 0
    try:
        async for member in bot.get_chat_members(message.chat.id):
            if mode == "1" and member.user.last_online_date and \
                    member.user.last_online_date < datetime.now() - timedelta(days=day):
                member_count += 1
                await kick_chat_member(message.chat.id, member.user.id, only_search)
            if mode == "2":
                now = datetime.now() - timedelta(days=day)
                async for message in bot.search_messages(message.chat.id, limit=1, from_user=member.user.id):
                    if message.date < now:
                        member_count += 1
                        await kick_chat_member(message.chat.id, member.user.id, only_search)
            elif mode == "3":
                try:
                    count = await bot.search_messages_count(message.chat.id, from_user=member.user.id)
                except PeerIdInvalid:
                    continue
                if count < day:
                    member_count += 1
                    await kick_chat_member(message.chat.id, member.user.id, only_search)
            if mode == "4" and member.user.is_deleted:
                member_count += 1
                await kick_chat_member(message.chat.id, member.user.id, only_search)
        if not only_search:
            await message.edit(f'??????????????? `{member_count}` ??????')
        else:
            await message.edit(f'???????????? `{member_count}` ??????')
    except ChatAdminRequired:
        await message.edit("??????????????????????????????????????????")
    except FloodWait:
        return await message.edit('??????????????????????????? TG ??????????????????')


@listener(command="clean_member",
          need_admin=True,
          groups_only=True,
          description="???????????????????????????")
async def clean_member(client: Client, message: Message):
    if not await check_self_and_from(message):
        return await message.edit("?????????????????????????????????????????????")
    uid = message.from_user.id
    mode, day = "0", 0
    reply = await message.edit("????????????????????????\n\n"
                               "1. ????????????????????????\n"
                               "2. ??????????????????????????????????????????\n"
                               "3. ??????????????????\n"
                               "4. ????????????\n")
    try:
        async with client.conversation(message.chat.id, filters=filters.user(uid)) as conv:
            await sleep(1)
            res: Message = await conv.get_response()
            mode = res.text
            await res.safe_delete()
            if mode in ["1", "2"]:
                await res.safe_delete()
                await reply.edit("????????????????????????")
                await sleep(1)
                res = await conv.get_response()
                day = max(int(res.text), 7)
                await res.safe_delete()
            elif mode == "3":
                await res.safe_delete()
                await reply.edit("??????????????????????????????????????????")
                await sleep(1)
                res = await conv.get_response()
                day = int(res.text)
                await res.safe_delete()
            elif mode != "4":
                raise ValueError("??????????????????")
            await reply.edit("?????????????????????")
            await sleep(1)
            res = await conv.get_response()
            only_search = res.text == "??????"
            await res.safe_delete()
    except ValueError as e:
        return await reply.edit(f"{e}")
    await reply.edit("????????????????????????")
    await process_clean_member(reply, mode, day, only_search)
