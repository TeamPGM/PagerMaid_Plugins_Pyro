import contextlib
import re

from typing import Optional, List

from datetime import datetime, timedelta

from pyrogram.enums import ParseMode
from pyrogram.types import ChatPermissions, Chat
from pyrogram.types.user_and_chats.user import Link

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite, Message
from pagermaid.scheduler import add_delete_message_job


class KeywordTask:
    task_id: Optional[int]
    cid: int
    key: str
    msg: str
    include: bool
    regexp: bool
    exact: bool
    case: bool
    ignore_forward: bool
    reply: bool
    delete: bool
    ban: int
    restrict: int
    delay_delete: int

    def __init__(self, task_id: Optional[int] = None, cid: int = 0, key: str = "", msg: str = "", include: bool = True, regexp: bool = False,
                 exact: bool = False, case: bool = False, ignore_forward: bool = False,
                 reply: bool = True, delete: bool = False, ban: int = 0, restrict: int = 0, delay_delete: int = 0):
        self.task_id = task_id
        self.cid = cid
        self.key = key
        self.msg = msg
        self.include = include
        self.regexp = regexp
        self.exact = exact
        self.case = case
        self.ignore_forward = ignore_forward
        self.reply = reply
        self.delete = delete
        self.ban = ban
        self.restrict = restrict
        self.delay_delete = delay_delete

    def export(self):
        return {"task_id": self.task_id, "cid": self.cid, "key": self.key, "msg": self.msg, "include": self.include, "regexp": self.regexp,
                "exact": self.exact, "case": self.case, "ignore_forward": self.ignore_forward, "reply": self.reply,
                "delete": self.delete, "ban": self.ban, "restrict": self.restrict, "delay_delete": self.delay_delete}

    def export_str(self, show_all: bool = False):
        text = f"<code>{self.task_id}</code> - "
        text += f"<code>{self.key}</code> - "
        if show_all:
            text += f"<code>{self.cid}</code> - "
        text += f"{self.msg}"
        return text

    def save_to_file(self):
        data = sqlite.get("keyword_tasks", [])
        for i in data:
            if i["task_id"] == self.task_id:
                data.remove(i)
                break
        data.append(self.export())
        sqlite["keyword_tasks"] = data

    def check_need_reply(self, message: Message) -> bool:
        if not message.text and not message.caption:
            return False
        if self.ignore_forward and message.forward_date:
            return False
        text = message.text or message.caption
        key = self.key
        if self.regexp:
            return re.search(key,text)
        if not self.case:
            text = text.lower()
            key = key.lower()
        if self.include and text.find(key) != -1:
            return True
        return bool(self.exact and text == key)

    @staticmethod
    def mention_chat(chat: Chat):
        return f'<a href="https://t.me/{chat.username}">{chat.title}</a>' if chat.username \
            else f'<code>{chat.title}</code>'

    def replace_reply(self, message: Message):
        text = self.msg
        if message.from_user:
            text = text.replace("$mention", str(Link(
                f"tg://user?id={message.from_user.id}",
                message.from_user.first_name or "Deleted Account",
                ParseMode.HTML
            )))
            text = text.replace("$code_id", str(message.from_user.id))
            text = text.replace("$code_name", message.from_user.first_name or "Deleted Account")
        elif message.sender_chat:
            text = text.replace("$mention", self.mention_chat(message.sender_chat))
            text = text.replace("$code_id", str(message.sender_chat.id))
            text = text.replace("$code_name", message.sender_chat.title)
        else:
            text = text.replace("$mention", "")
            text = text.replace("$code_id", "")
            text = text.replace("$code_name", "")
        if self.delay_delete:
            text = text.replace("$delay_delete", str(self.delay_delete))
        else:
            text = text.replace("$delay_delete", "")
        return text

    async def process_keyword(self, message: Message):
        msg = None
        text = self.replace_reply(message)
        with contextlib.suppress(Exception):
            msg = await message.reply(text, quote=self.reply, parse_mode=ParseMode.HTML)
        if self.delete:
            await message.safe_delete()
        uid = message.from_user.id if message.from_user else message.sender_chat.id
        if self.ban > 0:
            with contextlib.suppress(Exception):
                await bot.ban_chat_member(
                    message.chat.id, uid, until_date=datetime.now() + timedelta(seconds=self.ban))
        if self.restrict > 0:
            with contextlib.suppress(Exception):
                await bot.restrict_chat_member(
                    message.chat.id, uid, ChatPermissions(),
                    until_date=datetime.now() + timedelta(seconds=self.restrict))
        if self.delay_delete > 0 and msg:
            add_delete_message_job(msg, self.delay_delete)

    def parse_task(self, text: str):
        data = text.split("\n+++\n")
        if len(data) < 2:
            raise ValueError("Invalid task format")
        for i in data:
            if i == "":
                raise ValueError("Invalid task format")

        self.key = data[0]
        self.msg = data[1]

        if len(data) > 2:
            temp = data[2].split(" ")
            for i in temp:
                if i.startswith("include"):
                    self.include = True
                elif i.startswith("exact"):
                    self.include = False
                    self.exact = True
                elif i.startswith("regexp"):
                    self.regexp = True
                elif i.startswith("case"):
                    self.case = True
                elif i.startswith("ignore_forward"):
                    self.ignore_forward = True
                else:
                    raise ValueError("Invalid task format")
            if self.include and self.exact:
                raise ValueError("Invalid task format")

        if len(data) > 3:
            temp = data[3].split(" ")
            for i in temp:
                if i.startswith("reply"):
                    self.reply = True
                elif i.startswith("delete"):
                    self.delete = True
                elif i.startswith("ban"):
                    self.ban = int(i.replace("ban", ""))
                elif i.startswith("restrict"):
                    self.restrict = int(i.replace("restrict", ""))
                else:
                    raise ValueError("Invalid task format")

        if len(data) > 4:
            self.delay_delete = int(data[4])

        if self.ban < 0 or self.restrict < 0 or self.delay_delete < 0:
            raise ValueError("Invalid task format")


class KeywordTasks:
    tasks: List[KeywordTask]

    def __init__(self):
        self.tasks = []

    def add(self, task: KeywordTask):
        for i in self.tasks:
            if i.task_id == task.task_id:
                return
        self.tasks.append(task)

    def remove(self, task_id: int):
        for task in self.tasks:
            if task.task_id == task_id:
                self.tasks.remove(task)
                return True
        return False

    def get(self, task_id: int) -> Optional[KeywordTask]:
        return next((task for task in self.tasks if task.task_id == task_id), None)

    def get_all(self) -> List[KeywordTask]:
        return self.tasks

    def get_all_ids(self) -> List[int]:
        return [task.task_id for task in self.tasks]

    def print_all_tasks(self, show_all: bool = False, cid: int = 0) -> str:
        return "\n".join(task.export_str(show_all) for task in self.tasks if task.cid == cid or show_all)

    def save_to_file(self):
        data = [task.export() for task in self.tasks]
        sqlite["keyword_tasks"] = data

    def load_from_file(self):
        data = sqlite.get("keyword_tasks", [])
        for i in data:
            self.add(KeywordTask(**i))

    def get_next_task_id(self):
        return max(task.task_id for task in self.tasks) + 1 if self.tasks else 1

    def get_tasks_for_chat(self, cid: int) -> List[KeywordTask]:
        return [task for task in self.tasks if task.cid == cid]

    async def check_and_reply(self, message: Message):
        for task in self.get_tasks_for_chat(message.chat.id):
            if task.check_need_reply(message):
                with contextlib.suppress(Exception):
                    await task.process_keyword(message)


keyword_tasks = KeywordTasks()
keyword_tasks.load_from_file()


async def from_msg_get_task_id(message: Message):
    uid = -1
    try:
        uid = int(message.parameter[1])
    except ValueError:
        await message.edit("请输入正确的参数")
        message.continue_propagation()
    ids = keyword_tasks.get_all_ids()
    if uid not in ids:
        await message.edit("该任务不存在")
        message.continue_propagation()
    return uid


@listener(command="keyword",
          parameters="指定参数",
          need_admin=True,
          description="关键词回复\n\nhttps://telegra.ph/PagerMaid-keyword-07-12")
async def keyword_set(message: Message):
    if message.arguments == "h" or len(message.parameter) == 0:
        return await message.edit("关键词回复\n\nhttps://telegra.ph/PagerMaid-keyword-07-12")
    if len(message.parameter) == 1 and message.parameter[0] == "list":
        if keyword_tasks.get_all_ids():
            return await message.edit(
                f"关键词任务：\n\n{keyword_tasks.print_all_tasks(show_all=False, cid=message.chat.id)}")
        else:
            return await message.edit("没有关键词任务。")
    if len(message.parameter) == 2:
        if message.parameter[0] == "rm":
            if uid := await from_msg_get_task_id(message):
                keyword_tasks.remove(uid)
                keyword_tasks.save_to_file()
                keyword_tasks.load_from_file()
                return await message.edit(f"已删除任务 {uid}")
        elif message.parameter[0] == "list":
            if keyword_tasks.get_all_ids():
                return await message.edit(
                    f"关键词任务：\n\n{keyword_tasks.print_all_tasks(show_all=True)}")
            else:
                return await message.edit("没有关键词任务。")
    # add task
    task = KeywordTask(keyword_tasks.get_next_task_id())
    task.cid = message.chat.id
    try:
        task.parse_task(message.arguments)
    except Exception as e:
        return await message.edit(f"参数错误：{e}")
    keyword_tasks.add(task)
    keyword_tasks.save_to_file()
    keyword_tasks.load_from_file()
    await message.edit(f"已添加关键词任务 {task.task_id}")


@listener(is_plugin=True, incoming=True, outgoing=False)
async def process_keyword(message):
    with contextlib.suppress(Exception):
        await keyword_tasks.check_and_reply(message)
