# This plugin is a plugin of Pagermaid-Pyro.
# Copyright 2023 Guimc(xiluo@guimc.ltd), a member of BakaBotTeam, All rights reserved.
import os.path
import random
import tempfile
import traceback
import typing

from PIL import Image
from pyrogram.errors import PeerIdInvalid, RPCError
from pyrogram.file_id import FileId
from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.functions.stickers import CreateStickerSet
from pyrogram.raw.types import (
    InputStickerSetShortName,
    InputStickerSetItem,
    InputDocument,
)

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite, Message
from pagermaid.utils import alias_command
from pyromod.utils.conversation import Conversation


class GeneralError(Exception):
    def __init__(self, msg: str = ""):
        super().__init__(msg)


def get_tempfile() -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
        return f.name


def random_emoji() -> str:
    return random.choice(
        "😂😘❤️😍😊😁👍☺️😔😄😭😳😜🙈😉😃😢😝😱😌🙊😚😅😞😏"
        "😡😀😋😆👌😐😕🐶🐱🐭🐹🐰🦊🐻🐷🐮🐒🙊🦁🙉🐯🙈🐨🐵🐻‍"
        "❄️🐸🐼🐽🐔🐧🐦🐤🐣🐥🦆🦄🐴🐗🐺🦇🦉🦅🐝🪱🐛🦋🐌🐞🐜"
    )


async def create_sticker_set(name):
    try:
        empty_image = gen_empty_image()
        msgs = await push_file(empty_image)
        if msgs.document is None:
            raise GeneralError()

        file: FileId = FileId.decode(msgs.document.file_id)
        me = await bot.get_me()
        await bot.invoke(
            CreateStickerSet(
                user_id=await bot.resolve_peer(me.id),
                title=f"@{me.username} 的私藏",
                short_name=name,
                stickers=[
                    InputStickerSetItem(
                        document=InputDocument(
                            id=file.media_id,
                            access_hash=file.access_hash,
                            file_reference=file.file_reference,
                        ),
                        emoji=random_emoji(),
                    )
                ],
                animated=False,
                videos=False,
            )
        )
        await msgs.delete()

    except Exception as e:
        raise GeneralError("创建贴纸包失败.") from e


async def check_pack(name: str):
    try:
        if (
            await bot.invoke(
                GetStickerSet(
                    stickerset=InputStickerSetShortName(short_name=name), hash=0
                )
            )
        ).set.count == 120:
            return False
        return True
    except RPCError as e:
        traceback.print_exception(e)
        await create_sticker_set(name)
        return True


async def generate_sticker_set(time: int = 1) -> str:
    if time >= 20:
        raise GeneralError("尝试了很多次获取可用的贴纸包...但是都失败了. 尝试手动指定一个?")

    me = await bot.get_me()
    if not me.username:
        raise GeneralError("无法获取你的用户名...要不然咱去设置一个?")

    sticker_pack_name = f"{me.username}_{time}"
    if not await check_pack(sticker_pack_name):
        sticker_pack_name = await generate_sticker_set(time + 1)

    return sticker_pack_name


async def easy_ask(msg: typing.List, conv: Conversation):
    for i in msg:
        await conv.ask(i)
        await conv.mark_as_read()


async def add_to_stickers(sticker: Message):
    await get_sticker_set()  # To avoid some exception
    async with bot.conversation(429000) as conv:
        await easy_ask(["/start", "/cancel", "/addsticker"], conv)

        # Check Sticker pack
        resp: Message = await conv.ask(await get_sticker_set())
        if resp.text == "Invalid set selected.":
            raise GeneralError("无法指定贴纸包,请检查.")
        await conv.mark_as_read()
        await sticker.forward(429000)
        resp: Message = await conv.get_response()
        await conv.mark_as_read()
        if not resp.text.startswith("Thanks!"):
            await easy_ask(["/cancel"], conv)
            raise RuntimeError(f"无法添加贴纸, @Sticker 回复:\n{resp.text}")
        await easy_ask([random_emoji(), "/done", "/done"], conv)


async def download_photo(msg: Message) -> str:
    try:
        filename = get_tempfile()
        await bot.download_media(msg, filename)
        return filename
    except Exception as e:
        raise GeneralError("下载媒体失败.") from e


def convert_image(imgfile: str) -> str:
    try:
        img = Image.open(imgfile)
        width, height = img.size

        if (width >= 512 or height >= 512) or (width <= 512 and height <= 512):
            if width >= height:
                scaling = 512 / width
            else:
                scaling = 512 / height

            img = img.resize(
                (int(width * scaling), int(height * scaling)), Image.ANTIALIAS
            )
        img.save(imgfile + "_patched.png")

        return imgfile + "_patched.png"
    except Exception as e:
        raise GeneralError("在转换图片时出现了错误.") from e


async def push_file(imgfile: str) -> Message:
    try:
        me = await bot.get_me()

        async with bot.conversation(me.id) as conv:
            with open(imgfile, "rb") as f:
                msg = await conv.send_document(
                    f, file_name=f"{os.path.basename(imgfile)}"
                )

        return msg
    except Exception as e:
        raise GeneralError("上传文件失败.") from e


def get_custom_sticker() -> str | None:
    return sqlite.get("sticker_set", None)


def set_custom_sticker(name: str):
    sqlite["sticker_set"] = name


def del_custom_sticker():
    try:
        del sqlite["sticker_set"]
    except NameError as e:
        raise GeneralError("你好像没有设置自定义贴纸包.") from e


def gen_empty_image() -> str:
    filename = get_tempfile()
    Image.new("RGB", (512, 512), (0, 0, 0)).save(filename)

    return filename


async def get_sticker_set() -> str:
    sticker_pack_name = get_custom_sticker()

    if not sticker_pack_name or not await check_pack(sticker_pack_name):
        sticker_pack_name = await generate_sticker_set()
        set_custom_sticker(sticker_pack_name)
    return sticker_pack_name


@listener(
    command="sticker_refactor",
    parameters="[贴纸包名/cancel]",
    description="保存贴纸/照片到自己的贴纸包 但是重构",
    need_admin=True,
)
async def sticker_refactor(msg: Message):
    try:
        if msg.reply_to_message:
            # check target type
            if msg.reply_to_message.sticker:
                await add_to_stickers(msg.reply_to_message)
            elif msg.reply_to_message.photo:
                filename = await download_photo(msg.reply_to_message)
                converted_filename = convert_image(filename)
                # print(filename, converted_filename)
                msgs = await push_file(converted_filename)

                # Cleanup
                await add_to_stickers(msgs)
                await msgs.delete()
                os.remove(converted_filename)
                os.remove(filename)
            else:
                raise GeneralError("找不到可以转换的贴纸/图片,请检查.")
            await msg.edit(
                "✅ 成功添加到贴纸包 [{0}](https://t.me/addstickers/{0})".format(
                    await get_sticker_set()
                )
            )
        else:
            if len(msg.parameter) == 1:
                # Sticker Pack name
                if msg.arguments == "cancel":
                    del_custom_sticker()
                    await msg.edit("✅ 成功清除")
                else:
                    set_custom_sticker(msg.arguments)
                    await msg.edit("✅ 成功设置")
            else:
                await msg.edit(
                    f"""👋 Hi! 感谢使用 Sticker (重构版) 插件!
请直接回复你想要添加的贴纸/图片 来保存到你的贴纸包!
可使用 <code>,{alias_command('sticker_refactor')} 贴纸包名</code> 来自定义目标贴纸包 (若留cancel 则重置)
目前使用的贴纸包为 {await get_sticker_set()}
Made by Guimc (xiluo@guimc.ltd) with ❤"""
                )
    except PeerIdInvalid:
        await msg.edit("❌ 无法打开与 @Sticker 的对话 请先与其私聊一次")
    except GeneralError as e:
        await msg.edit(f"❌ 在处理时发生了错误: {e}")
