from pyrogram.raw.functions.messages import ReadMentions

from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.sub_utils import Sub
from pagermaid.utils import lang

from pyromod import require_mod_version

no_mentions_sub = Sub("no_mentions")


@listener(command="no_mentions",
          description="自动消除某个对话的 @ 提醒",
          parameters="[true|false|status]")
async def no_mentions(_: Client, message: Message):
    if len(message.parameter) != 1:
        await message.edit(f"[no_mentions] {lang('error_prefix')}{lang('arg_error')}")
        return
    status = message.parameter[0].lower()
    if status == "true":
        if no_mentions_sub.add_id(message.chat.id):
            return await message.edit("[no_mentions] 成功在这个对话开启")
        else:
            return await message.edit("[no_mentions] 这个对话已经开启了")
    elif status == "false":
        if no_mentions_sub.del_id(message.chat.id):
            return await message.edit("[no_mentions] 成功在这个对话关闭")
        else:
            return await message.edit("[no_mentions] 这个对话未开启")
    elif message.parameter[0] == "status":
        if no_mentions_sub.check_id(message.chat.id):
            await message.edit("[no_mentions] 这个对话已经开启了")
        else:
            await message.edit("[no_mentions] 这个对话未开启")
    else:
        await message.edit(f"[no_mentions] {lang('error_prefix')}{lang('arg_error')}")


@listener(incoming=True, outgoing=False, ignore_edited=True)
@require_mod_version(2)
async def set_read_mentions(client: Client, message: Message):
    if not no_mentions_sub.check_id(message.chat.id):
        return
    if not message.reply_to_message:
        return
    if not message.reply_to_message.outgoing:
        return
    await client.invoke(
        ReadMentions(
            peer=await client.resolve_peer(message.chat.id),
            top_msg_id=message.reply_to_top_message_id if message.chat.is_forum else None,
        )
    )
