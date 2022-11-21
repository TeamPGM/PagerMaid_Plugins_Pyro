from io import BytesIO

from PIL import Image
from math import floor

from pagermaid.listener import listener
from pagermaid.enums import Message, Client


async def resize_image(photo):
    image = Image.open(photo)
    if (image.width and image.height) < 512:
        size1 = image.width
        size2 = image.height
        if image.width > image.height:
            scale = 512 / size1
            size1new = 512
            size2new = size2 * scale
        else:
            scale = 512 / size2
            size1new = size1 * scale
            size2new = 512
        size1new = floor(size1new)
        size2new = floor(size2new)
        size_new = (size1new, size2new)
        image = image.resize(size_new)
    else:
        maxsize = (512, 512)
        image.thumbnail(maxsize)

    return image


@listener(command="pic_to_sticker",
          description="将你回复的图片转换为贴纸")
async def pic_to_sticker(bot: Client, message: Message):
    reply = message.reply_to_message
    photo = None
    if reply and reply.photo:
        photo = reply
    elif message.photo:
        photo = message
    if not photo:
        return await message.edit("请回复一张图片")
    try:
        photo = await bot.download_media(photo, in_memory=True)
        message: Message = await message.edit("正在转换...\n███████70%")
        image = await resize_image(photo)
        file = BytesIO()
        file.name = "sticker.webp"
        image.save(file, "WEBP")
        file.seek(0)
        if reply:
            await reply.reply_sticker(file, quote=True)
        else:
            await message.reply_sticker(file, quote=True)
    except Exception as e:
        return await message.edit(f"转换失败：{e}")
    await message.safe_delete()
