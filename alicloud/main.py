import contextlib
from asyncio import sleep
from datetime import datetime

from pyrogram.errors import FloodWait

from pagermaid import scheduler
from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.services import client as request, sqlite, bot
from pagermaid.enums import Message
from pagermaid.sub_utils import Sub
from pagermaid.utils import check_manage_subs, edit_delete


class AliCloud:
    def __init__(self):
        self.url = (
            "https://api.aliyundrive.com/adrive/v1/timeline/homepage/list_message"
        )
        self.data = {
            "user_id": "ec11691148db442aa7aa374ca707543c",  # 阿里盘盘酱
            "limit": 50,
            "order_by": "created_at",
            "order_direction": "DESC",
        }
        self.share_id = sqlite.get("alicloud.share_id")
        self.share_time = sqlite.get("alicloud.share_time")

    @staticmethod
    def parse_time(timestamp: int) -> str:
        """parse timestamp to date time"""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    async def get(self):
        with contextlib.suppress(Exception):
            resp = await request.post(url=self.url, json=self.data)
            results = resp.json()["items"]
            for i in results:
                recent_action = i["display_action"]
                if "掉落福利" not in recent_action:
                    continue
                return i

    async def refresh(self):
        with contextlib.suppress(Exception):
            item = await self.get()
            share_id = item["content"]["share_id"]
            share_time = item["created"] / 1000
            if share_id == self.share_id:
                return False
            self.share_id = share_id
            self.share_time = share_time
            sqlite["alicloud.share_time"] = share_id
            sqlite["alicloud.share_time"] = share_time
            return True
        return False

    def get_text(self, share_time=None, share_id=None) -> str:
        if not share_time:
            share_time = self.share_time
        if not share_id:
            share_id = self.share_id
        return (
            (
                f"最近一次阿里云盘掉落福利的时间是 {self.parse_time(share_time)}\n\n"
                f"https://www.aliyundrive.com/s/{share_id}"
            )
            if share_id
            else "未获取到阿里云盘掉落福利信息"
        )

    async def send_to_chat(self, cid: int):
        try:
            await bot.send_message(cid, self.get_text())
        except FloodWait as e:
            await sleep(e.value)
            await self.send_to_chat(cid)

    async def push(self):
        need_send = await self.refresh()
        if not need_send:
            return
        for gid in alicloud_sub.get_subs():
            try:
                await self.send_to_chat(gid)
            except Exception as e:  # noqa
                alicloud_sub.del_id(gid)


alicloud = AliCloud()
alicloud_sub = Sub("alicloud")


@scheduler.scheduled_job("interval", hours=1, id="alicloud.push")
async def alicloud_push() -> None:
    await alicloud.push()


@Hook.on_startup()
async def alicloud_startup() -> None:
    await alicloud.push()


@listener(command="alicloud", description="获取阿里云盘掉落福利信息", parameters="[订阅/退订]")
async def set_alicloud_notice(message: Message):
    if not message.arguments:
        try:
            item = await alicloud.get()
            text = alicloud.get_text(
                item["created"] / 1000, item["content"]["share_id"]
            )
        except Exception as e:  # noqa
            text = f"获取阿里云盘掉落福利信息失败：{e}"
        return await message.edit(text)
    elif message.arguments == "订阅":
        if check_manage_subs(message):
            if alicloud_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你已经订阅了阿里云盘掉落福利")
            alicloud_sub.add_id(message.chat.id)
            await message.edit("你已经成功订阅了阿里云盘掉落福利")
        else:
            await edit_delete(message, "❌ 权限不足，无法订阅阿里云盘掉落福利")
    elif message.arguments == "退订":
        if check_manage_subs(message):
            if not alicloud_sub.check_id(message.chat.id):
                return await edit_delete(message, "❌ 你还没有订阅阿里云盘掉落福利")
            alicloud_sub.del_id(message.chat.id)
            await message.edit("你已经成功退订了阿里云盘掉落福利")
        else:
            await edit_delete(message, "❌ 权限不足，无法退订阿里云盘掉落福利")
    else:
        await edit_delete(message, "❌ 未知参数")
