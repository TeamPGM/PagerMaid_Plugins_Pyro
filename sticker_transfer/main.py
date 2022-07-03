""" PagerMaid module that 贴纸迁移 """

import csv

from asyncio import sleep
from os import sep

from pyrogram.errors import StickersetInvalid, FloodWait
from pyrogram.raw.functions.messages import GetAllStickers
from pyrogram.raw.functions.messages import InstallStickerSet
from pyrogram.raw.types import InputStickerSetShortName

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove


async def export_sticker_to_csv():
    stickers = await bot.invoke(GetAllStickers(hash=0))
    if not stickers.sets:
        return False
    with open("stickers.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "short_name", "is_masks", "is_animated", "is_video"])
        for sticker_set in stickers.sets:
            writer.writerow([sticker_set.title,
                             sticker_set.short_name,
                             sticker_set.archived if hasattr(sticker_set, "archived") else False,
                             sticker_set.animated if hasattr(sticker_set, "animated") else False,
                             sticker_set.videos if hasattr(sticker_set, "videos") else False, ])
    return len(stickers.sets)


async def import_sticker(short_name):
    await bot.invoke(InstallStickerSet(
        stickerset=InputStickerSetShortName(short_name=short_name),
        archived=False,
    ))


async def import_sticker_from_csv(file_name):
    success = 0
    failed = 0
    with open(file_name, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "name":
                continue
            try:
                await import_sticker(row[1])
                success += 1
            except StickersetInvalid:
                failed += 1
            except FloodWait as e:
                await sleep(e.value)
                await import_sticker(row[1])
                success += 1
    return success, failed


@listener(command="sticker_transfer",
          need_admin=True,
          parameters="导出/导入",
          description="导出、导入已安装的贴纸包")
async def sticker_transfer(message: Message):
    if message.arguments == "导出":
        num = await export_sticker_to_csv()
        if num:
            await bot.send_document(message.chat.id,
                                    "stickers.csv",
                                    caption=f"贴纸包导出文件，成功导出了 {num} 个贴纸包",
                                    thumb=f"pagermaid{sep}assets{sep}logo.jpg",)
            safe_remove("stickers.csv")
            await message.safe_delete()
        else:
            await message.edit("没有贴纸包可以导出")
    elif message.arguments == "导入":
        reply = message.reply_to_message
        if not reply:
            return await message.edit("❌ 请回复贴纸包导出文件")
        if not reply.document:
            return await message.edit("❌ 请回复贴纸包导出文件")
        if not reply.document.file_name.endswith(".csv"):
            return await message.edit("❌ 请回复贴纸包导出文件")
        message = await message.edit("导入中")
        file_name = await reply.download()
        success, failed = await import_sticker_from_csv(file_name)
        safe_remove(file_name)
        await message.edit(f"导入成功 {success} 个贴纸包，失败 {failed} 个贴纸包")
    else:
        await message.edit("❌ 参数错误，请选择 `导出` 或 `导入` ")
