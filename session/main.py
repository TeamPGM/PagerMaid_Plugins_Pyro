import contextlib

from typing import List, Optional

from datetime import datetime

from pyrogram.enums import ChatType
from pyrogram.raw.functions.account import GetAuthorizations, ResetAuthorization
from pyrogram.raw.types import Authorization

from pagermaid.listener import listener
from pagermaid.single_utils import Message
from pagermaid.utils import alias_command
from pagermaid import bot


async def get_all_session() -> List[Authorization]:
    data = await bot.invoke(GetAuthorizations())
    return data.authorizations


async def filter_session(hash_start: str) -> Optional[Authorization]:
    try:
        hash_start = int(hash_start)
        if len(str(hash_start)) != 6 and hash_start != 0:
            return None
    except ValueError:
        return None
    return next((session for session in await get_all_session() if str(session.hash).startswith(str(hash_start))), None)


async def kick_session(session: Authorization) -> bool:
    if session.hash != 0:
        with contextlib.suppress(Exception):
            return await bot.invoke(ResetAuthorization(hash=session.hash))
    return False


def format_timestamp(timestamp: int) -> str:
    datetime_obj = datetime.fromtimestamp(timestamp)
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")


def format_session(session: Authorization, private: bool = True) -> str:
    text = f"标识符：<code>{str(session.hash)[:6]}</code>\n" \
           f"设备型号：<code>{session.device_model}</code>\n" \
           f"设备平台：<code>{session.platform}</code>\n" \
           f"系统版本：<code>{session.system_version}</code>\n" \
           f"应用名称：<code>{session.app_name}</code>\n" \
           f"应用版本：<code>{session.app_version}</code>\n" \
           f"官方应用：<code>{'是' if session.official_app else '否'}</code>\n" \
           f"登录时间：<code>{format_timestamp(session.date_created)}</code>\n" \
           f"在线时间：<code>{format_timestamp(session.date_active)}</code>"
    if private:
        text += f"\nIP：<code>{session.ip}</code>\n" \
                f"地理位置：<code>{session.country}</code>"
    if session.hash != 0:
        text += f"\n\n使用命令 <code>,{alias_command('session')} 注销 {str(session.hash)[:6]}</code> 可以注销此会话。"
    return text


async def count_platform(private: bool = True) -> str:
    sessions = await get_all_session()
    if not sessions:
        return "无任何在线设备？"
    platform_count = {}
    text = f"共有 {len(sessions)} 台设备在线，分别是：\n\n"
    for session in sessions:
        if session.platform in platform_count:
            platform_count[session.platform] += 1
        else:
            platform_count[session.platform] = 1
        text += f"<code>{str(session.hash)[:6]}</code> - <code>{session.device_model}</code>"
        if private:
            text += f" - <code>{session.app_name}</code>"
        text += f"\n"
    text += "\n"
    text += "\n".join(f"{platform}：{count} 台" for platform, count in platform_count.items())
    return text


@listener(command="session",
          need_admin=True,
          parameters="注销/查询",
          description="注销/查询已登录的会话")
async def session_manage(message: Message):
    if not message.arguments:
        return await message.edit(await count_platform(private=message.chat.type in [ChatType.PRIVATE, ChatType.BOT]))
    if len(message.parameter) != 2:
        return await message.edit_text("请输入 `注销/查询 标识符` 来查询或注销会话")
    if message.parameter[0] == "查询":
        session = await filter_session(message.parameter[1])
        if session:
            return await message.edit(format_session(
                session,
                private=message.chat.type in [ChatType.PRIVATE, ChatType.BOT]))
        return await message.edit_text("请输入正确的标识符！")
    if message.parameter[0] == "注销":
        session = await filter_session(message.parameter[1])
        if session:
            success = await kick_session(session)
            return await message.edit("注销成功！" if success else "注销失败！")
        return await message.edit_text("请输入正确的标识符！")
    return await message.edit_text("请输入 `注销/查询 标识符` 来查询或注销会话")
