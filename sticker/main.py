""" PagerMaid module to handle sticker collection. """

import traceback
from asyncio import sleep
from os import remove
from io import BytesIO
from PIL import Image, ImageOps
from math import floor
from pagermaid import bot, log
from pagermaid.config import config
from pagermaid.listener import listener
from pagermaid.utils import alias_command, client, pip_install
from pyrogram.enums import MessageMediaType

pip_install("beautifulsoup4", alias = "bs4")

from bs4 import BeautifulSoup

WAITING = 0
MSG = ""

@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=True, privates_only=True)
async def wait(_, message):
    global WAITING, MSG
    if message.from_user.id == 429000:
        WAITING = 0
        MSG = message

async def get_response():
    global WAITING, MSG
    WAITING = 1
    while WAITING:
        await sleep(0.01)
    return MSG

def is_int(a):
    try:
        int(a)
        return True
    except:
        return False

async def idle(*args, **kwargs):
    pass

@listener(is_plugin=False, outgoing=True, command=alias_command("s"),
          description="Sticker Tools",
          parameters="<emoji>")
async def sticker(app, context):
    """ Fetches images/stickers and add them to your pack. """
    # 首先解封 sticker Bot
    try:
        await app.unblock_user(429000)
    except:
        pass
    await context.delete()
    context.edit = idle
    pic_round = False
    is_batch = False
    to_sticker_set = False
    package_name = ""

    user = await bot.get_me()
    if not user.username:
        user.username = user.first_name

    custom_emoji = False
    animated = False
    emoji = ""
    message = None

    if len(context.parameter) >= 1:
        if "png" in context.parameter[0]:
            pic_round = False
            # s <number>
        elif "to" in context.parameter:
            if len(context.parameter) == 3:
                to_sticker_set = context.parameter[2]
                await context.edit(f"成功设置贴纸包为 {to_sticker_set}\n下次只需要 ,s to 即可!")
                await sleep(.5)
            elif len(context.parameter) == 2:
                to_sticker_set = context.parameter[1]
                await context.edit(f"成功设置贴纸包为 {to_sticker_set}\n下次只需要 ,s to 即可!")
                await sleep(.5)
            elif "to_sticker_set" in config:
                to_sticker_set = config["to_sticker_set"]
            else:
                return await context.edit("你过去没有指定过贴纸包! 请使用 ,s to <sticker_package>")
            config["to_sticker_set"] = to_sticker_set
        elif context.parameter[0] == "void_steal" and is_int(context.parameter[1]):
            await context.edit(f"正在运行 Anti-AntiSticker \ntarget={context.parameter[0]}  chat_id={context.chat.id}")
            try:
                async for m in app.get_chat_history(context.chat.id, limit = 5000):
                    if m.from_user.id == int(
                        context.parameter[1]
                    ) and m.media in [
                        MessageMediaType.PHOTO,
                        MessageMediaType.STICKER
                    ]:
                        await context.edit(f"找到啦! msg_id={m.id}")
                        message = m
                        break
            except Exception as e:
                traceback_msg = "\n".join(traceback.format_exception(e))
                return await context.reply(f"失败了... 是否输入了正确的参数?\n\n{traceback_msg}")
        elif context.parameter[0].isnumeric():
            pass
        elif isEmoji(context.parameter[0]) or len(context.parameter[0]) == 1:
            await log(f"emoji：{context.parameter[0]}")
        else:
            try:
                await context.reply("命令参数错误")
            except:
                pass
            return

    # 单张收集图片
    if not message:
        message = context.reply_to_message
    try:
        await single_sticker(animated, context, custom_emoji, emoji, message, pic_round, user, "", to_sticker_set)
    except FileExistsError:
        await context.reply("贴纸包满了!")


async def single_sticker(animated, context, custom_emoji, emoji, message, pic_round, user, package_name,
                         to_sticker_set):
    try:
        await context.edit("正在处理")
    except:
        pass
    if message and message.media:
        if message.media == MessageMediaType.PHOTO:
            photo = BytesIO()
            photo = await bot.download_media(message)
        elif message.media == MessageMediaType.STICKER:
            photo = BytesIO()
        elif message.media == MessageMediaType.VIDEO:
            try:
                await context.reply("不支持此类型!")
            except:
                pass
            return
        else:
            try:
                await context.reply("不支持此类型")
            except:
                pass
            return
    else:
        try:
            await context.reply("你回复的不是贴纸")
        except:
            pass
        return

    if photo:
        split_strings = context.text.split()
        if not custom_emoji:
            emoji = "👀"
        pack = 1
        if (
            to_sticker_set
            and split_strings[1].isnumeric()
            or not to_sticker_set
            and not package_name
            and len(split_strings) != 3
            and len(split_strings) == 2
            and split_strings[1].isnumeric()
        ):
            pack = int(split_strings[1])
        elif (
            to_sticker_set and not split_strings[1].isnumeric()
            or not to_sticker_set and 
                ((package_name and len(split_strings) != 5 and len(split_strings) != 4) or
                (not package_name and len(split_strings) != 3 and 
                    (len(split_strings) == 2 and not split_strings[1].isnumeric() or len(split_strings) != 2)
                ))
        ):
            pass
        elif package_name and len(split_strings) == 5:
            pack = split_strings[4]
        elif package_name:
            pack = split_strings[3]
        else:
            # s png <number|emoji>
            pack = split_strings[2]
        if not isinstance(pack, int):
            pack = 1

        if package_name:
            # merge指定package_name
            pack_name = f"{user.username}_{package_name}_{pack}"
            pack_title = f"@{user.username}  的私藏 ({package_name}) ({pack})"
        elif to_sticker_set:
            pack_name = to_sticker_set
            pack_title = f"@{user.username}  的私藏 ({package_name}) ({pack})"
        else:
            pack_name = f"{user.username}_{pack}"
            pack_title = f"@{user.username}  的私藏 ({pack})"
        command = '/newpack'
        file = BytesIO()

        if not animated and message.media != MessageMediaType.STICKER:
            try:
                await context.edit("缩放中")
            except:
                pass
            image = await resize_image(photo)
            if pic_round:
                try:
                    await context.edit("圆角处理中")
                except:
                    pass
                image = await rounded_image(image)
            file.name = "sticker.png"
            image.save(file, "PNG")
        elif animated:
            if not to_sticker_set:
                pack_name += "_animated"
                pack_title += " (animated)"
                command = '/newanimated'

        try:
            response = await client.get(f'https://t.me/addstickers/{pack_name}')
        except UnicodeEncodeError:
            pack_name = f's{hex(context.sender_id)[2:]}'
            if animated:
                pack_name = f's{hex(context.sender_id)[2:]}_animated'
            response = await client.get(f'https://t.me/addstickers/{pack_name}')
        if response.status_code != 200:
            try:
                await context.reply("服务器错误")
            except:
                pass
            return
        http_response = response.text.split('\n')

        if "  A <strong>Telegram</strong> user has created the <strong>Sticker&nbsp;Set</strong>." not in \
                http_response:
            sticker_already = False
            for _ in range(20):  # 最多重试20次
                try:
                    await context.bot.ask("Stickers", '/cancel', timeout = 60)
                    # await bot.send_read_acknowledge(429000)
                    await context.bot.ask("Stickers", '/addsticker', timeout = 60)
                    # await bot.send_read_acknowledge(429000)
                    chat_response = await context.bot.ask("Stickers", pack_name, timeout = 60)
                    while chat_response.text == "Whoa! That's probably enough stickers for one set, " \
                                                "give it a break. " \
                                                "A set can't have more than 120 stickers at the moment.":
                        pack += 1

                        # 指定贴纸包已满时直接报错
                        if to_sticker_set:
                            raise FileExistsError
                        if package_name:
                            # merge指定package_name
                            pack_name = f"{user.username}_{package_name}_{pack}"
                            pack_title = f"@{user.username}  的私藏 ({package_name}) ({pack})"
                        else:
                            pack_name = f"{user.username}_{pack}"
                            pack_title = f"@{user.username}  的私藏 ({pack})"
                        try:
                            if package_name:
                                await context.edit(f"切换到私藏{str(package_name)}{pack} 贴纸包满了")
                            else:
                                await context.edit(f"切换到私藏 {pack} 贴纸包满了")
                        except:
                            pass
                        chat_response = await context.bot.ask("Stickers", pack_name)
                        if chat_response.text == "Invalid set selected.":
                            await add_sticker(conversation, command, pack_title, pack_name, animated, message,
                                              context, file, emoji)
                            try:
                                await context.edit(
                                    f"贴纸已经被添加到 t.me/addstickers/{pack_name}")
                            except:
                                pass
                            return
                    if message.media == MessageMediaType.STICKER:
                        await context.edit(f"转发中 id={message.id}")
                        await bot.forward_messages(429000, message.chat.id, message.id)
                    else:
                        try:
                            await upload_sticker(animated, message, context, file)
                        except ValueError:
                            try:
                                await context.reply("请回复带有图片/贴纸的消息")
                            except:
                                pass
                            return
                    await get_response()
                    await context.bot.ask("Stickers", emoji, timeout = 60)
                    # await bot.send_read_acknowledge(429000)
                    await bot.send_message("Stickers", '/done')
                    # await bot.send_read_acknowledge(429000)
                    break
                except Exception:
                    # if not sticker_already:
                    #     try:
                    #         await context.edit("另一个贴纸保存正在运行")
                    #     except:
                    #         pass
                    #     sticker_already = True
                    await sleep(.5)
                    raise
        else:
            try:
                await context.edit("贴纸包不存在 正在创建")
            except:
                pass
            conversation = await bot.get_chat('Stickers')
            await add_sticker(conversation, command, pack_title, pack_name, animated, message,
                                 context, file, emoji)


async def add_sticker(conversation, command, pack_title, pack_name, animated, message, context, file, emoji):
    await context.bot.ask("Stickers", "/cancel", timeout = 60)
    # await bot.send_read_acknowledge(429000)
    await context.bot.ask("Stickers", command, timeout = 60)
    # await bot.send_read_acknowledge(429000)
    await context.bot.ask("Stickers", pack_title, timeout = 60)
    # await bot.send_read_acknowledge(429000)
    if message.media == MessageMediaType.STICKER:
        await context.edit(f"转发中 id={message.id}")
        await bot.forward_messages(429000, context.chat.id, message.id)
    else:
        try:
            await upload_sticker(animated, message, context, file)
        except ValueError:
            try:
                await context.reply("请回复带贴纸/图片的消息")
            except:
                pass
            return
    await get_response()
    await context.bot.ask("Stickers", emoji, timeout = 60)
    # await bot.send_read_acknowledge(429000)
    awaitcontext.bot.ask("Stickers", "/publish", timeout = 60)
    if animated:
        await context.bot.ask("Stickers", f"<{pack_title}>", timeout = 60)
    # await bot.send_read_acknowledge(429000)
    await context.bot.ask("Stickers", "/skip", timeout = 60)
    # wait bot.send_read_acknowledge(429000)
    await bot.send_message("Stickers", '/done')
    # await bot.send_read_acknowledge(429000)


async def upload_sticker(animated, message, context, file):
    if animated:
        try:
            await context.edit("上传中...")
        except:
            pass
        await bot.send_document(429000, "AnimatedSticker.tgs", force_document=True)
        remove("AnimatedSticker.tgs")
    else:
        file.seek(0)
        try:
            await context.edit("上传中")
        except:
            pass
        await bot.send_document(429000, file, force_document=True)


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


async def rounded_image(image):
    w = image.width
    h = image.height
    resize_size = 0
    # 比较长宽
    resize_size = h if w > h else w
    half_size = floor(resize_size / 2)

    # 获取圆角模版，切割成4个角
    tl = (0, 0, 256, 256)
    tr = (256, 0, 512, 256)
    bl = (0, 256, 256, 512)
    br = (256, 256, 512, 512)
    border = Image.open('pagermaid/static/images/rounded.png').convert('L')
    tlp = border.crop(tl)
    trp = border.crop(tr)
    blp = border.crop(bl)
    brp = border.crop(br)

    # 缩放四个圆角
    tlp = tlp.resize((half_size, half_size))
    trp = trp.resize((half_size, half_size))
    blp = blp.resize((half_size, half_size))
    brp = brp.resize((half_size, half_size))

    # 扩展四个角大小到目标图大小
    # tlp = ImageOps.expand(tlp, (0, 0, w - tlp.width, h - tlp.height))
    # trp = ImageOps.expand(trp, (w - trp.width, 0, 0, h - trp.height))
    # blp = ImageOps.expand(blp, (0, h - blp.height, w - blp.width, 0))
    # brp = ImageOps.expand(brp, (w - brp.width, h - brp.height, 0, 0))

    # 四个角合并到一张新图上
    ni = Image.new('RGB', (w, h), (0, 0, 0)).convert('L')
    ni.paste(tlp, (0, 0))
    ni.paste(trp, (w - trp.width, 0))
    ni.paste(blp, (0, h - blp.height))
    ni.paste(brp, (w - brp.width, h - brp.height))

    # 合并圆角和原图
    image.putalpha(ImageOps.invert(ni))

    return image


def isEmoji(content):
    return (
        u"\U0001F600" <= content <= u"\U0001F64F"
        or u"\U0001F300" <= content <= u"\U0001F5FF"
        or u"\U0001F680" <= content <= u"\U0001F6FF"
        or u"\U0001F1E0" <= content <= u"\U0001F1FF"
        if content
        else False
    )
