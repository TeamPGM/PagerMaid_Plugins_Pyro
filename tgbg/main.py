from urllib.parse import urlparse

from pyrogram.raw.functions.account import GetWallPaper
from pyrogram.raw.types import InputWallPaperSlug, WallPaper
from pyrogram.types.messages_and_media.document import Document

from pagermaid.listener import listener
from pagermaid.enums import Client, Message


@listener(command="tgbg", description="解析 Telegram 聊天窗口背景图", parameters="t.me/bg/xxx")
async def tg_bg(client: Client, message: Message):
    argument = message.obtain_message()
    if url := urlparse(argument):
        if path := url.path:
            if url.hostname == "t.me" and path.startswith("/bg/"):
                slug = path[4:]
                try:
                    bg: WallPaper = await client.invoke(
                        GetWallPaper(wallpaper=InputWallPaperSlug(slug=slug))
                    )
                except Exception as e:
                    return await message.edit(f"获取失败: {str(e)}")
                if bg.document:
                    bg_doc = Document._parse(
                        client, document=bg.document, file_name="bg.jpg"
                    )  # noqa
                    await client.send_document(
                        message.chat.id,
                        bg_doc.file_id,
                        file_name="bg.jpg",
                        reply_to_message_id=message.reply_to_top_message_id,
                    )
                    return await message.safe_delete()
    await message.edit("获取失败，请检查 URL")
