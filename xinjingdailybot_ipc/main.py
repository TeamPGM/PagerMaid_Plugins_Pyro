'''
XingjingdailyBot 自动转载插件
by chr233
'''

from dataclasses import dataclass
from enum import IntFlag, auto, unique
from os import path
from traceback import format_exc
from typing import  Dict, List, Optional, Tuple
from urllib import parse

from time import time
from pagermaid import bot, scheduler
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove, sqlite
from pagermaid.utils import alias_command, client

cmd_name = "xinjingdailybot"
alias_cmd_name = alias_command(cmd_name)

help_msg = "\n".join([
    "参数无效, 可用指令:\n",
    f"`,{alias_cmd_name} ipc http://example.com:8123`",
    "设置 XinjingdailyBot WebAPI 地址\n",
    f"`,{alias_cmd_name} token xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`",
    "设置 IPC 用户 Token, 对投稿机器人使用命令 /token 获取\n",
    f"`,{alias_cmd_name} test`",
    "测试 XinjingdailyBot WebAPI 配置是否有有效\n",
    f"`,{alias_cmd_name} status`",
    "查看 XinjingdailyBot WebAPI 连接配置\n",
    f"`,{alias_cmd_name} channel`",
    "获取正在监听的频道列表, 列表中的频道有更新时会自动推送至投稿机器人\n",
    f"`,{alias_cmd_name} add channelId [watch_type]`",
    "添加对指定频道的监听, 默认只监听多媒体消息\n",
    f"`,{alias_cmd_name} del channelId`",
    "删除对指定频道的监听\n",
    f"`,{alias_cmd_name} set channelId [watch_type]`",
    "修改对指定频道的监听类型\n",
    "WatchType类型 (Flag类型)",
    "Text: 1",
    "Photo: 2",
    "Audio: 4",
    "Video: 8",
    "Voice: 16",
    "Document: 32",
    "Animation: 64",
    "可以任意组合, 比如监听Photo和Video消息, 值为10"
])


@unique
class WatchType(IntFlag):
    Text = auto()
    Photo = auto()
    Audio = auto()
    Video = auto()
    Voice = auto()
    Document = auto()
    Animation = auto()
    Media = Photo | Audio | Video | Voice | Document | Animation
    All = Media | Text


@dataclass
class CreatePost:
    text: str
    post_type: int
    has_spoiler: bool
    channel_id: Optional[int]
    channel_name: Optional[str]
    channel_title: Optional[str]
    channel_msg_id: Optional[int]


class XjbClient:
    _ipc: str
    _token: str

    def __init__(self) -> None:
        self._ipc = sqlite.get("xjb_ipc", "")
        self._token = sqlite.get("xjb_token", "")

    @property
    def ipc(self):
        return self._ipc

    @ipc.setter
    def ipc(self, ipc: str):
        self._ipc = ipc
        sqlite["xjb_ipc"] = ipc

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token: str):
        self._token = token
        sqlite["xjb_token"] = token

    def _make_header(self) -> Dict[str, str]:
        headers = {"Authentication": self._token}
        return headers

    def _make_url(self, path: str) -> str:
        url = parse.urljoin(self._ipc, path)
        return url

    async def test_ipc(self):
        try:
            url = self._make_url("/Api/Post/TestToken")
            headers = self._make_header()
            resp = await client.post(url=url, headers=headers)
            return resp
        except Exception as ex:
            return None

    async def create_post(self, post: CreatePost, file_paths: List[str]):
        try:
            url = self._make_url("/Api/Post/CreatePost")
            headers = self._make_header()
            data = {
                'HasSpoiler': post.has_spoiler,
                'Text': post.text,
                'ChannelName': post.channel_name,
                'ChannelTitle': post.channel_title,
                'ChannelMsgID': post.channel_msg_id,
                'PostType': post.post_type,
                'ChannelID': post.channel_id,
            }
            files = [(path.basename(x), open(x, "rb")) for x in file_paths]
            resp = await client.post(url=url, data=data, files=files, headers=headers)
            return resp
        except Exception:
            err = format_exc()
            await xjb_core.send_log(err)
        finally:
            for file_path in file_paths:
                try:
                    safe_remove(file_path)
                except:
                    err = format_exc()
                    await xjb_core.send_log(err)


class XjbCore:
    _channels: Dict[int, WatchType]
    _log_chat: int

    def __init__(self) -> None:
        self._channels = sqlite.get("xjb_channels", {})
        self._log_chat = sqlite.get("xjb_log", 0)

    @property
    def channels(self):
        return self._channels

    def save_config(self) -> None:
        sqlite["xjb_channels"] = self._channels

    async def send_log(self, text: str) -> None:
        if self._log_chat != 0:
            try:
                await bot.send_message(self._log_chat, text)
            except:
                ...

    async def cmd_test(self) -> str:
        resp = await xjb_client.test_ipc()
        if resp:
            if resp.status_code == 200:
                json = resp.json()
                result = json.get("result", {})
                user_name = result.get("userName", None)
                user_id = result.get("userID", None)
                uid = result.get("uid", None)
                nick_name = result.get("nickName", None)

                msg = '\n'.join([
                    "连接到 Xinjingdaily Bot 成功",
                    "当前用户信息:",
                    f"UID: {uid}",
                    f"User Id: {user_id}",
                    f"User Name: {user_name}",
                    f"Nick Name: {nick_name}",
                    "监听频道的消息将会以此用户的身份投稿"
                ])
                return msg
            elif resp.status_code == 401:
                return "连接到 Xinjingdaily Bot 失败\nToken 无效 请检查 Token 设置"

            return f"连接到 Xinjingdaily Bot 失败\n代码 {resp.status_code} 请检查 IPC 和 Token 设置"
        else:
            return "连接到 Xinjingdaily Bot 失败\n请检查 IPC 设置"

    def cmd_status(self) -> str:
        return f"IPC: `{xjb_client.ipc}`\nToken: `{xjb_client.token}`"

    def cmd_ipc(self, ipc: str) -> str:
        try:
            url = parse. urlparse(ipc, allow_fragments=False)
            xjb_client.ipc = f"{url.scheme}://{url.netloc}"
            return "IPC 路径设置成功"

        except ValueError:
            return "IPC 路径不是有效的URL"

    def cmd_token(self, token: str) -> str:
        xjb_client.token = token
        return f"Token 设置成功, 使用命令 `,{alias_cmd_name} test` 测试连接"

    def cmd_channel(self) -> str:
        if len(self._channels) == 0:
            return "监听的频道列表为空\n使用 `,xjb add channel_id [watch_type]` 添加频道监听"

        msg = ["监听的频道, 监听类型:"]
        for i, (channel, type) in enumerate(self._channels.items(), 1):
            name, _ = self.watch_type(type)
            msg.append(f"[{i} {channel}](https://t.me/c/{channel}), {name}")

        return '\n'.join(msg)

    @staticmethod
    def watch_type(watch_type: str) -> Tuple[str, WatchType]:
        type = WatchType(int(watch_type))
        str_list = []
        if type & WatchType.Text:
            str_list.append("文本")
        if type & WatchType.Photo:
            str_list.append("图片")
        if type & WatchType.Audio:
            str_list.append("音乐")
        if type & WatchType.Video:
            str_list.append("视频")
        if type & WatchType.Voice:
            str_list.append("语音")
        if type & WatchType.Document:
            str_list.append("文件")
        if type & WatchType.Animation:
            str_list.append("GIF")

        if len(str_list) == 0:
            str_list.append("无")

        result = ' '.join(str_list)
        return (result, type)

    def cmd_add(self, channel_id: str, watch_type: str) -> str:
        try:
            chat_id = int(channel_id)
            name, type = self.watch_type(watch_type)

            if chat_id not in self._channels:
                self._channels[chat_id] = type
                self.save_config()
                return f"监听频道 {chat_id} 添加成功\n监听类型 {name}"
            else:
                return f"监听频道 {chat_id} 已存在, 无需重复添加"

        except ValueError:
            return f"监听频道 {chat_id} 无效, 只能为整数"

    def cmd_del(self, channel_id: str) -> str:
        try:
            chat_id = int(channel_id)

            if chat_id in self._channels:
                self._channels.pop(chat_id)
                self.save_config()
                return f"监听频道 {chat_id} 删除成功"
            else:
                return f"监听频道 {chat_id} 不存在, 无法删除"

        except ValueError:
            return f"监听频道 {chat_id} 无效, 只能为整数"

    def cmd_set(self, channel_id: str, watch_type: str) -> str:
        try:
            chat_id = int(channel_id)
            name, type = self.watch_type(watch_type)

            if chat_id in self._channels:
                self._channels[chat_id] = type
                self.save_config()
                return f"监听频道 {chat_id} 修改成功\n监听类型 {name}"
            else:
                return f"监听频道 {chat_id} 不存在, 无法修改"

        except ValueError:
            return f"监听频道 {chat_id} 无效, 只能为整数"

    def cmd_log(self, chat_id: int):
        self._log_chat = chat_id if self._log_chat != chat_id else 0
        sqlite["xjb_log"] = self._log_chat
        return "开启日志成功, 日志将输出到此会话" if self._log_chat != 0 else "关闭日志成功"


class XjbCache:
    _message_groups: Dict[str, Tuple[CreatePost, List[str]]]
    _message_ttl: Dict[str, int]

    def __init__(self) -> None:
        self._message_groups = {}
        self._message_ttl = {}

    def add_message(self, group_id: str, post: CreatePost, file_path: str):
        if group_id not in self._message_groups:
            self._message_groups[group_id] = (post, [file_path])
            ttl = int(time()) + 5
            self._message_ttl[group_id] = ttl

        else:
            self._message_groups[group_id][1].append(file_path)

    async def check_ttl(self):
        group_ids = []
        now = int(time())
        for (group_id, ttl) in self._message_ttl.items():
            if now > ttl:
                group_ids.append(group_id)

        for group_id in group_ids:
            (post, file_paths) = self._message_groups.pop(group_id, (None, None))
            if post and file_paths:
                await xjb_client.create_post(post, file_paths)


xjb_client = XjbClient()
xjb_core = XjbCore()
xjb_cache = XjbCache()


@scheduler.scheduled_job(trigger="interval",  seconds=2, id="xinjingdailybot.check_ttl")
async def check_ttl() -> None:
    await xjb_cache.check_ttl()


@listener(is_plugin=True, incoming=True, outgoing=False)
async def process_message(msg: Message):
    try:
        chat = msg.chat
        if chat.id not in xjb_core.channels:
            return

        type = xjb_core.channels[chat.id]

        file_path = None
        post = None

        if type & WatchType.Text and msg.text:
            post = CreatePost(msg.text, 1, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
        elif type & WatchType.Photo and msg.photo:
            post = CreatePost(msg.caption, 2, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
            file_path = await msg.download()
        elif type & WatchType.Audio and msg.audio:
            post = CreatePost(msg.caption, 4, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
            file_path = await msg.download()
        elif type & WatchType.Video and msg.video:
            post = CreatePost(msg.caption, 8, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
            file_path = await msg.download()
        elif type & WatchType.Voice and msg.voice:
            post = CreatePost(msg.caption, 16, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
            file_path = await msg.download()
        elif type & WatchType.Document and msg.document:
            post = CreatePost(msg.caption, 32, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
            file_path = await msg.download()
        elif type & WatchType.Animation and msg.animation:
            post = CreatePost(msg.caption, 64, msg.has_media_spoiler,
                              chat.id, chat.username, chat.title, msg.id)
            file_path = await msg.download()

        if post:
            if msg.media_group_id:
                # 媒体组消息先进行缓存, 然后由定时任务触发投稿
                xjb_cache.add_message(msg.media_group_id, post, file_path)
                return
            else:
                # 非媒体组消息, 直接投稿
                resp = await xjb_client.create_post(post, [file_path])
                if resp:
                    await xjb_core.send_log(resp.text)

    except Exception:
        err = format_exc()
        await xjb_core.send_log(err)


@listener(command="xinjingdailybot",
          description="设置投稿机器人",
          parameters="test|status|ipc|token|channel|add|del",
          usage="设置投稿机器人")
async def response_cmd(msg: Message):
    try:
        param = msg.parameter
        cmd = param[0]
        arg_len = len(param)

        resp = None
        if cmd == "test":
            resp = await xjb_core.cmd_test()

        elif cmd == "status":
            resp = xjb_core.cmd_status()

        elif cmd == "ipc" and arg_len > 1:
            resp = xjb_core.cmd_ipc(param[1])

        elif cmd == "token" and arg_len > 1:
            resp = xjb_core.cmd_token(param[1])

        elif cmd == "channel":
            resp = xjb_core.cmd_channel()

        elif cmd == "add" and arg_len > 2:
            resp = xjb_core.cmd_add(param[1], param[2])

        elif cmd == "add" and arg_len > 1:
            resp = xjb_core.cmd_add(param[1], str(int(WatchType.Media)))

        elif cmd == "del" and arg_len > 1:
            resp = xjb_core.cmd_del(param[1])

        elif cmd == "set" and arg_len > 2:
            resp = xjb_core.cmd_set(param[1], param[2])

        elif cmd == "set" and arg_len > 1:
            resp = xjb_core.cmd_set(param[1], str(int(WatchType.Media)))

        elif cmd == "log":
            resp = xjb_core.cmd_log(msg.chat.id)

        if not resp:
            await msg.edit(help_msg)
        else:
            await msg.edit(resp)
    except Exception:
        err = format_exc()
        await xjb_core.send_log(err)
