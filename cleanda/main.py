from pagermaid.enums import Message
from pagermaid.listener import listener
from pyrogram import Client, enums


@listener(
    command="cleanda", description="查找与已注销账号的会话"
)
async def clean_member(client: Client, message: Message):
    await message.edit("正在查找与已注销账号的会话，请稍等...")
    deleted = []
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat.type == enums.ChatType.PRIVATE:
            user = await client.get_users(chat.id)
            if getattr(user, "is_deleted", False):
                deleted.append(chat.id)
    await message.edit(
        f"共找到{len(deleted)}个与已注销账号的会话，请手动检查并删除\n\n"
        + "".join([f"[{uid}](tg://openmessage?user_id={uid})\n" for uid in deleted]),
        parse_mode=enums.ParseMode.MARKDOWN
    )
