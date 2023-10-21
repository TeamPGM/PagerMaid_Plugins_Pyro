from asyncio import sleep
from typing import Dict, List

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired, UserAdminInvalid, FloodWait
from pyrogram.raw.functions.channels import GetAdminLog
from pyrogram.raw.types import ChannelAdminLogEventsFilter, ChannelAdminLogEventActionUpdatePinned
from pyrogram.raw.types.channels import AdminLogResults

from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.services import bot


async def get_admin_log(cid: int) -> AdminLogResults:
    d: AdminLogResults = await bot.invoke(
        GetAdminLog(
            channel=await bot.resolve_peer(cid),
            q="",
            max_id=0,
            min_id=0,
            limit=100,
            events_filter=ChannelAdminLogEventsFilter(pinned=True),
        )
    )
    return d


def get_num_map(events: AdminLogResults) -> Dict[int, List[int]]:
    num_map: Dict[int, List[int]] = {}
    for event in events.events:
        if isinstance(event.action, ChannelAdminLogEventActionUpdatePinned):
            if event.action.message.pinned:
                continue
            num = num_map.get(event.user_id, [])
            num.append(event.action.message.id)
            num_map[event.user_id] = num
    return num_map


async def try_ask_admin(message: Message, num_map: Dict[int, List[int]]) -> int:
    nums = sorted(num_map.keys(), key=lambda x: len(num_map[x]), reverse=True)
    text = "请发送执行误取消置顶操作的管理员 id：\n\n"
    for idx in nums:
        text += f"`{idx}` - 取消 {len(num_map[idx])} 条\n"
    await message.edit(text)
    try:
        async with bot.conversation(
                message.chat.id, filters=filters.user(message.from_user.id)
        ) as conv:
            await sleep(.1)
            res: Message = await conv.get_response()
            await res.safe_delete()
            uid = int(res.text)
            if uid not in num_map:
                raise ValueError
    except ValueError:
        await message.edit("错误：管理员 id 不正确")
        return 0
    return uid


async def pin_one(message: Message, mid: int):
    try:
        await bot.pin_chat_message(message.chat.id, mid, disable_notification=True)
    except ChatAdminRequired:
        return
    except UserAdminInvalid:
        return
    except FloodWait as e:
        await message.edit(f"触发限制，睡眠 {e.value} 秒")
        await sleep(e.value)
        await pin_one(message, mid)


async def try_restore_pin(message: Message, ids: List[int]):
    msgs = await bot.get_messages(message.chat.id, ids)
    new_ids = [i.id for i in msgs if not i.pinned_message]
    error = ""
    for idx, i in enumerate(new_ids):
        if (idx + 1) % 5 == 0:
            await message.edit(f"正在恢复第 {idx + 1} 条置顶...")
        try:
            await pin_one(message, i)
        except Exception as e:
            error += f"恢复第 {idx + 1} 条置顶失败 ：{e}\n"
        await sleep(3)
    if error:
        await message.edit(error)
    else:
        await message.edit("已恢复所有消息的置顶")


@listener(
    command="restore_pin",
    description="恢复管理员误取消的置顶",
    groups_only=True,
    need_admin=True,
)
async def restore_pin(message: Message):
    if not message.from_user:
        return
    message = await message.edit("正在获取管理员日志...")
    try:
        events = await get_admin_log(message.chat.id)
    except Exception as e:
        return await message.edit(f"请求管理员日志失败：{e}")
    if not events.events:
        return await message.edit("管理员日志为空，无法恢复")
    num_map = get_num_map(events)
    if not num_map:
        return await message.edit("管理员日志为空，无法恢复")
    admin_id = await try_ask_admin(message, num_map)
    if admin_id not in num_map:
        return
    await message.edit("尝试恢复置顶...")
    await try_restore_pin(message, num_map[admin_id])
