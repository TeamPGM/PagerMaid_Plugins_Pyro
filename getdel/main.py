from datetime import datetime, timedelta

from pyrogram.errors import FloodWait, ChatAdminRequired, UserAdminInvalid

from pagermaid.listener import listener
from pagermaid.single_utils import Message


@listener(command="getdel",
          groups_only=True,
          need_admin=True,
          parameters="清理",
          description="获取当前群组的死号数。")
async def get_del(message: Message):
    """ PagerMaid get_del. """
    need_kick = message.arguments
    member_count = 0
    try:
        await message.edit('遍历成员中。。。')
        if need_kick:
            user = await message.bot.get_chat_member(message.chat.id, (await message.bot.get_me()).id)
            need_kick = bool(user.privileges and user.privileges.can_restrict_members)
        async for member in message.bot.get_chat_members(message.chat.id):
            if member.user.is_deleted:
                member_count += 1
                if need_kick:
                    try:
                        await message.bot.ban_chat_member(
                            message.chat.id,
                            member.user.id,
                            datetime.now() + timedelta(minutes=5))
                    except FloodWait:
                        return await message.edit('处理失败，您已受到 TG 服务器限制。')
                    except UserAdminInvalid:
                        pass
        if need_kick:
            await message.edit(f'此群组的死号数：`{member_count}`，并且已经清理完毕。')
        else:
            await message.edit(f'此群组的死号数：`{member_count}`。')
    except ChatAdminRequired:
        await message.edit("你好像并不拥有封禁用户权限。")
