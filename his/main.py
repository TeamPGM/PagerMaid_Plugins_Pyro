"""
Pagermaid_Pyro group message history query plugin. Plugin by @tom-snow (@caiji_shiwo)
"""
from pagermaid import log
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.utils import alias_command
from pagermaid.config import Config


class HisMsg:
    LANGUAGES = {
        "en": {
            "name": "",
            "arg": "&lt;user> [-n &lt;num>]",
            "help": "Query the message history of the specified user in the group\n"
            f"Usage: \n`,{alias_command('his')} &lt;user> [-n &lt;num>]`"
            "\n&nbsp;&nbsp; <i>user</i>: username or user_id; <i>num</i>: Limits the number of messages to be retrieved\n"
            "You can just reply to a message without <i>user</i> argument",
            "processing": f",{alias_command('his')}: Querying...",
            "media": {
                "AUDIO": "[AUDIO]:",
                "DOCUMENT": "[DOCUMENT]:",
                "PHOTO": "[PHOTO]:",
                "STICKER": "[STICKER]:",
                "VIDEO": "[VIDEO]:",
                "ANIMATION": "[ANIMATION]:",
                "VOICE": "[VOICE]:",
                "VIDEO_NOTE": "[VIDEO_NOTE]:",
                "CONTACT": "[CONTACT]:",
                "LOCATION": "[LOCATION]:",
                "VENUE": "[VENUE]:",
                "POLL": "[POLL]:",
                "WEB_PAGE": "[WEB_PAGE]:",
                "DICE": "[DICE]:",
                "GAME": "[GAME]:",
            },
            "service": {
                "service": "[Service_Message]: ",
                "PINNED_MESSAGE": "Pinned: ",
                "NEW_CHAT_TITLE": "New chat title: ",
            },
            "query_success": "Queryed history message. chat_id: {chat_id} user: {user}",
        },
        "zh-cn": {
            "help": "查询指定用户在群内的发言历史\n"
            f"使用方法: \n`,{alias_command('his')} &lt;user> [-n &lt;num>]`"
            "\n&nbsp;&nbsp; <i>user</i>: 可以是用户名或者用户id; <i>num</i>: 可选,消息数量\n"
            "你也可以直接回复一条消息，不带 <i>user</i> 参数",
            "processing": f",{alias_command('his')}: 正在查询...",
            "media": {
                "AUDIO": "[音频]:",
                "DOCUMENT": "[文档]:",
                "PHOTO": "[图片]:",
                "STICKER": "[贴纸]:",
                "VIDEO": "[视频]:",
                "ANIMATION": "[动画表情]:",
                "VOICE": "[语音]:",
                "VIDEO_NOTE": "[视频备注]:",
                "CONTACT": "[联系人]:",
                "LOCATION": "[位置]:",
                "VENUE": "[场地]:",
                "POLL": "[投票]:",
                "WEB_PAGE": "[网页]:",
                "DICE": "[骰子]:",
                "GAME": "[游戏]:",
            },
            "service": {
                "service": "[服务消息]: ",
                "PINNED_MESSAGE": "置顶了: ",
                "NEW_CHAT_TITLE": "新的群组名字: ",
            },
            "query_success": "查询历史消息完成. 群组id: {chat_id} 用户: {user}",
        },
    }
    MAX_COUNT = 30

    def __init__(self):
        try:
            self.lang_dict = self.LANGUAGES[Config.LANGUAGE]
        except:
            self.lang_dict = self.LANGUAGES["en"]

    def lang(self, text: str, default: str = "") -> str:
        res = self.lang_dict.get(text, default)
        if res == "":
            res = text
        return res


his_msg = HisMsg()


@listener(
    command="his",
    groups_only=True,
    need_admin=True,
    description=his_msg.lang("help"),
    parameters=his_msg.lang("arg", "&lt;user> [-n &lt;num>]"),
)
async def his(bot: Client, message: Message):
    user = ""
    num = 9999999
    chat_id = message.chat.id
    # 指定用户和数量
    try:
        if len(message.parameter) == 3 and message.parameter[1] == "-n":
            user = message.parameter[0]
            num = int(message.parameter[2])
        # 指定用户
        elif len(message.parameter) == 1:
            user = message.parameter[0]
        # 回复消息+指定数量
        elif (
            len(message.parameter) == 2
            and (message.reply_to_message_id is not None)
            and message.parameter[0] == "-n"
        ):
            user = int(message.reply_to_message.from_user.id)
            num = int(message.parameter[1])
        # 回复消息
        elif message.reply_to_message_id is not None:
            user = int(message.reply_to_message.from_user.id)
        # 预期外的调用方式
        else:
            return await message.edit(his_msg.lang("help"))
    except Exception:
        return await message.edit(his_msg.lang("help"))
    await message.edit(his_msg.lang("processing"))

    count = 0
    results = ""
    try:
        async for msg in bot.search_messages(
            chat_id, limit=min(num, his_msg.MAX_COUNT), from_user=user
        ):
            if msg.empty:
                continue
            count += 1
            message_link = msg.link
            message_text = msg.text

            if message_text is None and msg.media is not None:  # 媒体消息
                media_type = str(msg.media).split(".")[1]
                media_caption = msg.caption if msg.caption is not None else ""
                message_text = his_msg.lang("media")[media_type] + media_caption
            if msg.service is not None:  # 服务消息
                service_text = ""
                service_type = str(msg.service).split(".")[1]
                if (
                    service_type == "PINNED_MESSAGE"
                    and msg.pinned_message.text is not None
                ):
                    service_text = (
                        his_msg.lang("service")[service_type]
                        + msg.pinned_message.text[:20]
                    )
                elif (
                    service_type == "NEW_CHAT_TITLE" and msg.new_chat_title is not None
                ):
                    service_text = (
                        his_msg.lang("service")[service_type] + msg.new_chat_title
                    )
                else:
                    service_text = service_type
                message_text = his_msg.lang("service")["service"] + service_text

            if len(message_text) > 20:  # 消息过长截取前面的
                message_text = f"{count}.  {message_text[:20]}..."
            else:
                message_text = f"{count}. {message_text}"
            results += f'\n<a href="{message_link}">{message_text}</a> \n'

        await message.edit(
            f"<b>Message History</b> | <code>{user}</code> | 🔍 \n{results}",
            disable_web_page_preview=True,
        )
        await log(his_msg.lang("query_success").format(chat_id=chat_id, user=user))
    except Exception as e:
        await message.edit(f"[HIS_ERROR]: {e}")
        await log(f"[HIS_ERROR]: {e}")
