from pyrogram import Client
from pyrogram.enums import ParseMode

from asyncio import TimeoutError
from pagermaid.listener import listener
from pagermaid.utils import Message


@listener(command="duckduckgo",
          description="Duckduckgo 搜索",
          parameters="<query>")
async def duckduckgo(client: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入查询内容")
    try:
        answer: Message = await client.ask("PagerMaid_Modify_bot", f"/duckduckgo {text}")  # noqa
        await client.read_chat_history("PagerMaid_Modify_bot")
    except TimeoutError:
        return await message.edit("获取时间超时，请稍后再试。")
    await message.edit(answer.text.html, parse_mode=ParseMode.HTML)


@listener(command="caiyun",
          description="彩云翻译",
          parameters="<query>")
async def caiyun_translate(client: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入查询内容")
    try:
        answer: Message = await client.ask("PagerMaid_Modify_bot", f"/translate {text}")  # noqa
        await client.read_chat_history("PagerMaid_Modify_bot")
    except TimeoutError:
        return await message.edit("获取时间超时，请稍后再试。")
    await message.edit(answer.text)


@listener(command="weather",
          description="使用彩云天气 api 查询国内实时天气。",
          parameters="<位置>")
async def weather(client: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入正确的地址")
    try:
        answer: Message = await client.ask("PagerMaid_Modify_bot", f"/weather_api {text}")  # noqa
        await client.read_chat_history("PagerMaid_Modify_bot")
    except TimeoutError:
        return await message.edit("获取时间超时，请稍后再试。")
    await message.edit(answer.text)


@listener(command="weather_pic",
          description="使用彩云天气 api 查询国内实时天气，但是显示图片。",
          parameters="<位置>")
async def weather_pic(client: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入正确的地址")
    try:
        answer: Message = await client.ask("PagerMaid_Modify_bot", f"/weather {text}")  # noqa
        await client.read_chat_history("PagerMaid_Modify_bot")
    except TimeoutError:
        return await message.edit("获取时间超时，请稍后再试。")
    await answer.copy(message.chat.id, reply_to_message_id=message.reply_to_message_id)
    await message.safe_delete()


@listener(command="weather_he",
          description="使用和风天气 api 查询国内实时天气，但是显示图片。",
          parameters="<位置>")
async def weather_he(client: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请输入正确的地址")
    try:
        answer: Message = await client.ask("PagerMaid_Modify_bot", f"/weather_he {text}")  # noqa
        await client.read_chat_history("PagerMaid_Modify_bot")
    except TimeoutError:
        return await message.edit("获取时间超时，请稍后再试。")
    await answer.copy(message.chat.id, reply_to_message_id=message.reply_to_message_id)
    await message.safe_delete()


async def az_tts(client: Client, message: Message, mode: str):
    text = message.arguments
    if not text:
        return await message.edit("请输入需要 tts 的内容")
    try:
        answer: Message = await client.ask("PagerMaid_Modify_bot", f"/tts {text} {mode}")  # noqa
        await client.read_chat_history("PagerMaid_Modify_bot")
    except TimeoutError:
        return await message.edit("获取时间超时，请稍后再试。")
    await answer.copy(message.chat.id, reply_to_message_id=message.reply_to_message_id)
    await message.safe_delete()


@listener(command="tts_nan",
          description="通过 Azure 文本到语音 基于字符串生成 简体男声 语音消息。",
          parameters="<字符串>")
async def az_tts_nan(client: Client, message: Message):
    await az_tts(client, message, "")


@listener(command="tts_nv",
          description="通过 Azure 文本到语音 基于字符串生成 简体女声 语音消息。",
          parameters="<字符串>")
async def az_tts_nv(client: Client, message: Message):
    await az_tts(client, message, "nv")


@listener(command="tts_tw",
          description="通过 Azure 文本到语音 基于字符串生成 繁体男声 语音消息。",
          parameters="<字符串>")
async def az_tts_tw(client: Client, message: Message):
    await az_tts(client, message, "tw")


@listener(command="tts_ne",
          description="通过 Azure 文本到语音 基于字符串生成 简体新闻男声 语音消息。",
          parameters="<字符串>")
async def az_tts_ne(client: Client, message: Message):
    await az_tts(client, message, "ne")


@listener(command="tts_en",
          description="通过 Azure 文本到语音 基于字符串生成 英文男声 语音消息。",
          parameters="<字符串>")
async def az_tts_en(client: Client, message: Message):
    await az_tts(client, message, "en")
