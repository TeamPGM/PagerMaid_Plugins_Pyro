import asyncio
import shutil
from collections import defaultdict
import os
import zipfile

from pyrogram.enums import MessageEntityType
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.types import InputStickerSetShortName
from pyrogram.raw.types.messages import StickerSet
from pyrogram.types import Document, Sticker

from pagermaid import working_dir
from pagermaid.enums import Message, Client
from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove


async def download_stickers(bot: Client, message: Message, sticker: Sticker):
    try:
        sticker_set: StickerSet = await bot.invoke(
            GetStickerSet(stickerset=InputStickerSetShortName(short_name=sticker.set_name), hash=0))
    except Exception:  # noqa
        return await message.edit('回复的贴纸不存在于任何贴纸包中。')

    pack_file = os.path.join('data/sticker/', sticker_set.set.short_name, "pack.txt")

    if os.path.isfile(pack_file):
        os.remove(pack_file)
    emojis = defaultdict(str)
    for pack in sticker_set.packs:
        for document_id in pack.documents:
            emojis[document_id] += pack.emoticon
    file_ext_ns_ion = "webp"
    if sticker.is_video:
        file_ext_ns_ion = "mp4"
    elif sticker.is_animated:
        file_ext_ns_ion = "tgs"

    async def download(sticker_, emojis_, path, file):
        sticker_file = Document._parse(bot, sticker_, "sticker.webp")  # noqa
        await bot.download_media(sticker_file.file_id, file_name=os.path.join(path, file))

        with open(pack_file, "a") as f:
            f.write(f"{{'image_file': '{file}','emojis':{emojis_[sticker_.id]}}},")

    pending_tasks = [asyncio.ensure_future(
        download(document, emojis, f"data/sticker/{sticker_set.set.short_name}", f"{i:03d}.{file_ext_ns_ion}")
    ) for i, document in enumerate(sticker_set.documents)]

    message: Message = await message.edit(
        f"正在下载 {sticker_set.set.short_name} 中的 {sticker_set.set.count} 张贴纸。。。")

    while 1:
        done, pending_tasks = await asyncio.wait(pending_tasks, timeout=2.5, return_when=asyncio.FIRST_COMPLETED)
        if not pending_tasks:
            break
    await upload_sticker(bot, message, sticker_set)


async def upload_sticker(bot: Client, message: Message, sticker_set: StickerSet):
    await message.edit("下载完毕，打包上传中。")
    directory_name = sticker_set.set.short_name
    os.chdir("data/sticker/")
    zipf = zipfile.ZipFile(f"{directory_name}.zip", "w", zipfile.ZIP_DEFLATED)
    zipdir(directory_name, zipf)
    zipf.close()
    await bot.send_document(
        message.chat.id,
        f"{directory_name}.zip",
        caption=sticker_set.set.short_name,
        reply_to_message_id=message.reply_to_message_id
    )
    safe_remove(f"{directory_name}.zip")
    shutil.rmtree(directory_name)
    os.chdir(working_dir)
    await message.safe_delete()


async def get_custom_emojis(bot: Client, message: Message):
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.CUSTOM_EMOJI:
                try:
                    sticker = await bot.get_custom_emoji_stickers([entity.custom_emoji_id])
                except Exception:
                    return None
                return sticker[0] if sticker else None


@listener(command="getstickers",
          description="获取整个贴纸包的贴纸")
async def get_stickers(bot: Client, message: Message):
    if not os.path.isdir('data/sticker/'):
        os.makedirs('data/sticker/')
    if message.reply_to_message:
        sticker = message.reply_to_message.sticker or await get_custom_emojis(bot, message.reply_to_message)
    else:
        sticker = message.sticker or await get_custom_emojis(bot, message)
    if not sticker:
        return await message.edit("请回复一张贴纸。")
    if not sticker.set_name:
        return await message.edit("回复的贴纸不属于任何贴纸包。")
    await download_stickers(bot, message, sticker)


def zipdir(path, zip_):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip_.write(os.path.join(root, file))
            os.remove(os.path.join(root, file))
