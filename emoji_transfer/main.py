""" PagerMaid module that Emoji 迁移 """

import csv

from asyncio import sleep
from os import sep

from pyrogram.errors import StickersetInvalid, FloodWait
from pyrogram.raw.functions.messages import GetEmojiStickers, UninstallStickerSet
from pyrogram.raw.functions.messages import InstallStickerSet
from pyrogram.raw.types import InputStickerSetShortName

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove


class NoStickerSetError(Exception):
    pass


async def export_sticker_to_csv():
    stickers = await bot.invoke(GetEmojiStickers(hash=0))
    if not stickers.sets:
        raise NoStickerSetError
    with open("emojis.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "short_name"])
        for sticker_set in stickers.sets:
            writer.writerow(
                [
                    sticker_set.title,
                    sticker_set.short_name,
                ]
            )
    return len(stickers.sets)


async def import_sticker(short_name):
    await bot.invoke(
        InstallStickerSet(
            stickerset=InputStickerSetShortName(short_name=short_name),
            archived=False,
        )
    )


async def remove_sticker(short_name):
    await bot.invoke(
        UninstallStickerSet(
            stickerset=InputStickerSetShortName(short_name=short_name),
        )
    )


async def import_sticker_from_csv(file_name):
    success = 0
    failed = 0
    need_import = []
    with open(file_name, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "name":
                continue
            need_import.insert(0, row[1])
    for i in need_import:
        try:
            await import_sticker(i)
            success += 1
        except StickersetInvalid:
            failed += 1
        except FloodWait as e:
            await sleep(e.value)
            await import_sticker(row[1])
            success += 1
        except Exception:
            failed += 1
    return success, failed


async def clear_sets():
    stickers = await bot.invoke(GetEmojiStickers(hash=0))
    if not stickers.sets:
        raise NoStickerSetError
    success = 0
    failed = 0
    for sticker_set in stickers.sets:
        try:
            await remove_sticker(sticker_set.short_name)
            success += 1
        except FloodWait as e:
            await sleep(e.value)
            await remove_sticker(sticker_set.short_name)
            failed += 1
        except Exception:
            failed += 1
    return success, failed


@listener(
    command="emoji_transfer",
    need_admin=True,
    parameters="导出/导入/清空",
    description="导出、导入、清空已安装的 Emoji 包",
)
async def emoji_transfer(message: Message):
    if message.arguments == "导出":
        try:
            num = await export_sticker_to_csv()
        except NoStickerSetError:
            return await message.edit("没有 Emoji 包可以导出")
        if num:
            await bot.send_document(
                message.chat.id,
                "emojis.csv",
                caption=f"Emoji 包导出文件，成功导出了 {num} 个 Emoji 包",
                thumb=f"pagermaid{sep}assets{sep}logo.jpg",
                reply_to_message_id=message.reply_to_top_message_id,
            )
            safe_remove("emojis.csv")
            await message.safe_delete()
        else:
            await message.edit("没有 Emoji 包可以导出")
    elif message.arguments == "导入":
        reply = message.reply_to_message
        if not reply:
            return await message.edit("❌ 请回复Emoji 包导出文件")
        if not reply.document:
            return await message.edit("❌ 请回复Emoji 包导出文件")
        if not reply.document.file_name.endswith(".csv"):
            return await message.edit("❌ 请回复Emoji 包导出文件")
        message = await message.edit("导入中")
        file_name = await reply.download()
        success, failed = await import_sticker_from_csv(file_name)
        safe_remove(file_name)
        await message.edit(f"导入成功 {success} 个Emoji 包，失败 {failed} 个Emoji 包")
    elif message.arguments == "清空":
        message = await message.edit("清空中")
        try:
            success, failed = await clear_sets()
        except NoStickerSetError:
            return await message.edit("没有Emoji 包可以清空")
        await message.edit(f"清空成功 {success} 个Emoji 包，失败 {failed} 个Emoji 包")
    else:
        await message.edit("❌ 参数错误，请选择 `导出` 或 `导入` 或 `清空`")
