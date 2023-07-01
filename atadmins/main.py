from pyrogram.enums import ChatMembersFilter

from pagermaid.listener import listener
from pagermaid.enums import Client, Message


@listener(
    command="atadmins",
    description="一键 AT 本群管理员（仅在群组中有效）",
    groups_only=True,
    parameters="[要说的话]",
)
async def at_admins(client: Client, message: Message):
    admins = []
    async for m in client.get_chat_members(
        message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
    ):
        if not m.user.is_bot and not m.user.is_deleted:
            admins.append(m.user.mention)
    if not admins:
        return await message.edit("❌ 没有管理员")
    say = message.arguments or "召唤本群所有管理员"
    send_list = " , ".join(admins)
    await client.send_message(
        message.chat.id,
        "%s：\n\n%s" % (say, send_list),
        reply_to_message_id=message.reply_to_message_id
        or message.reply_to_top_message_id,
    )
    await message.safe_delete()
