from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove
from pagermaid.enums import Client, Message


async def get_audio(message: Message):
    if reply := message.reply_to_message:
        if reply.audio:
            return reply
    return message if message.audio else None


@listener(command="audio_to_voice",
          description="将音乐文件转换为语音")
async def audio_to_voice(bot: Client, message: Message):
    audio = await get_audio(message)
    if not audio:
        return await message.edit("请回复一个音乐文件")
    message: Message = await message.edit("转换中。。。")
    try:
        audio = await audio.download()
        await bot.send_voice(
            message.chat.id,
            audio,
            reply_to_message_id=message.id if message.audio else (message.reply_to_message_id or
                                                                  message.reply_to_top_message_id))
    except Exception as e:
        await message.edit(f"转换为语音消息失败：{e}")
    safe_remove(audio)
    if not message.audio:
        await message.safe_delete()
    else:
        await message.edit("")
