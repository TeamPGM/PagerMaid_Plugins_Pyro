from typing import List

from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.functions.stickers import CreateStickerSet
from pyrogram.raw.types import (
    InputStickerSetShortName,
    InputStickerSetItem,
    InputDocument,
)
from pyrogram.raw.types.messages import StickerSet

from pagermaid.listener import listener
from pagermaid.services import bot
from pagermaid.enums import Message


class NoStickerSetNameError(Exception):
    """
    Occurs when no username is provided
    """

    def __init__(self, string: str = "贴纸包不存在"):
        super().__init__(string)


async def get_pack(name: str):
    try:
        return await bot.invoke(
            GetStickerSet(stickerset=InputStickerSetShortName(short_name=name), hash=0)
        )
    except Exception as e:  # noqa
        raise NoStickerSetNameError() from e


async def create_sticker_set(
    sticker_set: str, title: str, stickers
):
    try:
        await bot.invoke(
            CreateStickerSet(
                user_id=await bot.resolve_peer("me"),
                title=title,
                short_name=sticker_set,
                stickers=stickers,
                software="pagermaid-pyro",
            )
        )
    except Exception as e:
        raise NoStickerSetNameError("贴纸包名称或者链接非法或者已被占用，请换一个") from e


async def process_old_sticker_set(sticker_sets: List[str]):
    stickers = []
    for idx, sticker_set in enumerate(sticker_sets):
        pack: StickerSet = await get_pack(sticker_set)
        hash_map = {}
        for i in pack.packs:
            for j in i.documents:
                hash_map[j] = i.emoticon
        _stickers = [
            InputStickerSetItem(
                document=InputDocument(
                    id=i.id,
                    access_hash=i.access_hash,
                    file_reference=i.file_reference,
                ),
                emoji=hash_map.get(i.id, "👀"),
            )
            for i in pack.documents
        ]
        if len(stickers) + len(_stickers) > 120:
            raise NoStickerSetNameError("贴纸包过多")
        stickers.extend(_stickers)
    return stickers


@listener(
    command="copy_sticker_set",
    parameters="旧的贴纸包用户名1,旧的贴纸包用户名2 贴纸包用户名 贴纸包名称",
    description="复制某个贴纸包",
)
async def copy_sticker_set(message: Message):
    if len(message.parameter) < 3:
        return await message.edit(
            "请指定贴纸包链接和贴纸包名称，例如 <code>xxx xxxx_sticker xxxx 的贴纸包</code>"
        )
    old_set_names = message.parameter[0].split(",")
    set_name = message.parameter[1]
    name = " ".join(message.parameter[2:])
    try:
        stickers = await process_old_sticker_set(old_set_names)
        await create_sticker_set(set_name, name, stickers)
    except Exception as e:
        return await message.edit(f"复制贴纸包失败：{e}")
    await message.edit(
        f'复制贴纸包成功 <a href="https://t.me/addstickers/{set_name}">{name}</a>'
    )
