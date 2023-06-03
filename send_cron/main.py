import contextlib
import datetime

from typing import Optional, List

from pagermaid import bot
from pagermaid.listener import listener
from pagermaid.scheduler import scheduler
from pagermaid.single_utils import sqlite, Message
from pagermaid.utils import alias_command


class SendTask:
    task_id: Optional[int]
    cid: int
    msg: str
    cron: str
    pause: bool

    def __init__(self, task_id: int, cid: int = 0, msg: str = "", cron: str = "", pause: bool = False):
        self.task_id = task_id
        self.cid = cid
        self.msg = msg
        self.cron = cron
        self.pause = pause

    def export(self):
        return {"task_id": self.task_id, "cid": self.cid, "msg": self.msg, "cron": self.cron, "pause": self.pause}

    def get_job(self):
        return scheduler.get_job(f"send_cron|{self.cid}|{self.task_id}")

    def remove_job(self):
        if self.get_job():
            scheduler.remove_job(f"send_cron|{self.cid}|{self.task_id}")

    def export_str(self, show_all: bool = False):
        text = f"<code>{self.task_id}</code> - " \
               f"<code>{self.cron}</code> -"
        if job := self.get_job():
            time: datetime.datetime = job.next_run_time
            text += f"<code>{time.strftime('%Y-%m-%d %H:%M:%S')}</code> - "
        else:
            text += "<code>未运行</code> - "
        if show_all:
            text += f"<code>{self.cid}</code> - "
        text += f"{self.msg}"
        return text

    @staticmethod
    def parse_cron_kwargs(text: str):
        data = text.split(" ")
        return {
            "second": data[0],
            "minute": data[1],
            "hour": data[2],
            "day": data[3],
            "month": data[4],
            "day_of_week": data[5],
        }

    @property
    def cron_kwargs(self):
        return self.parse_cron_kwargs(self.cron)

    def parse_task(self, text: str):
        self.msg = "|".join(text.split("|")[1:]).strip()
        if not self.msg:
            raise ValueError("No message provided")
        text = text.split("|")[0].strip()
        data = text.split(" ")
        if len(data) != 6:
            raise ValueError("Invalid crontab format")
        try:
            scheduler._create_trigger("cron", self.parse_cron_kwargs(text))
        except Exception as e:
            raise ValueError(f"Invalid crontab format: {e}") from e
        self.cron = text


class SendTasks:
    tasks: List[SendTask]

    def __init__(self):
        self.tasks = []

    def add(self, task: SendTask):
        for i in self.tasks:
            if i.task_id == task.task_id:
                return
        self.tasks.append(task)

    def remove(self, task_id: int):
        for task in self.tasks:
            if task.task_id == task_id:
                task.remove_job()
                self.tasks.remove(task)
                return True
        return False

    def get(self, task_id: int) -> Optional[SendTask]:
        return next((task for task in self.tasks if task.task_id == task_id), None)

    def get_all(self) -> List[SendTask]:
        return self.tasks

    def get_all_ids(self) -> List[int]:
        return [task.task_id for task in self.tasks]

    def print_all_tasks(self, show_all: bool = False, cid: int = 0) -> str:
        return "\n".join(task.export_str(show_all) for task in self.tasks if task.cid == cid or show_all)

    def save_to_file(self):
        data = [task.export() for task in self.tasks]
        sqlite["send_cron_tasks"] = data

    def load_from_file(self):
        data = sqlite.get("send_cron_tasks", [])
        for i in data:
            self.add(SendTask(**i))

    def pause_task(self, task_id):
        if task := self.get(task_id):
            task.pause = True
            task.remove_job()
            self.save_to_file()
            return True
        return False

    @staticmethod
    async def send_message(task: SendTask, _: "SendTasks"):
        with contextlib.suppress(Exception):
            await bot.send_message(task.cid, task.msg)

    def register_cron_task(self, task: SendTask):
        scheduler.add_job(
            self.send_message,
            "cron",
            id=f"send_cron|{task.cid}|{task.task_id}",
            name=f"send_cron|{task.cid}|{task.task_id}",
            args=[task, self],
            **task.cron_kwargs,
        )

    def register_single_task(self, task: SendTask):
        if task.pause:
            return
        self.register_cron_task(task)

    def resume_task(self, task_id: int):
        if task := self.get(task_id):
            task.pause = False
            self.register_single_task(task)
            self.save_to_file()
            return True
        return False

    def register_all_tasks(self):
        for task in self.tasks:
            self.register_single_task(task)

    def get_next_task_id(self):
        return max(task.task_id for task in self.tasks) + 1 if self.tasks else 1


send_cron_tasks = SendTasks()
send_cron_tasks.load_from_file()
send_cron_tasks.register_all_tasks()

send_help_msg = f"""
定时发送消息。
,{alias_command("send_cron")} crontab 表达式 | 消息内容
i.e.
,{alias_command("send_cron")} 59 59 23 * * * | 又是无所事事的一天呢。
,{alias_command("send_cron")} 0 * * * * * | 又过去了一分钟。


,{alias_command("send_cron")} rm 2 - 删除某个任务
,{alias_command("send_cron")} pause 1 - 暂停某个任务
,{alias_command("send_cron")} resume 1 - 恢复某个任务
,{alias_command("send_cron")} list <all> - 获取任务列表
"""


async def from_msg_get_task_id(message: Message):
    uid = -1
    try:
        uid = int(message.parameter[1])
    except ValueError:
        await message.edit("请输入正确的参数")
        message.continue_propagation()
    ids = send_cron_tasks.get_all_ids()
    if uid not in ids:
        await message.edit("该任务不存在")
        message.continue_propagation()
    return uid


@listener(
    command="send_cron",
    parameters="crontab 表达式 | 消息内容",
    need_admin=True,
    description=f"定时发送消息\n请使用 ,{alias_command('send_cron')} h 查看可用命令",
)
async def send_cron(message: Message):
    if message.arguments == "h" or len(message.parameter) == 0:
        return await message.edit(send_help_msg)
    if len(message.parameter) == 1:
        if message.parameter[0] != "list":
            return await message.edit("请输入正确的参数")
        if send_cron_tasks.get_all_ids():
            return await message.edit(
                f"已注册的任务：\n\n{send_cron_tasks.print_all_tasks(show_all=False, cid=message.chat.id)}")
        else:
            return await message.edit("没有已注册的任务。")
    if len(message.parameter) == 2:
        if message.parameter[0] == "rm":
            if uid := await from_msg_get_task_id(message):
                send_cron_tasks.remove(uid)
                send_cron_tasks.save_to_file()
                send_cron_tasks.load_from_file()
                return await message.edit(f"已删除任务 {uid}")
        elif message.parameter[0] == "pause":
            if uid := await from_msg_get_task_id(message):
                send_cron_tasks.pause_task(uid)
                return await message.edit(f"已暂停任务 {uid}")
        elif message.parameter[0] == "resume":
            if uid := await from_msg_get_task_id(message):
                send_cron_tasks.resume_task(uid)
                return await message.edit(f"已恢复任务 {uid}")
        elif message.parameter[0] == "list":
            if send_cron_tasks.get_all_ids():
                return await message.edit(
                    f"已注册的任务：\n\n{send_cron_tasks.print_all_tasks(show_all=True)}")
            else:
                return await message.edit("没有已注册的任务。")
    # add task
    task = SendTask(send_cron_tasks.get_next_task_id())
    task.cid = message.chat.id
    try:
        task.parse_task(message.arguments)
    except Exception as e:
        return await message.edit(f"参数错误：{e}")
    send_cron_tasks.add(task)
    send_cron_tasks.register_single_task(task)
    send_cron_tasks.save_to_file()
    send_cron_tasks.load_from_file()
    await message.edit(f"已添加任务 {task.task_id}")
