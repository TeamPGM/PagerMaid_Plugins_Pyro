import asyncio
from datetime import datetime, timedelta

from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import UserAdminInvalid, BadRequest, ChatAdminRequired
from pyrogram.types import ChatPermissions

from pagermaid.listener import listener
from pagermaid.utils import Message


@listener(command="portball", is_plugin=True, outgoing=True, need_admin=True,
          description="回复你要临时禁言的人的消息来实现XX秒的禁言",
          parameters="[理由]|<时间/秒>")
async def portball(_, message: Message):
    bot = message.bot
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        reply_to_message = message.reply_to_message
        if reply_to_message is not None:
            from_user = reply_to_message.from_user
            chat = reply_to_message.chat
            if from_user.id == bot.me.id:
                await message.edit_text('无法禁言自己。')
                return
            seconds: int = -1
            reason: str = ""
            if len(message.parameter) == 1:
                try:
                    seconds = int(message.parameter[0])
                except ValueError:
                    await message.edit_text("出错了呜呜呜 ~ 无效的参数。")
                    await asyncio.sleep(10)
                    await message.safe_delete()
                    return
            elif len(message.parameter) == 2:
                try:
                    reason = message.parameter[0]
                    seconds = int(message.parameter[1])
                except ValueError:
                    await message.edit_text("出错了呜呜呜 ~ 无效的参数。")
                    await asyncio.sleep(10)
                    await message.safe_delete()
                    return
            else:
                await message.edit_text("出错了呜呜呜 ~ 无效的参数。")
                await asyncio.sleep(10)
                await message.safe_delete()
                return
            if seconds < 60:
                await message.edit_text("诶呀不要小于60秒啦")
                await asyncio.sleep(10)
                await message.safe_delete()
                return
            try:
                await bot.restrict_chat_member(chat.id, from_user.id, ChatPermissions(),
                                               datetime.now() + timedelta(seconds=seconds))
            except (UserAdminInvalid, ChatAdminRequired):
                await bot.send_message(chat.id, "错误：该操作需要管理员权限")
                await asyncio.sleep(10)
                await message.safe_delete()
                return
            except BadRequest:
                await message.edit_text("出错了呜呜呜 ~ 执行封禁时出错")
                await asyncio.sleep(10)
                await message.safe_delete()
                return
            else:
                text = f"[{from_user.last_name}{from_user.first_name}](tg://user?id={from_user.id}) "
                if reason != "":
                    text += f"由于 {reason} "
                text += f"被塞了{seconds}秒口球.\n"
                text += "到期自动拔出,无后遗症."
                await bot.send_message(chat.id, text)
                await message.safe_delete()
        else:
            await message.edit_text("你好蠢诶，都没有回复人，我哪知道你要搞谁的事情……")
            await asyncio.sleep(10)
            await message.safe_delete()
    else:
        await message.edit_text("你好蠢诶，又不是群组，怎么禁言啦！")
        await asyncio.sleep(10)
        await message.safe_delete()
