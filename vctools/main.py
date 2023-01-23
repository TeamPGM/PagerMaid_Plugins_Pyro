from pyrogram.errors import ChatAdminRequired
from pyrogram.raw.functions.channels import GetFullChannel
from pyrogram.raw.functions.phone import CreateGroupCall, DiscardGroupCall

from pagermaid.listener import listener
from pagermaid.enums import Client, Message


@listener(command="vctools",
          admins_only=True,
          groups_only=True,
          parameters="[开启/关闭]",
          description="开启/关闭群组直播间")
async def vctools(bot: Client, message: Message):
    if not message.arguments:
        return await message.reply("请输入 `开启/关闭`")
    if message.arguments == "开启":
        try:
            await bot.invoke(
                CreateGroupCall(
                    peer=await bot.resolve_peer(message.chat.id),
                    random_id=bot.rnd_id() // 9000000000,
                )
            )
            return await message.edit("已开启群组直播间")
        except ChatAdminRequired:
            return await message.reply("需要管理员权限")
    elif message.arguments == "关闭":
        try:
            full_chat = (await bot.invoke(GetFullChannel(channel=await bot.resolve_peer(message.chat.id)))).full_chat
            if full_chat.call:
                await bot.invoke(DiscardGroupCall(call=full_chat.call))
            return await message.edit("已关闭群组直播间")
        except ChatAdminRequired:
            return await message.reply("需要管理员权限")
    else:
        return await message.reply("请输入开启/关闭")
