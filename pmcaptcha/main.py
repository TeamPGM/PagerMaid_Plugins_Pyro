# pmcaptcha - a pagermaid-pyro plugin by cloudreflection
# Rewritten by Sam
# https://t.me/cloudreflection_channel/268
# ver 2022/06/27

import re
import inspect
import html
import contextlib
from dataclasses import dataclass
from typing import Optional, Callable, Union

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


def bold(text: str) -> str:
    return f"<b>{text}</b>"


lang_dict = {
    # region General
    "no_cmd_given": [
        "Please use this command in private chat, or add parameters to execute.",
        "请在私聊时使用此命令，或添加参数执行。"
    ],
    "invalid_user_id": [
        "Invalid User ID",
        "未知用户或无效的用户 ID"
    ],
    "invalid_param": [
        "Invalid Parameter",
        "无效的参数"
    ],
    "enabled": [
        "Enabled",
        "开启"
    ],
    "disabled": [
        "Disabled",
        "关闭"
    ],
    "none": [
        "None",
        "无"
    ],
    "verb_msg": [
        "Message",
        "消息"
    ],
    "verb_array": [
        "List",
        "列表"
    ],
    "verb_bool": [
        "Boolean",
        "y / n"
    ],
    "action_param_name": [
        "Action",
        "操作"
    ],
    "tip_edit": [
        f"You can edit this by using {code('%s')}",
        f"如需编辑，请使用 {code('%s')}"
    ],
    "tip_run_in_pm": [
        "You can only run this command in private chat, or by adding parameters.",
        "请在私聊使用此命令，或添加参数执行。"
    ],
    # endregion

    # region Help
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
    # endregion

    # region Check
    "user_verified": [
        f"User {code('%i')} {italic('verified')}",
        f"用户 {code('%i')} {italic('已验证')}"
    ],
    "user_unverified": [
        f"User {code('%i')} {bold('unverified')}",
        f"用户 {code('%i')} {bold('未验证')}"
    ],
    # endregion

    # region Add
    "add_whitelist_success": [
        f"User {code('%i')} added to whitelist",
        f"用户 {code('%i')} 已添加到白名单"
    ],
    "remove_verify_log_success": [
        f"Removed User {code('%i')}'s verify record",
        f"已删除用户 {code('%i')} 的验证记录"
    ],
    "verify_log_not_found": [
        f"Verify record not found for User {code('%i')}",
        f"未找到用户 {code('%i')} 的验证记录"
    ],
    # endregion

    # region Welcome
    "welcome_curr_rule": [
        "Current welcome rule",
        "当前验证通过时消息规则"
    ],
    "welcome_set": [
        "Welcome message set.",
        "已设置验证通过消息"
    ],
    "welcome_reset": [
        "Welcome message reset.",
        "已重置验证通过消息"
    ],
    # endregion

    # region Whitelist
    "whitelist_curr_rule": [
        "Current whitelist rule",
        "当前白名单规则"
    ],
    "whitelist_set": [
        "Keywords whitelist set.",
        "已设置关键词白名单"
    ],
    "whitelist_reset": [
        "Keywords whitelist reset.",
        "已重置关键词白名单"
    ],
    # endregion

    # region Blacklist
    "blacklist_curr_rule": [
        "Current blacklist rule",
        "当前黑名单规则"
    ],
    "blacklist_set": [
        "Keywords blacklist set.",
        "已设置关键词黑名单"
    ],
    "blacklist_reset": [
        "Keywords blacklist reset.",
        "已重置关键词黑名单"
    ],
    # endregion

    # region Timeout
    "timeout_curr_rule": [
        "Current timeout: %i second(s)",
        "当前超时时间: %i 秒"
    ],
    "timeout_set": [
        "Verification timeout has been set to %i seconds.",
        "已设置验证超时时间为 %i 秒"
    ],
    "timeout_off": [
        "Verification timeout disabled.",
        "已关闭验证超时时间"
    ],
    # endregion

    # region Disable PM
    "disable_pm_curr_rule": [
        "Current disable PM status: %s",
        "当前禁止私聊状态: 已%s"
    ],
    "disable_pm_tip_exception": [
        "This feature will automatically allow contents and whitelist users.",
        "此功能会自动放行联系人与白名单用户"
    ],
    "disable_pm_set": [
        f"Private chat has bee set to {bold('%s')}.",
        f"已设置私聊为{bold('%s')}"
    ],
    # endregion

    # region Stats
    "stats_display": [
        "PMCaptcha has verified %i users in total.\n%i users has passed, %i users has been blocked.",
        "自上次重置起，已进行验证 %i 次\n其中验证通过 %i 次，拦截 %i 次"
    ],
    "stats_reset": [
        "Statistics has been reset.",
        "已重置统计"
    ],
    # endregion

    # region Action
    "action_curr_rule": [
        "Current action rule",
    ],
    "action_set": [
        f"Action has been set to {bold('%s')}.",
        f"验证失败后将执行{bold('%s')}操作"
    ],
    "action_set_none": [
        "Action has been set to none.",
        "验证失败后将不执行任何操作"
    ],
    "action_ban": [
        "Ban",
        "封禁"
    ],
    "action_delete": [
        "Ban and delete",
        "封禁并删除对话"
    ],
    "action_archive": [
        "Ban and archive",
        "封禁并归档"
    ],
    # endregion

    # region Premium Set
    "premium_curr_rule": [
        "Current premium user rule",
        "当前 Premium 用户规则"
    ],
    "premium_set_allow": [
        f"Telegram Premium users will be allowed to {bold('bypass')} the captcha.",
        f"将{bold('不对')} Telegram Premium 用户{bold('发起验证')}"
    ],
    "premium_set_ban": [
        f"Telegram Premium users will be {bold('banned')} from private chat.",
        f"将{bold('禁止')} Telegram Premium 用户私聊"
    ],
    "premium_set_only": [
        f"{bold('Only allowed')} Telegram Premium users to private chat.",
        f"将{bold('仅允许')} Telegram Premium 用户私聊"
    ],
    "premium_set_none": [
        "Nothing will do to Telegram Premium",
        "将不对 Telegram Premium 用户执行额外操作"
    ],
    # endregion

    # region Collect Logs
    "collect_logs_curr_rule": [
        "Current collect logs status: %s",
        "当前收集日志状态: 已%s"
    ],
    "collect_logs_note": [
        ("此功能仅会通过 @CloudreflectionPmcaptchabot 收集未通过验证者的首条消息、用户ID以及用户名；"
         "且不会提供给第三方(@LivegramBot 除外)。\n收集的信息将用于 PMCaptcha 改进，开启或关闭此功能不影响 PMCaptcha 的使用。"),
        ("This feature will only collect the first message, user ID, and username of non-verifiers "
         "via @CloudreflectionPmcaptchabot , and is not provided to third parties (except @LivegramBot ).\n"
         "Information collected will be used for PMCaptcha improvements, "
         "toggling this feature does not affect the use of PMCaptcha.")
    ],
    "collect_logs_set": [
        "Collect logs has been set to %s.",
        "已设置收集日志为 %s"
    ],
    # endregion

    # Functional

    # region Verify
    "verify_verified": [
        "Verified user",
        "已验证用户"
    ],
    "verify_unverified": [
        "Unverified user",
        "未验证用户"
    ],
    # endregion
}


# noinspection DuplicatedCode
@dataclass
class SubCommand:
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
                    f"{is_optional}{code(result[2].lstrip('_'))} - {result[3]}",
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
                             re.sub(r" {4,}", "", text).replace("{cmd_name}", cmd_name).strip()
                         ] + extras)

    def _get_cmd_with_param(self, subcmd_name: str) -> str:
        msg = subcmd_name
        if result := re.search(self.param_rgx, getattr(self, msg).__doc__):
            param = result[2].lstrip("_")
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
        await self.msg.edit(lang(f'verify_{"" if captcha_success.check_id(self.msg.chat.id) else "un"}verified'))
        await asyncio.sleep(5)
        await self.msg.safe_delete()

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

        if self.msg.chat.type != ChatType.PRIVATE:
            await self.msg.edit_text(lang('tip_run_in_pm'), parse_mode=ParseMode.HTML)
            await asyncio.sleep(5)
            return await self.msg.safe_delete()
        await self.msg.edit_text("\n".join(help_msg + footer), parse_mode=ParseMode.HTML)

    async def check(self, _id: int):
        """查询指定用户验证状态

        :param _id: 用户 ID
        """
        try:
            _id = _id or self.msg.from_user.id
            verified = captcha_success.check_id(int(_id))
            await self.msg.edit(lang(f"user_{'' if verified else 'un'}verified") % _id, parse_mode=ParseMode.HTML)
        except ValueError:
            await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)

    async def add(self, _id: Optional[int] = None):
        """将 ID 加入已验证，如未指定为当前私聊用户 ID

        :param opt _id: 用户 ID
        """
        try:
            if not _id and self.msg.chat.type != ChatType.PRIVATE:
                return await self.msg.edit(lang('tip_run_in_pm'), parse_mode=ParseMode.HTML)
            _id = _id or self.msg.chat.id
            captcha_success.add_id(int(_id))
            await bot.unarchive_chats(chat_ids=int(_id))
            await self.msg.edit(lang('add_whitelist_success') % _id, parse_mode=ParseMode.HTML)
        except ValueError:
            await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)

    async def delete(self, _id: Optional[int] = None):
        """移除 ID 验证记录，如未指定为当前私聊用户 ID

        :param opt _id: 用户 ID
        :alias: del
        """
        try:
            if not _id and self.msg.chat.type != ChatType.PRIVATE:
                return await self.msg.edit(lang('tip_run_in_pm'), parse_mode=ParseMode.HTML)
            _id = _id or self.msg.from_user.id
            text = lang('remove_verify_log_success' if captcha_success.del_id(int(_id)) else 'verify_log_not_found')
            await self.msg.edit(text % _id, parse_mode=ParseMode.HTML)
        except ValueError:
            await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)

    async def welcome(self, *message: str):
        """查看或设置验证通过时发送的消息
        使用 <code>,{cmd_name} welcome -clear</code> 可恢复默认规则

        :param message: 消息内容
        :alias: wel
        """
        data = sqlite.get("pmcaptcha", {})
        if not message:
            return await self.msg.edit_text("\n".join((
                lang('welcome_curr_rule') + ":",
                code(data.get('welcome', lang('none'))),
                "",
                lang('tip_edit') % f",{cmd_name} wel <{lang('verb_msg')}>"
            )), parse_mode=ParseMode.HTML)
        message = " ".join(message)
        if message == "-clear":
            if data.get("welcome", False):
                del data["welcome"]
                sqlite["pmcaptcha"] = data
            await self.msg.edit(lang('welcome_reset'), parse_mode=ParseMode.HTML)
            return
        data["welcome"] = message
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('welcome_set'), parse_mode=ParseMode.HTML)

    async def whitelist(self, array: str):
        """查看或设置关键词白名单列表（英文逗号分隔）
        使用 <code>,{cmd_name} whitelist -clear</code> 可清空列表

        :param array: 白名单列表 (英文逗号分隔)
        :alias: wl, whl
        """
        data = sqlite.get("pmcaptcha", {})
        if not array:
            return await self.msg.edit_text("\n".join((
                lang('whitelist_curr_rule') + ":",
                code(data.get('whitelist', lang('none'))),
                "",
                lang('tip_edit') % f",{cmd_name} wl <{lang('verb_array')}>"
            )), parse_mode=ParseMode.HTML)
        if array == "-clear":
            if data.get("whitelist", False):
                del data["whitelist"]
                sqlite["pmcaptcha"] = data
            await self.msg.edit(lang('whitelist_reset'), parse_mode=ParseMode.HTML)
            return
        data["whitelist"] = array.replace(" ", "").split(",")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('whitelist_set'), parse_mode=ParseMode.HTML)

    async def blacklist(self, array: str):
        """查看或设置关键词黑名单列表 (英文逗号分隔)
        使用 <code>,{cmd_name} blacklist -clear</code> 可清空列表

        :param array: 黑名单列表 (英文逗号分隔)
        :alias: bl
        """
        data = sqlite.get("pmcaptcha", {})
        if not array:
            return await self.msg.edit_text("\n".join((
                lang('blacklist_curr_rule') + ":",
                code(data.get('blacklist', lang('none'))),
                "",
                lang('tip_edit') % f",{cmd_name} bl <{lang('verb_array')}>"
            )), parse_mode=ParseMode.HTML)
        if array == "-clear":
            if data.get("blacklist", False):
                del data["blacklist"]
                sqlite["pmcaptcha"] = data
            await self.msg.edit(lang('blacklist_reset'), parse_mode=ParseMode.HTML)
            return
        data["blacklist"] = array.replace(" ", "").split(",")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('blacklist_set'), parse_mode=ParseMode.HTML)

    async def timeout(self, seconds: Union[str, int]):
        """查看或设置超时时间，默认为 30 秒 (<b>不适用于图形验证</b>)
        使用 <code>,{cmd_name} wait off</code> 可关闭验证时间限制

        :param seconds: 超时时间，单位秒
        :alias: wait
        """
        data = sqlite.get("pmcaptcha", {})
        if not seconds:
            return await self.msg.edit_text("\n".join((
                lang('timeout_curr_rule') % int(data.get('timeout', 30)),
                "",
                lang('tip_edit') % f",{cmd_name} wait <{lang('verb_int')}>"
            )), parse_mode=ParseMode.HTML)
        if seconds == "off":
            if data.get("timeout", False):
                del data["timeout"]
                sqlite["pmcaptcha"] = data
            await self.msg.edit(lang('timeout_off'), parse_mode=ParseMode.HTML)
            return
        data["timeout"] = int(seconds)
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('timeout_set') % seconds, parse_mode=ParseMode.HTML)

    async def disable_pm(self, toggle: str):
        """启用 / 禁止陌生人私聊
        此功能会放行联系人和白名单(<i>已通过验证</i>)用户
        您可以使用 <code>,{cmd_name} add</code> 将用户加入白名单

        :param toggle: 开关 (y / n)
        :alias: disablepm
        """
        data = sqlite.get("pmcaptcha", {})
        if not toggle:
            return await self.msg.edit_text("\n".join((
                lang('disable_pm_curr_rule') % (data.get('disablepm', lang('off'))),
                "",
                lang('tip_edit') % f",{cmd_name} disablepm <{lang('verb_bool')}>"
            )), parse_mode=ParseMode.HTML)
        toggle = toggle.lower()[0]
        if toggle not in ("y", "n", "t", "f", "1", "0"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        data["disable_pm"] = toggle in ("y", "t", "1")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('disable_pm_set') % lang("enabled" if data["disable_pm"] else "disabled"),
                            parse_mode=ParseMode.HTML)

    async def stats(self, arg: str):
        """查看验证统计
        可以使用 <code>,{cmd_name} stats -clear</code> 重置
        """
        data = sqlite.get("pmcaptcha", {})
        if not arg:
            data = (data.get('pass', 0) + data.get('banned', 0), data.get('pass', 0), data.get('banned', 0))
            return await self.msg.edit_text(code("PMCaptcha ") + lang('stats_display') % data,
                                            parse_mode=ParseMode.HTML)
        if arg == "-clear":
            data["pass"] = 0
            data["banned"] = 0
            sqlite["pmcaptcha"] = data
            await self.msg.edit(lang('stats_reset'), parse_mode=ParseMode.HTML)
            return

    async def action(self, action: str):
        """选择验证失败的处理方式，默认为 <code>archive</code>
        图形模式默认为 <code>none</code>

        :param action: 处理方式 (<code>ban</code> / <code>delete</code> / <code>archive</code> / <code>none</code>)
        :alias: act
        """
        data = sqlite.get("pmcaptcha", {})
        if not action:
            action = data.get("action", "none")
            return await self.msg.edit_text("\n".join((
                lang('action_curr_rule') + ":",
                lang('action_set_none') if action == "none" else lang('action_set') % lang(f'action_{action}'),
                "",
                lang('tip_edit') % f",{cmd_name} act <{lang('action_param_name')}>"
            )), parse_mode=ParseMode.HTML)
        if action not in ("ban", "delete", "archive", "none"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        if action in ("ban", "delete", "archive"):
            await self.msg.edit(lang('action_set') % lang(f'action_{action}'), parse_mode=ParseMode.HTML)
        elif action == "none":
            await self.msg.edit(lang('action_set_none'), parse_mode=ParseMode.HTML)
        data["action"] = action
        sqlite["pmcaptcha"] = data

    async def premium(self, action: str):
        """选择对 <b>Premium</b> 用户的操作，默认为 <code>archive</code>
        图形模式默认为 <code>none</code>

        :param action: 操作方式 (<code>allow</code> / <code>ban</code> / <code>only</code> / <code>none</code>)
        :alias: vip, prem
        """
        data = sqlite.get("pmcaptcha", {})
        if not action:
            return await self.msg.edit_text("\n".join((
                lang('premium_curr_rule') + ":",
                lang(f'premium_set_{data.get("premium", "none")}'),
                "",
                lang('tip_edit') % f",{cmd_name} prem <{lang('action_param_name')}>"
            )), parse_mode=ParseMode.HTML)
        if action not in ("allow", "ban", "only", "none"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        if action == "none":
            del data["premium"]
        else:
            data["premium"] = action
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang(f'premium_set_{action}'), parse_mode=ParseMode.HTML)

    async def collect_logs(self, toggle: str):
        """查看或设置是否允许 <code>PMCaptcha</code> 收集验证错误相关信息以帮助改进
        默认为 N ,收集的信息包括验证的首条消息，被验证者的 ID 和用户名

        :param toggle: 开关 (y / n)
        :alias: collect, log
        """
        data = sqlite.get("pmcaptcha", {})
        if not toggle:
            status = lang('enabled' if data.get('collect', False) else 'disabled')
            return await self.msg.edit_text("\n".join((
                lang('collect_curr_rule') % status,
                lang("collect_logs_note"),
                "",
                lang('tip_edit') % f",{cmd_name} collect <{lang('verb_bool')}>"
            )), parse_mode=ParseMode.HTML)
        toggle = toggle.lower()[0]
        if toggle not in ("y", "n", "t", "f", "1", "0"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        data["collect"] = toggle in ("y", "t", "1")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('collect_logs_set') % lang("enabled" if data["collect"] else "disabled"))


@listener(is_plugin=True, outgoing=True,
          command=cmd_name,
          need_admin=True,
          description=f"私聊人机验证插件\n请使用 {code(',pmcaptcha h')} 查看可用命令")
async def cmd_entry(_, msg: Message):
    cmd = len(msg.parameter) > 0 and msg.parameter[0] or cmd_name
    func = SubCommand(msg)[cmd]
    args_len = -1 if inspect.getfullargspec(func).varargs else len(inspect.getfullargspec(func).args)
    await (func(*(len(msg.parameter) > 1 and msg.parameter[1:args_len] or [None] * (args_len - 1))) if func else
           msg.edit_text(f"{lang('cmd_not_found')}: {code(cmd)}", parse_mode=ParseMode.HTML))  # Command Not Found
