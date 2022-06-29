# pmcaptcha - a pagermaid-pyro plugin by cloudreflection
# Rewritten by Sam
# https://t.me/cloudreflection_channel/268
# ver 2022/06/27

import re
import inspect
import html
import contextlib
from dataclasses import dataclass
from typing import Optional, Callable

from pyrogram import Client
from pyrogram.enums.chat_type import ChatType
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.raw.functions.account import UpdateNotifySettings
from pyrogram.raw.functions.messages import DeleteHistory
from pyrogram.raw.types import InputNotifyPeer, InputPeerNotifySettings

from pagermaid import log, bot
from pagermaid.utils import Message
from pagermaid.listener import listener
from pagermaid.config import Config
from pagermaid.single_utils import sqlite
from pagermaid.sub_utils import Sub

import asyncio
import random

cmd_name = "pmcaptcha"
version = "2.0"

captcha_success = Sub("pmcaptcha.success")


def lang(lang_id: str) -> str:
    return lang_dict.get(lang_id)[1 if Config.LANGUAGE.startswith("zh") else 0]


def code(text: str) -> str:
    return f"<code>{text}</code>"


def italic(text: str) -> str:
    return f"<i>{text}</i>"


lang_dict = {
    "cmd_param": [
        "Parameter",
        "参数"
    ],
    "cmd_param_optional": [
        "Optional",
        "可选"
    ],
    "cmd_alias": [
        "Alias",
        "别名/快捷命令"
    ],
    "cmd_detail": [
        f"Do {code(f',{cmd_name} h [command]')} for details",
        f"详细指令请输入 {code(f',{cmd_name} h [指令名称]')}",
    ],
    "cmd_not_found": [
        "Command Not Found",
        "指令不存在"
    ],
    "cmd_list": [
        "Command List",
        "指令列表"
    ],
    "priority": [
        "Priority",
        "优先级"
    ],
    "no_cmd_given": [
        "Please use this command in private chat, or add parameters to execute.",
        "请在私聊时使用此命令，或添加参数执行。"
    ],
}


@dataclass
class SubCommand:
    c: Client
    msg: Message

    # Regex
    alias_rgx = r":alias: (.+)"
    param_rgx = r":param (opt)?\s?(\w+):\s?(.+)"

    def _extract_docs(self, subcmd_name: str, text: str) -> str:
        extras = []
        if result := re.search(self.param_rgx, text):
            is_optional = f"({italic(lang('cmd_param_optional'))}) " if result[1] else ""
            extras.extend(
                (
                    f"{lang('cmd_param')}:",
                    f"{is_optional}{code(result[2])} - {result[3]}",
                )
            )

            text = re.sub(self.param_rgx, "", text)
        if result := re.search(self.alias_rgx, text):
            alias = result[1].replace(" ", "").split(",")
            alia_text = ", ".join(code(a) for a in alias)
            extras.append(f"{lang('cmd_alias')}: {code(alia_text)}")
            text = re.sub(self.alias_rgx, "", text)
        len(extras) and extras.insert(0, "")
        if cmd_name == subcmd_name:
            subcmd_name = ""
        return "\n".join([
                             code(f",{cmd_name} {subcmd_name}".strip()),
                             re.sub(r" {4,}", "", text).strip()
                         ] + extras)

    def _get_cmd_with_param(self, subcmd_name: str) -> str:
        msg = subcmd_name
        if result := re.search(self.param_rgx, getattr(self, msg).__doc__):
            param = result[2]
            msg += f" [{param}]" if result[1] else html.escape(f" <{param}>")
        return msg

    def _get_mapped_alias(self, alias_name: str, ret_type: str):
        # Get alias function
        for name, func in inspect.getmembers(self, inspect.iscoroutinefunction):
            if name.startswith("_"):
                continue
            if result := re.search(self.alias_rgx, func.__doc__):
                if alias_name in result[1].replace(" ", "").split(","):
                    return func if ret_type == "func" else name

    def __getitem__(self, cmd: str) -> Optional[Callable]:
        # Get subcommand function
        if func := getattr(self, cmd, None):
            return func
        # Check for alias
        if func := self._get_mapped_alias(cmd, "func"):
            return func
        return  # Not found

    async def pmcaptcha(self):
        """查询当前私聊用户验证状态"""

    async def help(self, command: Optional[str] = None):
        """显示帮助信息

        :param opt command: 命令名称
        :alias: h
        """
        help_msg = [f"{lang('cmd_list')}:"]
        footer = [
            italic(lang('cmd_detail')),
            "",
            f"{lang('priority')}: disable_pm > premium > whitelist > blacklist",
            f"遇到任何问题请先 {code(',apt update')} 更新后复现再反馈",
            "捐赠: cloudreflection.eu.org/donate"
        ]
        if command:  # Single command help
            func = getattr(self, command, self._get_mapped_alias(command, "func"))
            return await (
                self.msg.edit_text(self._extract_docs(command, func.__doc__), parse_mode=ParseMode.HTML) if func else
                self.msg.edit_text(f"{lang('cmd_not_found')}: {code(command)}", parse_mode=ParseMode.HTML))
        for name, func in inspect.getmembers(self, inspect.iscoroutinefunction):
            if name.startswith("_"):
                continue
            help_msg.append(
                (
                    code(f",{cmd_name} {self._get_cmd_with_param(name)}")
                    + f"\n- {re.search(r'(.+)', func.__doc__)[1].strip()}\n"
                )
            )

        await self.msg.edit_text("\n".join(help_msg + footer), parse_mode=ParseMode.HTML)

    # noinspection PyShadowingBuiltins
    async def check(self, id: int):
        """查询指定用户验证状态

        :param id: 用户 ID
        """

    # noinspection PyShadowingBuiltins
    async def add(self, id: Optional[int] = None):
        """将 ID 加入已验证，如未指定为当前私聊用户 ID

        :param opt id: 用户 ID
        """

    # noinspection PyShadowingBuiltins
    async def delete(self, id: Optional[int] = None):
        """移除 ID 验证记录，如未指定为当前私聊用户 ID

        :param opt id: 用户 ID
        :alias: del
        """

    async def welcome(self, message: str):
        """查看或设置验证通过时发送的消息
        使用 ```,{cmd_name} welcome -clear``` 可恢复默认规则

        :param message: 消息内容
        :alias: wel
        """

    async def whitelist(self, array: str):
        """查看或设置关键词白名单列表（英文逗号分隔）
        使用 ```,{cmd_name} whitelist -clear``` 可清空列表

        :param array: 白名单列表 (英文逗号分隔)
        :alias: wl, whl
        """

    async def blacklist(self, array: str):
        """查看或设置关键词黑名单列表 (英文逗号分隔)
        使用 ```,{cmd_name} blacklist -clear``` 可清空列表

        :param array: 黑名单列表 (英文逗号分隔)
        :alias: bl
        """

    async def timeout(self, seconds: int):
        """查看或设置超时时间，默认为 30 秒
        使用 ```,{cmd_name} timeout off``` 可关闭验证时间限制

        :param seconds: 超时时间，单位秒
        :alias: wait
        """

    async def disable_pm(self, toggle: bool):
        """启用/禁止陌生人私聊
        此功能会放行联系人和白名单(已通过验证)用户
        您可以使用 ```,{cmd_name} add``` 将用户加入白名单

        :param toggle: 开关 (y / n)
        :alias: disablepm
        """

    async def stats(self):
        """查看验证统计
        可以使用 ```,{cmd_name} stats -clear``` 重置
        """

    async def action(self, action: str):
        """选择验证失败的处理方式，默认为 archive
        图形模式默认为 none

        :param action: 处理方式 (ban / delete / archive / none)
        :alias: act
        """

    async def premium(self, action: str):
        """选择对 Rremium 用户的操作，默认为 none
        图形模式默认为 none

        :param action: 操作方式 (allow / ban / only / none)
        :alias: vip, prem
        """

    async def collect_logs(self, toggle: bool):
        """查看或设置是否允许 PMCaptcha 收集验证错误相关信息以帮助改进
        默认为 N ,收集的信息包括验证的首条消息，被验证者的 ID 和用户名

        :param toggle: 开关 (y / n)
        :alias: collect, log
        """


@listener(is_plugin=True, outgoing=True,
          command=cmd_name,
          need_admin=True,
          description=f"私聊人机验证插件\n请使用 {code(',pmcaptcha h')} 查看可用命令")
async def cmd_entry(c: Client, msg: Message):
    cmd = len(msg.parameter) > 0 and msg.parameter[0] or cmd_name
    func = SubCommand(c, msg)[cmd]
    args_len = len(inspect.getfullargspec(func).args)
    await (func(*(len(msg.parameter) > 1 and msg.parameter[1:args_len] or [None] * args_len)) if func else
           msg.edit_text(f"{lang('cmd_not_found')}: {code(cmd)}", parse_mode=ParseMode.HTML))  # Command Not Found
