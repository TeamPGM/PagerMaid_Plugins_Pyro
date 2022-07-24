from pagermaid.enums import Client, Message
from pagermaid.listener import listener

from pyrogram.raw.functions.channels import GetAdminedPublicChannels


@listener(command="listusernames",
          admins_only=True,
          description="列出所有属于自己的公开群组/频道。")
async def list_usernames(bot: Client, message: Message):
    """ Get a list of your reserved usernames. """
    result = await bot.invoke(GetAdminedPublicChannels())
    output = f"以下是属于我的 {len(result.chats)} 个所有公开群组/频道：\n\n"
    for i in result.chats:
        try:
            output += f"{i.title}\n@{i.username}\n\n"
        except AttributeError:
            output += f"{i.title}\n\n"
    await message.edit(output)
