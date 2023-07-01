from PIL import Image

from pagermaid.listener import listener
from pagermaid.enums import Message, Client
from pagermaid.single_utils import safe_remove


@listener(
    command="sticker_to_pic", description="将你回复的静态贴纸转换为图片", parameters="（是否发送原图，默认为否）"
)
async def sticker_to_pic(bot: Client, message: Message):
    origin = bool(message.arguments)
    reply = message.reply_to_message
    if not reply:
        return await message.edit("请回复一个静态贴纸")
    if not reply.sticker:
        return await message.edit("请回复一个静态贴纸")
    if reply.sticker.is_animated or reply.sticker.is_video:
        return await message.edit("请回复一个静态贴纸")
    try:
        photo = await bot.download_media(reply, in_memory=True)
        message: Message = await message.edit("正在转换...\n███████70%")
        image = Image.open(photo)
        image.save("sticker.png", "PNG")
    except Exception as e:
        return await message.edit(f"转换失败：{e}")
    if origin:
        await reply.reply_document("sticker.png", quote=True)
    else:
        await reply.reply_photo("sticker.png", quote=True)
    safe_remove("sticker.png")
    await message.safe_delete()
