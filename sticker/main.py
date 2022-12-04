import contextlib

from asyncio import sleep
from typing import Optional

from pyrogram.raw.functions.messages import GetStickerSet
from pyrogram.raw.functions.stickers import CreateStickerSet
from pyrogram.raw.types import InputStickerSetShortName, InputDocument, InputStickerSetItem
from pyrogram.raw.types.messages import StickerSet
from pyrogram.file_id import FileId

from pagermaid.listener import listener
from pagermaid.services import bot, sqlite
from pagermaid.enums import Message
from pagermaid.single_utils import safe_remove
from pagermaid.utils import alias_command


class CannotToStickerSetError(Exception):
    """
        Occurs when program cannot change a message to a sticker set
    """

    def __init__(self):
        super().__init__(
            "无法将此消息转换为贴纸"
        )


class NoStickerSetNameError(Exception):
    """
        Occurs when no username is provided
    """

    def __init__(self, string: str = "请先设置用户名"):
        super().__init__(
            string
        )


class StickerSetFullError(Exception):
    """
        Occurs when the sticker set is full
    """

    def __init__(self):
        super().__init__(
            "贴纸包已满"
        )


async def get_pack(name: str):
    try:
        return await bot.invoke(GetStickerSet(
            stickerset=InputStickerSetShortName(short_name=name),
            hash=0
        ))
    except Exception as e:  # noqa
        raise NoStickerSetNameError("贴纸名名称错误或者不存在") from e


class Sticker:
    message: Message
    sticker_set: str
    custom_sticker_set: bool
    emoji: str
    should_forward: Message
    is_animated: bool
    is_video: bool
    document: Optional[InputDocument]
    document_path: Optional[str]
    software: str = "PagerMaid-Pyro"

    def __init__(self, message: Message, sticker_set: str = "", emoji: str = "😀",
                 should_forward: Message = None):
        self.message = message
        self.sticker_set = sticker_set
        self.custom_sticker_set = False
        self.load_custom_sticker_set()
        self.emoji = emoji
        self.should_forward = should_forward
        self.should_create = False
        self.is_animated = False
        self.is_video = False
        self.document = None
        self.document_path = None

    @staticmethod
    def get_custom_sticker_set():
        return sqlite.get("sticker_set", None)

    @staticmethod
    def set_custom_sticker_get(name: str):
        sqlite["sticker_set"] = name

    @staticmethod
    def del_custom_sticker_set():
        del sqlite["sticker_set"]

    def load_custom_sticker_set(self):
        if name := self.get_custom_sticker_set():
            self.sticker_set = name
            self.custom_sticker_set = True

    async def generate_sticker_set(self, time: int = 1):
        if not self.sticker_set or time > 1:
            me = await bot.get_me()
            if not me.username:
                raise NoStickerSetNameError()
            self.sticker_set = f"{me.username}_{time}"
            if self.is_video:
                self.sticker_set += "_video"
            elif self.is_animated:
                self.sticker_set += "_animated"
        try:
            await self.check_pack_full()
        except NoStickerSetNameError as e:
            self.should_create = True
        except StickerSetFullError:
            await self.generate_sticker_set(time + 1)

    async def check_pack_full(self):
        pack: StickerSet = await get_pack(self.sticker_set)
        if pack.set.count == 120:
            raise StickerSetFullError()

    async def process_sticker(self):
        if not (self.should_forward and self.should_forward.sticker):
            raise CannotToStickerSetError()
        sticker_ = self.should_forward.sticker
        self.is_video = sticker_.is_video
        self.is_animated = sticker_.is_animated
        self.emoji = sticker_.emoji
        if self.is_video or self.is_animated:
            self.document_path = await self.download_file()
        file = FileId.decode(sticker_.file_id)
        self.document = InputDocument(
            id=file.media_id,
            access_hash=file.access_hash,
            file_reference=file.file_reference,
        )

    async def download_file(self) -> str:
        return await self.should_forward.download()

    async def upload_file(self):
        if not self.document_path:
            return
        with contextlib.suppress(Exception):
            msg = await bot.send_document(429000, document=self.document_path, force_document=True)
            file = FileId.decode(msg.document.file_id)
            self.document = InputDocument(
                id=file.media_id,
                access_hash=file.access_hash,
                file_reference=file.file_reference,
            )
        safe_remove(self.document_path)

    async def create_sticker_set(self):
        me = await bot.get_me()
        title = f"@{me.username} 的私藏" if me.username else self.sticker_set
        try:
            await bot.invoke(
                CreateStickerSet(
                    user_id=await bot.resolve_peer((await bot.get_me()).id),
                    title=title,
                    short_name=self.sticker_set,
                    stickers=[
                        InputStickerSetItem(
                            document=self.document,
                            emoji=self.emoji
                        )
                    ],
                    animated=self.is_animated,
                    videos=self.is_video,
                )
            )
        except Exception as e:
            raise NoStickerSetNameError("贴纸包名称非法，请换一个") from e

    async def add_to_sticker_set(self):
        async with bot.conversation(429000) as conv:
            await conv.ask("/start")
            await sleep(.3)
            await conv.mark_as_read()
            await conv.ask("/cancel")
            await sleep(.3)
            await conv.mark_as_read()
            await conv.ask("/addsticker")
            await sleep(.3)
            await conv.mark_as_read()
            resp: Message = await conv.ask(self.sticker_set)
            await sleep(.3)
            if resp.text == "Invalid set selected.":
                raise NoStickerSetNameError("这个贴纸包好像不属于你~")
            await conv.mark_as_read()
            if self.is_video or self.is_animated:
                await self.upload_file()
            else:
                await self.should_forward.forward("Stickers")
            resp: Message = await conv.get_response()
            await sleep(.3)
            if not resp.text.startswith("Thanks!"):
                raise NoStickerSetNameError("这个贴纸包类型好像不匹配~")
            await conv.mark_as_read()
            await conv.ask(self.emoji)
            await sleep(.3)
            await conv.mark_as_read()
            await conv.ask("/done")
            await sleep(.3)
            await conv.mark_as_read()
            await conv.ask("/done")
            await sleep(.3)
            await conv.mark_as_read()

    async def to_sticker_set(self):
        await self.generate_sticker_set()
        if not self.sticker_set:
            raise NoStickerSetNameError()
        if self.should_create:
            await self.upload_file()
            await self.create_sticker_set()
        else:
            await self.add_to_sticker_set()

    def mention(self):
        return f"[{self.sticker_set}](https://t.me/addstickers/{self.sticker_set})"

    def get_config(self) -> str:
        pack = self.mention() if self.sticker_set else "无法保存，请设置用户名"
        return f"欢迎使用 sticker 插件\n\n" \
               f"将自动保存到贴纸包：{pack}\n\n" \
               f"使用命令 <code>,{alias_command('s')} 贴纸包名</code> 自定义保存贴纸包\n" \
               f"使用命令 <code>,{alias_command('s')} cancel</code> 取消自定义保存贴纸包"


@listener(command="s",
          need_admin=True)
async def sticker(message: Message):
    one_sticker = Sticker(message, should_forward=message.reply_to_message)
    if not message.reply_to_message:
        with contextlib.suppress(Exception):
            await one_sticker.generate_sticker_set()
        if not message.arguments:
            return await message.edit(one_sticker.get_config())
        elif len(message.parameter) == 1:
            if message.arguments == "cancel":
                if one_sticker.get_custom_sticker_set() is None:
                    return await message.edit("还没有设置自定义保存贴纸包")
                one_sticker.del_custom_sticker_set()
                return await message.edit("移除自定义保存贴纸包成功")
            else:
                one_sticker.sticker_set = message.arguments
                try:
                    await one_sticker.check_pack_full()
                except NoStickerSetNameError:
                    pass
                except Exception as e:
                    return await message.edit(f"设置自定义贴纸包失败：{e}")
                one_sticker.set_custom_sticker_get(message.arguments)
                return await message.edit("设置自定义保存贴纸包成功")
        else:
            return await message.edit("参数错误")
    try:
        await one_sticker.process_sticker()
        await one_sticker.to_sticker_set()
    except Exception as e:
        return await message.edit(f"收藏到贴纸包失败：{e}")
    await message.edit(f"收藏到贴纸包 {one_sticker.mention()} 成功")
