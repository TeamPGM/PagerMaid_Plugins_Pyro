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


async def process_old_sticker_set(sticker_set: str):
    pack: StickerSet = await get_pack(sticker_set)
    hash_map = {}
    for i in pack.packs:
        for j in i.documents:
            hash_map[j] = i.emoticon
    stickers = [
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
    return stickers


@listener(
    command="cut_sticker_set",
    parameters="旧的贴纸包用户名 贴纸包用户名 开始,结束 贴纸包名称",
    description="剪切某个贴纸包",
)
async def copy_sticker_set(message: Message):
    if len(message.parameter) < 4:
        return await message.edit(
            "请指定贴纸包链接和贴纸包名称，例如 <code>xxx xxx_sticker 1,120 xxxx 的贴纸包</code>"
        )
    old_set_name = message.parameter[0]
    set_name = message.parameter[1]
    try:
        start, end = map(int, message.parameter[2].split(","))
    except ValueError:
        return await message.edit("开始和结束参数必须为数字")
    name = " ".join(message.parameter[3:])
    try:
        stickers = await process_old_sticker_set(old_set_name)
        stickers = stickers[start - 1 : end]
        await create_sticker_set(set_name, name, stickers)
    except Exception as e:
        return await message.edit(f"剪切贴纸包失败：{e}")
    await message.edit(
        f'剪切贴纸包成功 <a href="https://t.me/addstickers/{set_name}">{name}</a>'
    )
