from pyrogram.enums import ParseMode

from pagermaid.listener import listener
from pagermaid.utils import Message


@listener(command="duckduckgo",
          description="Duckduckgo 搜索",
          parameters="<query>")
async def duckduckgo(message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入查询内容")
    async with message.bot.conversation("PagerMaid_Modify_bot") as conv:
        answer: Message = await conv.ask(f"/duckduckgo {text}")
        await conv.mark_as_read()
    await message.edit(answer.text.html, parse_mode=ParseMode.HTML)


@listener(command="caiyun",
          description="彩云翻译",
          parameters="<query>")
async def caiyun_translate(message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入查询内容")
    async with message.bot.conversation("PagerMaid_Modify_bot") as conv:
        answer: Message = await conv.ask(f"/translate {text}")
        await conv.mark_as_read()
    await message.edit(answer.text)


@listener(command="weather",
          description="使用彩云天气 api 查询国内实时天气。",
          parameters="<位置>")
async def weather(message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入正确的地址")
    async with message.bot.conversation("PagerMaid_Modify_bot") as conv:
        answer: Message = await conv.ask(f"/weather_api {text}")
        await conv.mark_as_read()
    await message.edit(answer.text)


@listener(command="weather_pic",
          description="使用彩云天气 api 查询国内实时天气，但是显示图片。",
          parameters="<位置>")
async def weather_pic(message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入正确的地址")
    async with message.bot.conversation("PagerMaid_Modify_bot") as conv:
        answer: Message = await conv.ask(f"/weather {text}")
        await conv.mark_as_read()
    await answer.copy(message.chat.id, reply_to_message_id=message.reply_to_message_id)
    await message.safe_delete()


@listener(command="weather_he",
          description="使用和风天气 api 查询国内实时天气，但是显示图片。",
          parameters="<位置>")
async def weather_he(message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入正确的地址")
    async with message.bot.conversation("PagerMaid_Modify_bot") as conv:
        answer: Message = await conv.ask(f"/weather_he {text}")
        await conv.mark_as_read()
    await answer.copy(message.chat.id, reply_to_message_id=message.reply_to_message_id)
    await message.safe_delete()


async def az_tts(message: Message, mode: str):
    text = message.arguments
    if not text:
        return await message.edit("请输入需要 tts 的内容")
    async with message.bot.conversation("PagerMaid_Modify_bot") as conv:
        answer: Message = await conv.ask(f"/tts {text} {mode}")
        await conv.mark_as_read()
    await answer.copy(message.chat.id, reply_to_message_id=message.reply_to_message_id)
    await message.safe_delete()


@listener(command="tts_nan",
          description="通过 Azure 文本到语音 基于字符串生成 简体男声 语音消息。",
          parameters="<字符串>")
async def az_tts_nan(message: Message):
    await az_tts(message, "")


@listener(command="tts_nv",
          description="通过 Azure 文本到语音 基于字符串生成 简体女声 语音消息。",
          parameters="<字符串>")
async def az_tts_nv(message: Message):
    await az_tts(message, "nv")


@listener(command="tts_tw",
          description="通过 Azure 文本到语音 基于字符串生成 繁体男声 语音消息。",
          parameters="<字符串>")
async def az_tts_tw(message: Message):
    await az_tts(message, "tw")


@listener(command="tts_ne",
          description="通过 Azure 文本到语音 基于字符串生成 简体新闻男声 语音消息。",
          parameters="<字符串>")
async def az_tts_ne(message: Message):
    await az_tts(message, "ne")


@listener(command="tts_en",
          description="通过 Azure 文本到语音 基于字符串生成 英文男声 语音消息。",
          parameters="<字符串>")
async def az_tts_en(message: Message):
    await az_tts(message, "en")
