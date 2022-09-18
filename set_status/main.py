from typing import Optional

from pyrogram.enums import MessageEntityType
from pyrogram.raw.functions.account import UpdateEmojiStatus
from pyrogram.raw.types import EmojiStatus

from pagermaid.listener import listener
from pagermaid.enums import Client, Message


async def get_custom_emojis(message: Message) -> Optional[int]:
    if not message:
        return None
    if message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.CUSTOM_EMOJI:
                return entity.custom_emoji_id


async def set_custom_emoji(bot: Client, custom_emoji_id: int):
    try:
        await bot.invoke(
            UpdateEmojiStatus(emoji_status=EmojiStatus(document_id=custom_emoji_id))
        )
    except Exception as e:
        raise FileNotFoundError from e


@listener(command="set_status",
          parameters="<大会员自定义 emoji>",
          need_admin=True,
          description="快速设置大会员自定义 emoji 状态")
async def set_emoji_status(bot: Client, message: Message):
    """ 快速设置大会员自定义 emoji 状态 """
    me = bot.me or await bot.get_me()
    if not me.is_premium:
        return await message.edit("你好像不是大会员。。。")
    custom_emoji_id = await get_custom_emojis(message.reply_to_message or message)
    if not custom_emoji_id:
        return await message.edit("请回复或者输入一个大会员 emoji。")
    try:
        await set_custom_emoji(bot, custom_emoji_id)
    except FileNotFoundError:
        return await message.edit("找不到这个大会员 emoji。")
    await message.edit("设置自定义大会员 emoji 状态成功")
