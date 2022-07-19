import contextlib
import datetime
import pytz

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
    interval: bool
    cron: bool
    pause: bool
    time_limit: int
    hour: str = "0"
    minute: str = "0"
    second: str = "0"

    def __init__(self, task_id: Optional[int] = None, cid: int = 0, msg: str = "", interval: bool = False,
                 cron: bool = False, pause: bool = False, time_limit: int = -1,
                 hour: str = "0", minute: str = "0", second: str = "0"):
        self.task_id = task_id
        self.cid = cid
        self.msg = msg
        self.interval = interval
        self.cron = cron
        self.pause = pause
        self.time_limit = time_limit
        self.hour = hour
        self.minute = minute
        self.second = second

    def reduce_time(self):
        if self.time_limit > 0:
            self.time_limit -= 1
            self.save_to_file()

    def export(self):
        return {"task_id": self.task_id, "cid": self.cid, "msg": self.msg, "interval": self.interval,
                "cron": self.cron, "pause": self.pause, "time_limit": self.time_limit, "hour": self.hour,
                "minute": self.minute, "second": self.second}

    def get_job(self):
        return scheduler.get_job(f"sendat|{self.cid}|{self.task_id}")

    def remove_job(self):
        if self.get_job():
            scheduler.remove_job(f"sendat|{self.cid}|{self.task_id}")

    def export_str(self, show_all: bool = False):
        text = f"<code>{self.task_id}</code> - " \
               f"<code>{'循环任务' if self.interval else '单次任务'}</code> - "
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
    def check_time(time: str, min_value: int = None, max_value: int = None) -> str:
        if max_value and int(time) > max_value:
            raise ValueError(f"Time value {time} is too large")
        if min_value and int(time) < min_value:
            raise ValueError(f"Time value {time} is too small")
        if int(time) < 0:
            raise ValueError(f"Time value {time} is too small")
        return time

    def save_to_file(self):
        data = sqlite.get("sendat_tasks", [])
        for i in data:
            if i["task_id"] == self.task_id:
                data.remove(i)
                break
        data.append(self.export())
        sqlite["sendat_tasks"] = data

    @staticmethod
    def parse_date(date: str):
        datetime.datetime.strptime(date, "%H:%M:%S")

    def parse_task(self, text: str):
        self.msg = "|".join(text.split("|")[1:]).strip()
        if not self.msg:
            raise ValueError("No message provided")
        text = text.split("|")[0].strip()
        if "every" in text:
            self.interval = True
            text = text.replace("every", "").strip()
        data = text.split(" ")
        if len(data) % 2:
            raise ValueError("Invalid task format")
        format_right = False
        no_date = True
        for i in range(1, len(data)):
            if data[i] == "seconds":
                format_right = True
                self.second = self.check_time(data[i - 1], 0, 60)
            elif data[i] == "minutes":
                format_right = True
                self.minute = self.check_time(data[i - 1], 0, 60)
            elif data[i] == "hours":
                format_right = True
                self.hour = self.check_time(data[i - 1], 0, 24)
            elif data[i] == "times":
                self.interval = True
                self.time_limit = int(self.check_time(data[i - 1], min_value=1))
            elif data[i] == "date":
                format_right = True
                no_date = False
                self.cron = True
                date = datetime.datetime.strptime(data[i - 1], "%H:%M:%S")
                self.hour = str(date.hour)
                self.minute = str(date.minute)
                self.second = str(date.second)
        if not format_right:
            raise ValueError("Invalid task format")
        if no_date:
            self.interval = True
            self.time_limit = self.time_limit if self.time_limit > 0 else 1


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
        sqlite["sendat_tasks"] = data

    def load_from_file(self):
        data = sqlite.get("sendat_tasks", [])
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
    async def send_message(task: SendTask, tasks):
        with contextlib.suppress(Exception):
            await bot.send_message(task.cid, task.msg)
        task.reduce_time()
        if task.time_limit == 0:
            task.remove_job()
            tasks.remove(task.task_id)
        if not task.interval:
            task.remove_job()

    def register_interval_task(self, task: SendTask):
        scheduler.add_job(self.send_message,
                          "interval",
                          id=f"sendat|{task.cid}|{task.task_id}",
                          name=f"sendat|{task.cid}|{task.task_id}",
                          hours=int(task.hour),
                          minutes=int(task.minute),
                          seconds=int(task.second),
                          args=[task, self])

    def register_cron_task(self, task: SendTask):
        scheduler.add_job(self.send_message,
                          "cron",
                          id=f"sendat|{task.cid}|{task.task_id}",
                          name=f"sendat|{task.cid}|{task.task_id}",
                          hour=int(task.hour),
                          minute=int(task.minute),
                          second=int(task.second),
                          args=[task, self])

    def register_date_task(self, task: SendTask):
        date_now = datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
        date_will = date_now.replace(hour=int(task.hour), minute=int(task.minute), second=int(task.second))
        if date_will < date_now:
            date_will += datetime.timedelta(days=1)
        scheduler.add_job(self.send_message,
                          "date",
                          id=f"sendat|{task.cid}|{task.task_id}",
                          name=f"sendat|{task.cid}|{task.task_id}",
                          run_date=date_will,
                          args=[task, self])

    def register_single_task(self, task: SendTask):
        if task.pause or task.time_limit == 0:
            return
        if task.interval:
            if task.cron:
                self.register_cron_task(task)
            else:
                self.register_interval_task(task)
        else:
            self.register_date_task(task)

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


send_tasks = SendTasks()
send_tasks.load_from_file()
send_tasks.register_all_tasks()

send_help_msg = f"""
定时发送消息。
,{alias_command("sendat")} 时间 | 消息内容
i.e.
,{alias_command("sendat")} 16:00:00 date | 投票截止！
,{alias_command("sendat")} every 23:59:59 date | 又是无所事事的一天呢。
,{alias_command("sendat")} every 1 minutes | 又过去了一分钟。
,{alias_command("sendat")} 3 times 1 minutes | 此消息将出现三次，间隔均为一分钟。


,{alias_command("sendat")} rm 2 - 删除某个任务
,{alias_command("sendat")} pause 1 - 暂停某个任务
,{alias_command("sendat")} resume 1 - 恢复某个任务
,{alias_command("sendat")} list <all> - 获取任务列表
"""


async def from_msg_get_task_id(message: Message):
    uid = -1
    try:
        uid = int(message.parameter[1])
    except ValueError:
        await message.edit("请输入正确的参数")
        message.continue_propagation()
    ids = send_tasks.get_all_ids()
    if uid not in ids:
        await message.edit("该任务不存在")
        message.continue_propagation()
    return uid


@listener(command="sendat",
          parameters="时间 | 消息内容",
          need_admin=True,
          description=f"定时发送消息\n请使用 ,{alias_command('sendat')} h 查看可用命令")
async def send_at(message: Message):
    if message.arguments == "h" or len(message.parameter) == 0:
        return await message.edit(send_help_msg)
    if len(message.parameter) == 1:
        if message.parameter[0] != "list":
            return await message.edit("请输入正确的参数")
        if send_tasks.get_all_ids():
            return await message.edit(
                f"已注册的任务：\n\n{send_tasks.print_all_tasks(show_all=False, cid=message.chat.id)}")
        else:
            return await message.edit("没有已注册的任务。")
    if len(message.parameter) == 2:
        if message.parameter[0] == "rm":
            if uid := await from_msg_get_task_id(message):
                send_tasks.remove(uid)
                send_tasks.save_to_file()
                send_tasks.load_from_file()
                return await message.edit(f"已删除任务 {uid}")
        elif message.parameter[0] == "pause":
            if uid := await from_msg_get_task_id(message):
                send_tasks.pause_task(uid)
                return await message.edit(f"已暂停任务 {uid}")
        elif message.parameter[0] == "resume":
            if uid := await from_msg_get_task_id(message):
                send_tasks.resume_task(uid)
                return await message.edit(f"已恢复任务 {uid}")
        elif message.parameter[0] == "list":
            if send_tasks.get_all_ids():
                return await message.edit(
                    f"已注册的任务：\n\n{send_tasks.print_all_tasks(show_all=True)}")
            else:
                return await message.edit("没有已注册的任务。")
    # add task
    task = SendTask(send_tasks.get_next_task_id())
    task.cid = message.chat.id
    try:
        task.parse_task(message.arguments)
    except Exception as e:
        return await message.edit(f"参数错误：{e}")
    send_tasks.add(task)
    send_tasks.register_single_task(task)
    send_tasks.save_to_file()
    send_tasks.load_from_file()
    await message.edit(f"已添加任务 {task.task_id}")
