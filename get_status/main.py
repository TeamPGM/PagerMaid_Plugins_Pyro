from datetime import datetime
from pytz import timezone

from pyrogram.errors import DocumentInvalid
from pyrogram.raw.functions.users import GetUsers
from pyrogram.raw.types import InputUserSelf, InputUserFromMessage
from pyrogram.raw.types import EmojiStatus, EmojiStatusEmpty, EmojiStatusUntil

from pagermaid.listener import listener
from pagermaid.enums import Client, Message


async def get_status_emoji(bot: Client, message: Message = None) -> str:
    try:
        peer = (
            InputUserFromMessage(
                peer=(await bot.resolve_peer(message.chat.id)),
                msg_id=message.id,
                user_id=message.from_user.id,
            )
            if message
            else InputUserSelf()
        )
        req = await bot.invoke(GetUsers(id=[peer]))
        emoji_status = req[0].emoji_status
        if not emoji_status or isinstance(emoji_status, EmojiStatusEmpty):
            return "你还没有设置自定义 emoji 状态"
        if isinstance(emoji_status, EmojiStatus):
            return f"你的自定义 emoji 状态是 <emoji id='{emoji_status.document_id}'>🔥</emoji>"
        if isinstance(emoji_status, EmojiStatusUntil):
            time = datetime.strftime(
                datetime.fromtimestamp(emoji_status.until, timezone("Asia/Shanghai")),
                "%Y-%m-%d %H:%M:%S",
            )
            return f"你的自定义 emoji 状态是 <emoji id='{emoji_status.document_id}'>🔥</emoji> （有效期至：{time}）"
    except DocumentInvalid:
        return "无法获取自定义 emoji 状态，可能是状态已过期。"
    except Exception as e:
        raise FileNotFoundError from e


@listener(command="get_status", need_admin=True, description="获取自己或者他人的大会员自定义 emoji 状态")
async def get_emoji_status(bot: Client, message: Message):
    """获取自己或者他人的大会员自定义 emoji 状态"""
    if not message.reply_to_message_id:
        me = bot.me or await bot.get_me()
        if not me.is_premium:
            return await message.edit("你好像不是大会员。。。")
    try:
        string = await get_status_emoji(bot, message.reply_to_message)
    except FileNotFoundError:
        string = "获取自定义 emoji 状态失败。"
    await message.edit(string)
