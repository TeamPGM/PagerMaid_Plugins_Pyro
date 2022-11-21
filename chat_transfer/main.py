""" PagerMaid module that 群组/频道迁移 """

import csv

from asyncio import sleep
from os import sep
from typing import List

from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, UsernameNotOccupied, UsernameInvalid
from pyrogram.types import Chat

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove


async def export_chat_to_csv():
    chats: List[Chat] = []
    async for dialog in bot.get_dialogs():
        chat_type = dialog.chat.type
        if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
            chats.append(dialog.chat)
    with open("chats.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "id", "username", "members"])
        for chat in chats:
            writer.writerow([chat.title, chat.id, chat.username or "", chat.members_count])
    return len(chats)


async def join_chat(username: str):
    await bot.join_chat(username)


async def join_chat_from_csv(file_name):
    success = 0
    failed = 0
    processed = 0
    need_import = []
    with open(file_name, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "name":
                continue
            if row[2] != "":
                need_import.insert(0, row[2])
            processed += 1
    for i in need_import:
        try:
            await join_chat(i)
            success += 1
        except (UsernameNotOccupied, UsernameInvalid):
            failed += 1
        except FloodWait as e:
            await sleep(e.value)
            await join_chat(row[2])
            success += 1
        except Exception:
            failed += 1
    return success, failed, processed


@listener(command="chat_transfer",
          need_admin=True,
          parameters="导出/导入",
          description="导出、导入已加入的群组/频道（仅可导入公开群组/频道）")
async def chat_transfer(message: Message):
    if message.arguments == "导出":
        message: Message = await message.edit("导出中...")
        num = await export_chat_to_csv()
        if num:
            await bot.send_document(
                message.chat.id,
                "chats.csv",
                caption=f"对话导出文件，成功导出了 {num} 个群组/频道",
                thumb=f"pagermaid{sep}assets{sep}logo.jpg",
                reply_to_message_id=message.reply_to_top_message_id,
            )
            safe_remove("chats.csv")
            await message.safe_delete()
        else:
            await message.edit("没有群组/频道可以导出")
    elif message.arguments == "导入":
        reply = message.reply_to_message
        if not reply:
            return await message.edit("❌ 请回复对话导出文件")
        if not reply.document:
            return await message.edit("❌ 请回复对话导出文件")
        if not reply.document.file_name.endswith(".csv"):
            return await message.edit("❌ 请回复对话导出文件")
        message = await message.edit("导入中")
        file_name = await reply.download()
        success, failed, processed = await join_chat_from_csv(file_name)
        safe_remove(file_name)
        await message.edit(f"处理了 {processed} 条记录，导入成功 {success} 个群组/频道，失败 {failed} 个群组/频道")
    else:
        await message.edit("❌ 参数错误，请选择 `导出` 或 `导入`")
