# -*- coding: utf-8 -*-
"""PMCaptcha v2 - A PagerMaid-Pyro plugin
v1 by xtaodata and cloudreflection
v2 by Sam
"""

import re
import time
import html
import asyncio
import inspect
import traceback
from dataclasses import dataclass, field
from typing import Optional, Callable, Union, List, Any

from pyrogram.errors import FloodWait, AutoarchiveNotAvailable, ChannelsAdminPublicTooMuch
from pyrogram.raw.functions.channels import UpdateUsername
from pyrogram.raw.types import GlobalPrivacySettings
from pyrogram.raw.functions.account import SetGlobalPrivacySettings, GetGlobalPrivacySettings
from pyrogram.enums.chat_type import ChatType
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.raw.functions import messages
from pyrogram.raw.types.messages import PeerSettings
from pyrogram.types import User

from pagermaid import bot, logs
from pagermaid.config import Config
from pagermaid.sub_utils import Sub
from pagermaid.utils import Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite

cmd_name = "pmcaptcha"
version = "2.1"

log_collect_bot = "CloudreflectionPmcaptchabot"
img_captcha_bot = "PagerMaid_Sam_Bot"


def sort_line_number(m):
    try:
        func = getattr(m[1], "__func__", m[1])
        return func.__code__.co_firstlineno
    except AttributeError:
        return -1


async def log(message: str, remove_prefix: bool = False):
    console.info(message.replace('`', '\"'))
    Config.LOG and logging.send_log(message, remove_prefix)


def lang(lang_id: str, lang_code: str = Config.LANGUAGE or "en") -> str:
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
        "tip_edit": [
            f"You can edit this by using {code('%s')}",
            f"如需编辑，请使用 {code('%s')}"
        ],
        "tip_run_in_pm": [
            "You can only run this command in private chat, or by adding parameters.",
            "请在私聊使用此命令，或添加参数执行。"
        ],
        # endregion

        # region Plugin
        "plugin_desc": [
            "Captcha for PM",
            "私聊人机验证插件"
        ],
        "check_usage": [
            "Please use %s to see available commands.",
            "请使用 %s 查看可用命令"
        ],
        "curr_version": [
            f"Current {code('PMCaptcha')} Version: %s",
            f"{code('PMCaptcha')} 当前版本：%s"
        ],
        "unknown_version": [
            italic("Unknown"),
            italic("未知")
        ],
        # endregion

        # region Vocabs
        "vocab_msg": [
            "Message",
            "消息"
        ],
        "vocab_array": [
            "List",
            "列表"
        ],
        "vocab_bool": [
            "Boolean",
            "y / n"
        ],
        "vocab_int": [
            "Integer",
            "整数"
        ],
        "vocab_cmd": [
            "Command",
            "指令"
        ],
        # endregion

        # region Verify
        "verify_verified": [
            "Verified user",
            "已验证用户"
        ],
        "verify_unverified": [
            "Unverified user",
            "未验证用户"
        ],
        "verify_blocked": [
            "You were blocked.",
            "您已被封禁"
        ],
        "verify_log_punished": [
            "User %s has been %s.",
            "已对用户 %s 执行`%s`操作"
        ],
        "verify_challenge": [
            "Please answer this question to prove you are human (1 chance)",
            "请回答这个问题证明您不是机器人 (一次机会)"
        ],
        "verify_challenge_timed": [
            "You have %i seconds.",
            "您有 %i 秒来回答这个问题"
        ],
        "verify_passed": [
            "Verification passed.",
            "验证通过"
        ],
        "verify_failed": [
            "Verification failed.",
            "验证失败"
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
            f"Do {code(f',{cmd_name} h ')}[command ] for details",
            f"详细指令请输入 {code(f',{cmd_name} h ')}[指令名称 ]",
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
        "cmd_search_result": [
            f"Search Result for `%s`",
            f"`%s` 的搜索结果"
        ],
        "cmd_search_docs": [
            "Documentation",
            "文档"
        ],
        "cmd_search_cmds": [
            "Commands",
            "指令"
        ],
        "cmd_search_none": [
            "No result found.",
            "未找到结果"
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

        # region Add / Delete
        "add_whitelist_success": [
            f"User {code('%i')} added to whitelist",
            f"用户 {code('%i')} 已添加到白名单"
        ],
        "remove_verify_log_success": [
            f"Removed User {code('%i')}'s verify record",
            f"已删除用户 {code('%i')} 的验证记录"
        ],
        "remove_verify_log_failed": [
            f"Failed to remove User {code('%i')}'s verify record.",
            f"删除用户 {code('%i')} 的验证记录失败"
        ],
        "remove_verify_log_not_found": [
            f"Verify record not found for User {code('%i')}",
            f"未找到用户 {code('%i')} 的验证记录"
        ],
        # endregion

        # region Unstuck
        "unstuck_success": [
            f"User {code('%i')} has removed from challenge mode",
            f"用户 {code('%i')} 已解除验证状态"
        ],
        "not_stuck": [
            f"User {code('%i')} is not stuck",
            f"用户 {code('%i')} 未在验证状态"
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
        "blacklist_triggered": [
            "Blacklist rule triggered",
            "您触发了黑名单规则"
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
        "timeout_exceeded": [
            "Verification timeout.",
            "验证超时"
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
        "disable_set": [
            f"Disable private chat has been set to {bold('%s')}.",
            f"已设置禁止私聊为{bold('%s')}"
        ],
        "disable_pm_enabled": [
            "Owner has private chat disabled.",
            "对方已禁止私聊。"
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
        "action_param_name": [
            "Action",
            "操作"
        ],
        "action_curr_rule": [
            "Current action rule",
            "当前验证失败规则"
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

        # region Report
        "report_curr_rule": [
            "Current report state: %s",
            "当前举报状态为: %s"
        ],
        "report_set": [
            f"Report has been set to {bold('%s')}.",
            f"已设置举报状态为{bold('%s')}"
        ],
        # endregion

        # region Premium
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
        "premium_only": [
            "Owner only allows Telegram Premium users to private chat.",
            "对方只允许 Telegram Premium 用户私聊"
        ],
        "premium_ban": [
            "Owner bans Telegram Premium users from private chat.",
            "对方禁止 Telegram Premium 用户私聊"
        ],
        # endregion

        # region Groups In Common
        "groups_in_common_set": [
            f"Groups in common larger than {bold('%i')} will be whitelisted.",
            f"共同群数量大于 {bold('%i')} 时将自动添加到白名单"
        ],
        "groups_in_common_disabled": [
            "Group in command is not enabled",
            "未开启共同群数量检测"
        ],
        "groups_in_common_disable": [
            "Groups in common disabled.",
            "已关闭共同群检查"
        ],
        # endregion

        # region Chat History
        "chat_history_curr_rule": [
            f"Chat history equal or larger than {bold('%i')} will be whitelisted.",
            f"聊天记录数量大于 {bold('%i')} 时将自动添加到白名单"
        ],
        "chat_history_disabled": [
            "Chat history check is not enabled",
            "未开启聊天记录数量检测"
        ],
        # endregion

        # region Initiative
        "initiative_curr_rule": [
            "Current initiative status: %s",
            "当前对主动进行对话的用户添加白名单状态为： %s"
        ],
        "initiative_set": [
            f"Initiative has been set to {bold('%s')}.",
            f"已设置对主动进行对话的用户添加白名单状态为{bold('%s')}"
        ],
        # endregion

        # region Silent
        "silent_curr_rule": [
            "Current silent status: %s",
            "当前静音状态: 已%s"
        ],
        "silent_set": [
            f"Silent has been set to {bold('%s')}.",
            f"已设置静音模式为{bold('%s')}"
        ],
        # endregion

        # region Flood
        "flood_curr_rule": [
            "Current flood detect limit was set to %i user(s)",
            "当前轰炸人数已设置为 %i 人"
        ],
        # Username
        "flood_username_curr_rule": [
            "Current flood username option was set to %s",
            "当前轰炸时切换用户名选项已设置为 %s"
        ],
        "flood_username_set_confirm": [
            (f"The feature may lose your username, are you sure you want to enable this feature?\n"
             f"Please enter {code(f',{cmd_name} flood_username y')} again to confirm."),
            f"此功能有可能回导致您的用户名丢失，您是否确定要开启此功能？\n请再次输入 {code(f',{cmd_name} flood_username y')} 来确认"
        ],
        "flood_username_set": [
            f"Change username in flood preiod has been %s.",
            f"轰炸时切换用户名已%s"
        ],
        "flood_channel_desc": [
            ("This channel is a placeholder of username, which the owner is being flooded.\n"
             "Please content him later after this channel is gone."),
            "这是一个用于临时设置用户名的频道，该群主正在被私聊轰炸\n请在此频道消失后再联系他。"
        ],
        # Action
        "flood_act_curr_rule": [
            "Current flood action was set to %s",
            "当前轰炸操作已设置为 %s"
        ],
        "flood_act_set_asia": [
            f"All users in flood period will be {bold('treat as verify failed')}.",
            f"所有在轰炸期间的用户将会{bold('与验证失败的处理方式一致')}"
        ],
        "flood_act_set_captcha": [
            f"All users in flood period will be {bold('asked for captcha')}.",
            f"所有在轰炸期间的用户将会{bold('进行验证码挑战')}"
        ],
        "flood_act_set_none": [
            "Nothing will do to users in flood period.",
            "所有在轰炸期间的用户将不会被进行任何处理"
        ],
        # endregion

        # region Collect Logs
        "collect_logs_curr_rule": [
            "Current collect logs status: %s",
            "当前收集日志状态: 已%s"
        ],
        "collect_logs_note": [
            ("This feature will only collect user information and chat logs of non-verifiers "
             f"via @{log_collect_bot} , and is not provided to third parties (except @LivegramBot ).\n"
             "Information collected will be used for PMCaptcha improvements, "
             "toggling this feature does not affect the use of PMCaptcha."),
            (f"此功能仅会通过 @{log_collect_bot} 收集未通过验证者的用户信息以及验证未通过的聊天记录；"
             "且不会提供给第三方(@LivegramBot 除外)。\n收集的信息将用于 PMCaptcha 改进，开启或关闭此功能不影响 PMCaptcha 的使用。")
        ],
        "collect_logs_set": [
            "Collect logs has been set to %s.",
            "已设置收集日志为 %s"
        ],
        # endregion

        # region Captcha Type
        "type_curr_rule": [
            "Current captcha type: %s",
            "当前验证码类型: %s"
        ],
        "type_set": [
            f"Captcha type has been set to {bold('%s')}.",
            f"已设置验证码类型为 {bold('%s')}"
        ],
        "type_param_name": [
            "Type",
            "类型"
        ],
        "type_captcha_img": [
            "Image",
            "图像辨识"
        ],
        "type_captcha_math": [
            "Math",
            "计算"
        ],
        # endregion

        # region Image Captcha Type
        "img_captcha_type_func": [
            "funCaptcha",
            "funCaptcha",
        ],
        "img_captcha_type_github": [
            "GitHub",
            "GitHub",
        ],
        "img_captcha_type_rec": [
            "reCaptcha",
            "reCaptcha"
        ],
        "img_captcha_retry_curr_rule": [
            "Current max retry for image captcha: %s",
            "当前图像验证码最大重试次数: %s"
        ],
        "img_captcha_retry_set": [
            "Max retry for image captcha has been set to %s.",
            "已设置图像验证码最大重试次数为 %s"
        ],
        # endregion
    }

    lang_code = lang_code or "en"
    return lang_dict.get(lang_id)[1 if lang_code.startswith("zh") else 0]


def get_version():
    from pagermaid import working_dir
    from os import sep
    from json import load
    plugin_directory = f"{working_dir}{sep}plugins{sep}"
    with open(f"{plugin_directory}version.json", 'r', encoding="utf-8") as f:
        version_json = load(f)
    return version_json.get(cmd_name, lang('unknown_version'))


# region Text Formatting
def code(text: str) -> str:
    return f"<code>{text}</code>"


def italic(text: str) -> str:
    return f"<i>{text}</i>"


def bold(text: str) -> str:
    return f"<b>{text}</b>"


def gen_link(text: str, url: str) -> str:
    return f"<a href=\"{url}\">{text}</a>"


# endregion

@dataclass
class Log:
    task: Optional[asyncio.Task] = None
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    last_send_time: int = 0

    async def worker(self):
        while True:
            text = None
            try:
                if int(time.time()) - self.last_send_time < 5:
                    await asyncio.sleep(5 - (int(time.time()) - self.last_send_time))
                    continue
                (text,) = await self.queue.get()
                await bot.send_message(Config.LOG_ID, text, ParseMode.HTML)
                self.last_send_time = int(time.time())
            except asyncio.CancelledError:
                break
            except FloodWait as e:
                console.debug(f"Flood triggered when sending log, wait for {e.value}s")
                await asyncio.sleep(e.value)
            except Exception as e:
                console.error(f"Error when sending log: {e}\n{traceback.format_exc()}")
            finally:
                text and self.queue.task_done()

    def send_log(self, message: str, remove_prefix: bool):
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.worker())
        message = message if remove_prefix else " ".join(("[PMCaptcha]", message))
        self.queue.put_nowait((message,))


@dataclass
class Setting:
    key_name: str
    whitelist: Sub = field(init=False)
    pending_ban_list: Sub = field(init=False)
    pending_challenge_list: Sub = field(init=False)

    def __post_init__(self):
        self.whitelist = Sub("pmcaptcha.success")
        self.pending_ban_list = Sub("pmcaptcha.pending_ban")
        self.pending_challenge_list = Sub("pmcaptcha.pending_challenge")

    def get(self, key: str, default=None):
        if sqlite.get(self.key_name) is None:
            return default
        return sqlite[self.key_name].get(key, default)

    def set(self, key: str, value: Any):
        """Set the value of a key in the database, return value"""
        if (data := sqlite.get(self.key_name)) is None:
            sqlite[self.key_name] = data = {}
        data.update({key: value})
        sqlite[self.key_name] = data
        return value

    def delete(self, key: str):
        """Delete a key in the database, if key exists"""
        if self.get(key):
            del sqlite[self.key_name][key]
        return self

    def is_verified(self, user_id: int) -> bool:
        return self.whitelist.check_id(user_id)

    # region Captcha Challenge

    def get_challenge_state(self, user_id: int) -> dict:
        return sqlite.get(f"{self.key_name}.challenge.{user_id}", {})

    def set_challenge_state(self, user_id: int, state: dict):
        sqlite[f"{self.key_name}.challenge.{user_id}"] = state
        return state

    def del_challenge_state(self, user_id: int):
        key = f"{self.key_name}.challenge.{user_id}"
        if sqlite.get(key):
            del sqlite[key]

    # endregion

    # region Flood State

    def get_flood_state(self) -> dict:
        return sqlite.get(f"{self.key_name}.flood_state", {})

    def set_flood_state(self, state: dict) -> dict:
        sqlite[f"{self.key_name}.flood_state"] = state
        return state

    def del_flood_state(self):
        key = f"{self.key_name}.flood_state"
        if sqlite.get(key):
            del sqlite[key]

    # endregion


@dataclass
class Command:
    user: User
    msg: Message

    # Regex
    alias_rgx = r":alias: (.+)"
    param_rgx = r":param (opt)?\s?(\w+):\s?(.+)"

    async def _run_command(self):
        command = len(self.msg.parameter) > 0 and self.msg.parameter[0] or cmd_name
        if not (func := self[command]):
            return False, "NOT_FOUND", command
        full_arg_spec = inspect.getfullargspec(func)
        args_len = None if full_arg_spec.varargs else len(full_arg_spec.args)
        cmd_args = self.msg.parameter[1:args_len]
        func_args = []
        for index, arg_type in enumerate(tuple(full_arg_spec.annotations.values())):  # Check arg type
            try:
                if getattr(arg_type, "__origin__", None) == Union:
                    NoneType = type(None)
                    if (
                            len(arg_type.__args__) != 2
                            or arg_type.__args__[1] is not NoneType
                    ):
                        continue
                    if len(cmd_args) - 1 > index and not cmd_args[index] or len(cmd_args) - 1 < index:
                        func_args.append(None)
                        continue
                    arg_type = arg_type.__args__[0]
                func_args.append(arg_type(cmd_args[index]))
            except ValueError:
                return False, "INVALID_PARAM", tuple(full_arg_spec.annotations.keys())[index]
            except IndexError:  # No more args
                await self.help(command)
                return True, None, None
        await func(*func_args)
        return True, None, None

    def _extract_docs(self, subcmd_name: str, text: str) -> str:
        extras = []
        if result := re.search(self.param_rgx, text):
            is_optional = f"({italic(lang('cmd_param_optional'))} ) " if result[1] else ""
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
            extras.append(f"{lang('cmd_alias')}: {alia_text}")
            text = re.sub(self.alias_rgx, "", text)
        len(extras) and extras.insert(0, "")
        return "\n".join([
                             code(f",{cmd_name} {self._get_cmd_with_param(subcmd_name)}".strip()),
                             re.sub(r" {4,}", "", text).replace("{cmd_name}", cmd_name).strip()
                         ] + extras)

    def _get_cmd_with_param(self, subcmd_name: str) -> str:
        if subcmd_name == cmd_name:
            return ""
        msg = subcmd_name
        if result := re.search(self.param_rgx, getattr(self, msg).__doc__ or ''):
            param = result[2].lstrip("_")
            msg += f" [{param}]" if result[1] else html.escape(f" <{param}>")
        return msg

    def _get_mapped_alias(self, alias_name: str, ret_type: str):
        # Get alias function
        for name, func in inspect.getmembers(self, inspect.iscoroutinefunction):
            if name.startswith("_"):
                continue
            if ((result := re.search(self.alias_rgx, func.__doc__ or "")) and
                    alias_name in result[1].replace(" ", "").split(",")):
                return func if ret_type == "func" else name

    # region Helpers (Formatting, User ID)

    async def _display_value(self, *, key: Optional[str] = None, display_text: str, sub_cmd: str, value_type: str):
        text = [display_text, "", lang('tip_edit') % html.escape(f",{cmd_name} {sub_cmd} <{lang(value_type)}>")]
        key and text.insert(0, lang(f"{key}_curr_rule") + ":")
        return await self.msg.edit_text("\n".join(text), parse_mode=ParseMode.HTML)

    # Set On / Off Boolean
    async def _set_toggle(self, key: str, toggle: str):
        if ((toggle := toggle.lower()[0]) not in ("y", "n", "t", "f", "1", "0") and
                (toggle := toggle.lower()) not in ("on", "off")):
            return await self.help(key)
        toggle = toggle in ("y", "t", "1", "on")
        toggle and setting.set(key, True) or setting.delete(key)
        await self.msg.edit(lang(f"{key}_set") % lang("enabled" if toggle else "disabled"), parse_mode=ParseMode.HTML)

    async def _get_user_id(self, user_id: Union[str, int]) -> Optional[int]:
        if not user_id and not self.msg.reply_to_message_id and self.msg.chat.type != ChatType.PRIVATE:
            await self.msg.edit(lang('tip_run_in_pm'), parse_mode=ParseMode.HTML)
            return
        try:
            if int(user_id) < 0:
                return
        except (ValueError, TypeError):
            pass
        user = None
        user_id = user_id or self.msg.reply_to_message_id or (
                self.msg.chat.type == ChatType.PRIVATE and self.msg.chat.id or 0)
        if not user_id or not (user := await bot.get_users(user_id)) or (
                user.is_bot or user.is_verified or user.is_deleted):
            return
        return user.id

    # Set Black / White List
    async def _set_list(self, _type: str, array: str):
        if not array:
            return await self._display_value(
                key=_type,
                display_text=code(setting.get(_type, lang('none'))),
                sub_cmd=f"{_type[0]}l",
                value_type="vocab_array")
        if array.startswith("-c"):
            setting.delete(_type)
            return await self.msg.edit(lang(f'{_type}_reset'), parse_mode=ParseMode.HTML)
        setting.set(_type, array.replace(" ", "").split(","))
        await self.msg.edit(lang(f'{_type}_set'), parse_mode=ParseMode.HTML)

    # endregion

    def __getitem__(self, cmd: str) -> Optional[Callable]:
        # Get subcommand function
        if func := getattr(self, cmd, None):
            return func
        # Check for alias
        if func := self._get_mapped_alias(cmd, "func"):
            return func
        return  # Not found

    def get(self, cmd: str, default=None):
        return self[cmd] or default

    async def pmcaptcha(self):
        """查询当前用户的验证状态"""
        if not (user_id := await self._get_user_id(self.msg.chat.id)):
            return await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)
        await self.msg.edit(lang(f'verify_{"" if setting.is_verified(user_id) else "un"}verified'),
                            parse_mode=ParseMode.HTML)
        await asyncio.sleep(5)
        await self.msg.safe_delete()

    async def version(self):
        """查看 PMCaptcha 当前版本

        :alias: v, ver
        """
        await self.msg.edit(f"{lang('curr_version') % get_version()}")

    async def help(self, command: Optional[str], search_str: Optional[str] = None):
        """显示指令帮助信息
        搜索：
            - 使用 <code>,{cmd_name} search [搜索内容]</code> 进行文档、指令(和别名)搜索

        :param opt command: 命令名称
        :param opt search_str: 搜索的文字，只有 command 为 search 时有效
        :alias: h
        """
        if not setting.is_verified(self.user.id) and self.msg.chat.type not in (ChatType.PRIVATE, ChatType.BOT):
            await self.msg.edit_text(lang('tip_run_in_pm'), parse_mode=ParseMode.HTML)
            await asyncio.sleep(5)
            return await self.msg.safe_delete()
        help_msg = [f"{code('PMCaptcha')} {lang('cmd_list')}:", ""]
        footer = [
            italic(lang('cmd_detail')),
            "",
            f"{lang('priority')}:\n{' > '.join(Rule._get_rules_priority())}",
            "",
            f"遇到任何问题请先 {code(',apt update')} 、 {code(',restart')} 后复现再反馈",
            (f"👉 {gen_link('捐赠网址', 'https://afdian.net/@xtaodada')} "
             f"{gen_link('捐赠说明', 'https://t.me/PagerMaid_Modify/121')} "
             f"(v{get_version()})"),
        ]
        if command == "search":  # Search for commands or docs
            if not search_str:
                return await self.help("h")
            search_str = search_str.lower()
            search_results = [lang('cmd_search_result') % search_str]
            have_doc = False
            have_cmd = False
            for name, func in inspect.getmembers(self, inspect.iscoroutinefunction):
                if name.startswith("_"):
                    continue
                # Search for docs
                docs = func.__doc__ or ""
                if docs.lower().find(search_str) != -1:
                    not have_doc and search_results.append(f"{lang('cmd_search_docs')}:")
                    have_doc = True
                    search_results.append(self._extract_docs(func.__name__, docs))
                # Search for commands
                if name.find(search_str) != -1:
                    not have_cmd and search_results.append(f"{lang('cmd_search_cmds')}:")
                    have_cmd = True
                    search_results.append(
                        (code(f"- {code(self._get_cmd_with_param(name))}".strip())
                         + f"\n· {re.search(r'(.+)', docs)[1].strip()}\n"))
                # Search for aliases
                elif result := re.search(self.alias_rgx, docs):
                    if search_str not in result[1].replace(" ", "").split(","):
                        continue
                    not have_cmd and search_results.append(f"{lang('cmd_search_cmds')}:")
                    have_cmd = True
                    search_results.append(
                        (f"* {code(search_str)} -> {code(self._get_cmd_with_param(func.__name__))}".strip()
                         + f"\n· {re.search(r'(.+)', docs)[1].strip()}\n"))
            len(search_results) == 1 and search_results.append(italic(lang('cmd_search_none')))
            return await self.msg.edit("\n\n".join(search_results), parse_mode=ParseMode.HTML)
        elif command:  # Single command help
            func = getattr(self, command, self._get_mapped_alias(command, "func"))
            return await (
                self.msg.edit_text(self._extract_docs(func.__name__, func.__doc__ or ''), parse_mode=ParseMode.HTML)
                if func else self.msg.edit_text(f"{lang('cmd_not_found')}: {code(command)}", parse_mode=ParseMode.HTML))
        members = inspect.getmembers(self, inspect.iscoroutinefunction)
        members.sort(key=sort_line_number)
        for name, func in members:
            if name.startswith("_"):
                continue
            help_msg.append(
                (code(f",{cmd_name} {self._get_cmd_with_param(name)}".strip())
                 + f"\n· {re.search(r'(.+)', func.__doc__ or '')[1].strip()}\n"))
        await self.msg.edit_text("\n".join(help_msg + footer), parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    # region Checking User / Manual update

    async def check(self, _id: Optional[str]):
        """查询指定用户验证状态，如未指定为当前私聊用户 ID

        :param opt _id: 用户 ID
        """
        if not (user_id := await self._get_user_id(_id)):
            return await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)
        await self.msg.edit(lang(f"user_{'' if setting.is_verified(user_id) else 'un'}verified") % _id,
                            parse_mode=ParseMode.HTML)

    async def add(self, _id: Optional[str]):
        """将 ID 加入已验证，如未指定为当前私聊用户 ID

        :param opt _id: 用户 ID
        """
        if not (user_id := await self._get_user_id(_id)):
            return await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)
        result = setting.whitelist.add_id(user_id)
        await bot.unarchive_chats(chat_ids=user_id)
        await self.msg.edit(lang(f"add_whitelist_{'success' if result else 'failed'}") % user_id,
                            parse_mode=ParseMode.HTML)

    async def delete(self, _id: Optional[str]):
        """移除 ID 验证记录，如未指定为当前私聊用户 ID

        :param opt _id: 用户 ID
        :alias: del
        """
        if not (user_id := await self._get_user_id(_id)):
            return await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)
        text = lang(f"remove_verify_log_{'success' if setting.whitelist.del_id(user_id) else 'not_found'}")
        await self.msg.edit(text % user_id, parse_mode=ParseMode.HTML)

    # endregion

    async def unstuck(self, _id: Optional[str]):
        """解除一个用户的验证状态，通常用于解除卡死的验证状态

        :param opt _id: 用户 ID
        """
        if not (user_id := await self._get_user_id(_id)):
            return await self.msg.edit(lang('invalid_user_id'), parse_mode=ParseMode.HTML)
        captcha = None
        if (state := setting.get_challenge_state(user_id)) or (captcha := curr_captcha.get(user_id)):
            await CaptchaTask.archive(user_id, un_archive=True)
            try:
                (captcha and captcha.type or state.get("type", "math")) == "img" and await bot.unblock_user(user_id)
            except Exception as e:
                console.error(f"Error when unblocking user {user_id}: {e}\n{traceback.format_exc()}")
            if captcha:
                del curr_captcha[user_id]
            state and setting.del_challenge_state(user_id)
            return await self.msg.edit(lang('unstuck_success') % user_id, parse_mode=ParseMode.HTML)
        await self.msg.edit(lang('not_stuck') % user_id, parse_mode=ParseMode.HTML)

    async def welcome(self, *message: Optional[str]):
        """查看或设置验证通过时发送的消息
        使用 <code>,{cmd_name} welcome -c</code> 可恢复默认规则

        :param opt message: 消息内容
        :alias: wel
        """
        if not message:
            return await self._display_value(
                key="welcome",
                display_text=code(setting.get('welcome', lang('none'))),
                sub_cmd="wel",
                value_type="vocab_msg")
        message = " ".join(message)
        if message.startswith("-c"):
            setting.delete("welcome")
            return await self.msg.edit(lang('welcome_reset'), parse_mode=ParseMode.HTML)
        setting.set("welcome", message)
        await self.msg.edit(lang('welcome_set'), parse_mode=ParseMode.HTML)

    async def whitelist(self, array: Optional[str]):
        """查看或设置关键词白名单列表（英文逗号分隔）
        使用 <code>,{cmd_name} whitelist -c</code> 可清空列表

        :param opt array: 白名单列表 (英文逗号分隔)
        :alias: wl, whl
        """
        return await self._set_list("whitelist", array)

    async def blacklist(self, array: Optional[str]):
        """查看或设置关键词黑名单列表 (英文逗号分隔)
        使用 <code>,{cmd_name} blacklist -c</code> 可清空列表

        :param opt array: 黑名单列表 (英文逗号分隔)
        :alias: bl
        """
        return await self._set_list("blacklist", array)

    async def timeout(self, seconds: Optional[int], _type: Optional[str]):
        """查看或设置超时时间，默认为 <code>30</code> 秒；图像模式为 <code>5</code> 分钟
        使用 <code>,{cmd_name} wait off</code> 可关闭验证时间限制

        在图像模式中，此超时时间会于用户最后活跃而重置，
        建议数值设置大一点让机器人有一个时间可以处理后端操作

        :param opt seconds: 超时时间，单位秒
        :param opt _type: 验证类型，默认为当前类型
        :alias: wait
        """
        if _type and _type not in ("math", "img"):
            return await self.help("wait")
        captcha_type: str = _type or setting.get("type", "math")
        key_name: str = {
            "img": "img_timeout",
            "math": "timeout"
        }.get(captcha_type)
        default_timeout_time: int = {
            "img": 300,
            "math": 30
        }.get(captcha_type)
        if seconds is None:
            return await self._display_value(
                display_text=lang('timeout_curr_rule') % int(setting.get(key_name, default_timeout_time)),
                sub_cmd="wait",
                value_type="vocab_int")
        elif seconds == "off":
            setting.delete(key_name)
            return await self.msg.edit(lang('timeout_off'), parse_mode=ParseMode.HTML)
        if seconds < 0:
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        setting.set(key_name, seconds)
        await self.msg.edit(lang('timeout_set') % seconds, parse_mode=ParseMode.HTML)

    async def disable_pm(self, toggle: Optional[str]):
        """启用 / 禁止陌生人私聊，默认为 <code>N</code> （允许私聊）
        此功能会放行联系人和白名单(<i>已通过验证</i>)用户
        您可以使用 <code>,{cmd_name} add</code> 将用户加入白名单

        :param opt toggle: 开关 (y / n)
        :alias: disablepm, disable
        """
        if not toggle:
            return await self._display_value(
                display_text=lang('disable_pm_curr_rule') % lang('enabled' if setting.get('disable') else 'disabled'),
                sub_cmd="disable_pm",
                value_type="vocab_bool")
        await self._set_toggle("disable", toggle)

    async def stats(self, arg: Optional[str]):
        """查看验证统计
        使用 <code>,{cmd_name} stats -c</code> 重置数据

        :param opt arg: 参数 (reset)
        """
        if not arg:
            data = (setting.get('pass', 0) + setting.get('banned', 0), setting.get('pass', 0), setting.get('banned', 0))
            return await self.msg.edit_text(f"{code('PMCaptcha')} {lang('stats_display') % data}",
                                            parse_mode=ParseMode.HTML)
        if arg.startswith("-c"):
            setting.delete('pass').delete('banned')
            return await self.msg.edit(lang('stats_reset'), parse_mode=ParseMode.HTML)

    async def action(self, action: Optional[str]):
        """选择验证失败的处理方式，默认为 <code>none</code>
        处理方式如下：
        - <code>ban</code> | 封禁
        - <code>delete</code> | 封禁并删除对话
        - <code>none</code> | 不执行任何操作

        :param opt action: 处理方式 (<code>ban</code> / <code>delete</code> / <code>none</code>)
        :alias: act
        """
        if not action:
            action = setting.get("action", "none")
            return await self._display_value(
                key="action",
                display_text=lang(f"action_{action == 'none' and 'set_none' or action}"),
                sub_cmd="act",
                value_type="action_param_name")
        if action not in ("ban", "delete", "none"):
            return await self.help("act")
        if (action == "none" and setting.delete("action") or setting.set("action", action)) == action:
            return await self.msg.edit(lang('action_set') % lang(f'action_{action}'), parse_mode=ParseMode.HTML)
        await self.msg.edit(lang('action_set_none'), parse_mode=ParseMode.HTML)

    async def report(self, toggle: Optional[str]):
        """选择验证失败后是否举报该用户，默认为 <code>N</code>

        :param opt toggle: 开关 (y / n)
        """
        if not toggle:
            return await self._display_value(
                display_text=lang('report_curr_rule') % lang('enabled' if setting.get('report') else 'disabled'),
                sub_cmd="report",
                value_type="vocab_bool")
        await self._set_toggle("report", toggle)

    async def premium(self, action: Optional[str]):
        """选择对 <b>Premium</b> 用户的操作，默认为 <code>none</code>
        处理方式如下：
        - <code>allow</code> | 白名单
        - <code>ban</code> | 封禁
        - <code>only</code> | 只允许
        - <code>none</code> | 不执行任何操作

        :param opt action: 处理方式 (<code>allow</code> / <code>ban</code> / <code>only</code> / <code>none</code>)
        :alias: vip, prem
        """
        if not action:
            return await self._display_value(
                key="premium",
                display_text=lang(f'premium_set_{setting.get("premium", "none")}'),
                sub_cmd="vip",
                value_type="action_param_name")
        if action not in ("allow", "ban", "only", "none"):
            return await self.help("vip")
        action == "none" and setting.delete("action") or setting.set("action", action)
        await self.msg.edit(lang(f'premium_set_{action}'), parse_mode=ParseMode.HTML)

    async def groups_in_common(self, count: Optional[int]):
        """设置是否对拥有一定数量的共同群的用户添加白名单
        使用 <code>,{cmd_name} groups -1</code> 重置设置

        :param opt count: 共同群数量
        :alias: group, groups, common
        """
        if not count:
            groups = setting.get('groups_in_common')
            text = lang(f"groups_in_common_{'set' if groups is not None else 'disabled'}")
            if groups is not None:
                text = text % groups
            return await self._display_value(
                display_text=text,
                sub_cmd="groups",
                value_type="vocab_int")
        if count == -1:
            setting.delete('groups_in_common')
            return await self.msg.edit(lang('groups_in_common_disable'), parse_mode=ParseMode.HTML)
        elif count < 0:
            return await self.help("groups_in_common")
        setting.set('groups_in_common', count)
        await self.msg.edit(lang('groups_in_common_set') % count, parse_mode=ParseMode.HTML)

    async def chat_history(self, count: Optional[int]):
        """设置对拥有一定数量的聊天记录的用户添加白名单（触发验证的信息不计算在内）
        使用 <code>,{cmd_name} his -1</code> 重置设置

        <b>请注意，由于 Telegram 内部限制，信息获取有可能会不完整，请不要设置过大的数值</b>

        :param opt count: 聊天记录数量
        :alias: his, history
        """
        if not count:
            history_count = setting.get('history_count')
            text = lang("chat_history_curr_rule" if history_count is not None else "chat_history_disabled")
            if history_count is not None:
                text = text % history_count
            return await self._display_value(
                display_text=text,
                sub_cmd="his",
                value_type="vocab_bool")
        setting.set('history_count', count)
        await self.msg.edit(lang('chat_history_curr_rule') % count, parse_mode=ParseMode.HTML)

    async def initiative(self, toggle: Optional[str]):
        """设置对主动进行对话的用户添加白名单，默认为 <code>N</code>

        :param opt toggle: 开关 (y / n)
        """
        if not toggle:
            return await self._display_value(
                display_text=lang('initiative_curr_rule') % lang(
                    'enabled' if setting.get('initiative', False) else 'disabled'),
                sub_cmd="initiative",
                value_type="vocab_bool")
        await self._set_toggle("initiative", toggle)

    async def silent(self, toggle: Optional[str]):
        """减少信息发送，默认为 <code>N</code>
        开启后，将不会发送封禁提示 (不影响 log 发送)

        :param opt toggle: 开关 (y / n)
        :alias: quiet
        """
        if not toggle:
            return await self._display_value(
                display_text=lang('silent_curr_rule') % lang('enabled' if setting.get('silent', False) else 'disabled'),
                sub_cmd="quiet",
                value_type="vocab_bool")
        await self._set_toggle("silent", toggle)

    async def flood(self, limit: Optional[int]):
        """设置一分钟内超过 <code>n</code> 人开启轰炸检测机制，默认为 <code>50</code> 人
        此机制会在用户被轰炸时启用，持续 <code>5</code> 分钟，假如有用户继续进行私聊计时将会重置

        当轰炸开始时，<code>PMCaptcha</code> 将会启动以下一系列机制
        - 强制开启自动归档（无论是否 <code>Telegram Premium</code> 用户都会尝试开启）
        - 不向用户发送 <code>CAPTCHA</code> 挑战
        - 继上面的机制，记录未发送 <code>CAPTCHA</code> 的用户 ID
        - （用户可选）创建临时频道，并把用户名转移到创建的频道上 【默认关闭】

        轰炸结束后，如果用户名已转移到频道上，将恢复用户名，并删除频道
        并对记录收集机器人发送轰炸的<code>用户数量</code>、<code>轰炸开始时间</code>、<code>轰炸结束时间</code>、<code>轰炸时长</code>（由于不存在隐私问题，此操作为强制性）

        请参阅 <code>,{cmd_name} h flood_username</code> 了解更多有关创建临时频道的机制
        请参阅 <code>,{cmd_name} h flood_act</code> 查看轰炸结束后的处理方式

        :param opt limit: 人数限制
        :alias: boom
        """
        if not limit:
            return await self._display_value(
                display_text=lang('flood_curr_rule') % setting.get('flood_limit', 50),
                sub_cmd="flood",
                value_type="vocab_int")
        setting.set('flood_limit', limit)
        await self.msg.edit(lang('flood_curr_rule') % limit, parse_mode=ParseMode.HTML)

    async def flood_username(self, toggle: Optional[str]):
        """设置是否在轰炸时启用“转移用户名到临时频道”机制（如有用户名）
        将此机制分开出来的原因是此功能有可能会被抢注用户名<i>(虽然经测试临时取消用户名并不会出现此问题)</i>
        但为了万一依然分开出来作为一个选项了

        启用后，在轰炸机制开启时，会进行以下操作
        - 创建临时频道
        - （如创建成功）清空用户名，设置用户名为临时频道，并在频道简介设置正在受到轰炸提示
        - （如设置失败）恢复用户名，删除频道

        :param opt toggle: 开关 (y / n)
        :alias: boom_username
        """
        global user_want_set_flood_username
        if not toggle:
            return await self._display_value(
                display_text=lang('flood_username_curr_rule') % lang(
                    'enabled' if setting.get('flood_username', False) else 'disabled'),
                sub_cmd="flood_username",
                value_type="vocab_bool")
        if toggle in ("y", "t", "1", "on") and not user_want_set_flood_username:
            user_want_set_flood_username = True
            return await self.msg.edit(lang('flood_username_set_confirm'), parse_mode=ParseMode.HTML)
        user_want_set_flood_username = None
        await self._set_toggle("flood_username", toggle)

    async def flood_act(self, action: Optional[str]):
        """设置轰炸结束后进行的处理方式，默认为 <code>none</code>
        可用的处理方式如下：
        - <code>asis</code> | 与验证失败的处理方式一致，但不会进行验证失败通知
        - <code>captcha</code> | 对每个用户进行 <code>CAPTCHA</code> 挑战
        - <code>none</code> | 不进行任何操作

        :param opt action: 处理方式
        :alias: boom_act
        """
        if not action:
            return await self._display_value(
                display_text=lang('flood_act_curr_rule') % lang(f"flood_act_set_{setting.get('flood_act', 'none')}"),
                sub_cmd="flood_act",
                value_type="vocab_str")
        if action not in ("asis", "captcha", "none"):
            return await self.help("flood_act")
        action == "none" and setting.delete("flood_act") or setting.set("flood_act", action)
        await self.msg.edit(lang(f'flood_act_set_{action}'), parse_mode=ParseMode.HTML)

    async def collect_logs(self, toggle: Optional[str]):
        """查看或设置是否允许 <code>PMCaptcha</code> 收集验证错误相关信息以帮助改进
        默认为 <code>Y</code>，收集的信息包括被验证者的信息以及未通过验证的信息记录

        :param opt toggle: 开关 (y / n)
        :alias: collect, log
        """
        if not toggle:
            status = lang('enabled' if setting.get('collect', True) else 'disabled')
            return await self._display_value(
                display_text=f"{lang('collect_logs_curr_rule') % status}\n{lang('collect_logs_note')}",
                sub_cmd="log",
                value_type="vocab_bool")
        await self._set_toggle("collect_logs", toggle)

    async def change_type(self, _type: Optional[str]):
        """切换验证码类型，默认为 <code>math</code>
        验证码类型如下：
        - <code>math</code> | 计算验证
        - <code>img</code> | 图像辨识验证

        <b>注意：如果图像验证不能使用将回退到计算验证</b>

        :param opt _type: 验证码类型 (<code>img</code> / <code>math</code>)
        :alias: type, typ
        """
        if not _type:
            return await self._display_value(
                display_text=lang('type_curr_rule') % lang(f'type_captcha_{setting.get("type", "math")}'),
                sub_cmd="typ",
                value_type="type_param_name")
        if _type not in ("img", "math"):
            return await self.help("typ")
        _type == "math" and setting.delete("type") or setting.set("type", _type)
        await self.msg.edit(lang('type_set') % lang(f'type_captcha_{_type}'), parse_mode=ParseMode.HTML)

    # Image Captcha

    async def change_img_type(self, _type: Optional[str]):
        """切换图像辨识使用接口，默认为 <code>func</code>
        目前可用的接口：
        - <code>func</code> (<i>ArkLabs funCaptcha</i> )
        - <code>github</code> (<i>GitHub 螺旋星系</i> )
        - <code>rec</code> (<i>Google reCAPTCHA</i> )

        请注意， <code>reCAPTCHA</code> 难度相比前两个<a href="https://t.me/c/1441461877/958395">高出不少</a>，
        因此验证码系统会在尝试过多后提供 <code>funCaptcha</code> 接口让用户选择

        :param opt _type: 验证码类型 (<code>func</code> / <code>github</code> / <code>rec</code>)
        :alias: img_type, img_typ
        """
        if not _type:
            return await self._display_value(
                display_text=lang('type_curr_rule') % lang(f'img_captcha_type_{setting.get("img_type", "func")}'),
                sub_cmd="img_typ",
                value_type="type_param_name")
        if _type not in ("func", "github", "rec"):
            return await self.help("img_typ")
        _type == "func" and setting.delete("img_type") or setting.set("img_type", _type)
        await self.msg.edit(lang('type_set') % lang(f'img_captcha_type_{_type}'), parse_mode=ParseMode.HTML)

    async def img_retry_chance(self, number: Optional[int]):
        """图形验证码最大可重试次数，默认为 <code>3</code>

        :param opt number: 重试次数
        :alias: img_re
        """
        if number is None:
            return await self._display_value(
                display_text=lang('img_captcha_retry_curr_rule') % setting.get("img_max_retry", 3),
                sub_cmd="img_re",
                value_type="vocab_int")
        if number < 0:
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        setting.set("img_max_retry", number)
        await self.msg.edit(lang('img_captcha_retry_set') % number, parse_mode=ParseMode.HTML)


# region Captcha

@dataclass
class TheOrder:
    """Worker of blocking user (Punishment)"""
    queue = asyncio.Queue()
    task: Optional[asyncio.Task] = None
    flood_text = "[The Order] Flood Triggered: wait %is, Command: %s, Target: %s"

    def __post_init__(self):
        if pending := setting.pending_ban_list.get_subs():
            console.debug(f"Pending user(s) to ban: {len(pending)}")
            for user_id in pending:
                self.queue.put_nowait((user_id,))

    async def worker(self):
        console.debug("Punishment Worker started")
        while True:
            target = None
            try:
                (target,) = await self.queue.get()
                action = setting.get("action", "none")
                if action in ("ban", "delete"):
                    for _ in range(3):
                        try:
                            await bot.block_user(user_id=target)
                            break
                        except FloodWait as e:
                            console.info(self.flood_text % (e.value, "Block", target))
                            await asyncio.sleep(e.value)
                        except Exception as e:
                            console.debug(f"Failed to block user {target}: {e}\n{traceback.format_exc()}")
                    if action == "delete":
                        for _ in range(3):
                            try:
                                await bot.invoke(messages.DeleteHistory(
                                    just_clear=False,
                                    revoke=False,
                                    peer=await bot.resolve_peer(target),
                                    max_id=0))
                                break
                            except FloodWait as e:
                                console.info(self.flood_text % (e.value, "Delete Message", target))
                                await asyncio.sleep(e.value)
                            except Exception as e:
                                console.debug(f"Failed to delete user {target}: {e}\n{traceback.format_exc()}")
                setting.pending_ban_list.del_id(target)
                setting.get_challenge_state(target) and setting.del_challenge_state(target)
                setting.set("banned", setting.get("banned", 0) + 1)
                chat_link = gen_link(str(target), f"tg://user?id={target}")
                text = f"[PMCaptcha - The Order] {lang('verify_log_punished')} (Punishment)"
                action not in ("none", "archive") and await log(text % (chat_link, lang(f'action_{action}')), True)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await log(f"Error occurred when punishing user: {e}\n{traceback.format_exc()}")
            finally:
                target and self.queue.task_done()

    async def active(self, user_id: int, reason_code: str):
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.worker())
        try:
            user = await bot.get_users(user_id)
            not setting.get("silent") and await bot.send_message(user_id, " ".join((
                lang(reason_code, user.language_code),
                lang("verify_blocked", user.language_code)
            )))
        except FloodWait:
            pass  # Skip waiting
        finally:
            setting.pending_ban_list.add_id(user_id)
            self.queue.put_nowait((user_id,))
            console.debug(f"User {user_id} added to ban queue")


@dataclass
class TheWorldEye:
    """Anti-Flooding System

    Actual name of each functions:
    - sophitia -> Watcher
    - synchronize -> flood_triggered
    - overload -> flood_ended
    """
    queue = asyncio.Queue()
    watcher: Optional[asyncio.Task] = None
    timer_task: Optional[asyncio.Task] = None

    # Watcher
    last_challenge_time: Optional[int] = None
    level: int = 0

    # Post Init Value
    channel_id: Optional[int] = None
    username: Optional[str] = None
    triggered: bool = False
    start: Optional[int] = None
    update: Optional[int] = None
    end: Optional[int] = None
    user_ids: Optional[list] = field(init=False)
    auto_archive_enabled_default: Optional[bool] = None

    def __post_init__(self):
        self.user_ids = []
        if state := setting.get_flood_state():  # PMCaptcha restarts, flood keeps going
            # Resume last flood state
            now = int(time.time())
            self.triggered = True
            self.channel_id = state.get("channel_id")
            self.username = state.get("username")
            self.start = state.get("start")
            self.update = state.get("update")
            self.user_ids = state.get("user_ids")
            self.auto_archive_enabled_default = state.get("auto_archive_enabled_default")
            self.reset_timer(300 - (now - self.start))
            console.debug("PMCaptcha restarted, flood state resume")
        self.watcher = asyncio.create_task(self.sophitia())

    # region Timer

    async def _flood_timer(self, interval: int):
        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            return
        console.debug("Flood ends")
        self.triggered = False
        self.end = int(time.time())
        await self.overload()

    def reset_timer(self, interval: int = 300):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.update = int(time.time())
        self.timer_task = asyncio.create_task(self._flood_timer(interval))
        console.debug("Flood timer reset")
        return self

    # endregion

    async def _set_channel_username(self):
        console.debug("Creating temporary channel")
        try:
            channel = await bot.create_supergroup(
                "PMCaptcha Temporary Channel",
                about="\n\n".join((lang("flood_channel_desc", "en"), lang("flood_channel_desc", "zh"))))
            console.debug("Temporary channel created")
            self.channel_id = channel.id
        except Exception as e:
            await log(f"Failed to create temporary channel: {e}\n{traceback.format_exc()}")
            return False
        console.debug("Moving username to temporary channel")
        try:
            await bot.set_username(None)
        except Exception as e:
            await log(f"Failed to remove username: {e}\n{traceback.format_exc()}")
            return False
        result = False
        try:
            await bot.invoke(UpdateUsername(channel=await bot.resolve_peer(channel.id), username=self.username))
            result = True
        except ChannelsAdminPublicTooMuch:
            await log("Failed to move username to temporary channel, too many public channels")
        except Exception as e:
            await log(f"Failed to set username for channel: {e}\n{traceback.format_exc()}")
        if not result:
            console.debug("Setting back username")
            try:
                await bot.set_username(self.username)
                await bot.delete_supergroup(channel.id)
            except Exception as e:
                await log(f"Failed to set username back: {e}\n{traceback.format_exc()}")
            self.username = None
        return result

    async def _restore_username(self):
        if self.channel_id:
            console.debug("Deleting temporary channel")
            try:
                await bot.invoke(
                    UpdateUsername(channel=await bot.resolve_peer(self.channel_id), username=self.username)
                )
            except Exception as e:
                await log(f"Failed to remove username for channel: {e}\n{traceback.format_exc()}")
            try:
                await bot.delete_supergroup(self.channel_id)
            except Exception as e:
                console.debug(f"Failed to delete temporary channel: {e}\n{traceback.format_exc()}")
        if self.username:
            console.debug("Setting back username")
            try:
                await bot.set_username(self.username)
            except Exception as e:
                await log(f"Failed to set username back: {e}\n{traceback.format_exc()}")
        self.username = self.channel_id = None

    # region State

    def save_state(self):
        setting.set_flood_state({
            "start": self.start,
            "update": self.update,
            "user_ids": self.user_ids,
            "auto_archive_enabled_default": self.auto_archive_enabled_default,
            "username": self.username,
            "channel_id": self.channel_id
        })

    def update_state(self):
        data = setting.get_flood_state()
        data.update({
            "update": self.update,
            "user_ids": self.user_ids,
        })
        setting.set_flood_state(data)

    @staticmethod
    def del_state():
        setting.del_flood_state()

    # endregion

    # noinspection SpellCheckingInspection
    async def sophitia(self):
        """Watches the private message chat (World)"""
        console.debug("Flood Watcher started")
        while True:
            user_id = None
            try:
                (user_id,) = await self.queue.get()
                if self.triggered:  # Continues flooding, add to list and reset timer
                    self.reset_timer()
                    self.user_ids.append(user_id)
                    console.debug(f"User {user_id} added to flood list")
                    self.update_state()
                    continue
                now = int(time.time())
                if self.last_challenge_time and now - self.last_challenge_time < 60:
                    # A user is challenged less than a min
                    self.level += 1
                elif not self.last_challenge_time or now - self.last_challenge_time > 60:
                    self.level = 1
                self.last_challenge_time = now
                if self.level >= setting.get("flood_limit", 50):
                    console.warn(f"Flooding detected: {self.level} reached in 1 min")
                    self.triggered = True
                    self.start = self.update = now
                    self.reset_timer()
                    await self.synchronize()
            except asyncio.CancelledError:
                break
            except Exception as e:
                await log(f"Error occurred in flood watcher: {e}\n{traceback.format_exc()}")
            finally:
                user_id and self.queue.task_done()

    async def add_synchronize(self, user_id: int):
        await self.queue.put((user_id,))

    async def synchronize(self):
        """Triggered when flood starts (Iris has started synchronizing people)"""
        # Force enable auto archive to reduce api flood
        settings: GlobalPrivacySettings = await bot.invoke(GetGlobalPrivacySettings())
        self.auto_archive_enabled_default = settings.archive_and_mute_new_noncontact_peers
        if settings.archive_and_mute_new_noncontact_peers:
            console.debug("Enabling auto archive")
            try:
                await bot.invoke(SetGlobalPrivacySettings(
                    settings=GlobalPrivacySettings(archive_and_mute_new_noncontact_peers=True)
                ))
                console.debug("Auto archive enabled")
            except AutoarchiveNotAvailable:
                console.warn("Auto archive is not available, API Flooding may be larger than expected")
            except Exception as e:
                console.error(f"Failed to enable auto archive: {e}\n{traceback.format_exc()}")
        if setting.get("flood_username") and bot.me.username:
            self.username = bot.me.username
            console.debug("Moving username to temporary channel")
            if not await self._set_channel_username():
                self.username = None
        # Save state
        self.save_state()

    async def overload(self):
        """Executed after flood ends (Nine has performed load action)"""
        console.info(f"Flood ended, {len(self.user_ids)} users were affected, duration: {self.end - self.start}s")
        if self.channel_id or self.username:
            console.debug("Changing back username")
            await self._restore_username()
        try:
            await bot.send_message(log_collect_bot, "\n".join((
                "FLOOD",
                f"User Count: {code(str(len(self.user_ids)))}"
                f"Start: {code(str(self.start))}",
                f"End: {code(str(self.end))}",
                f"Duration: {code(str(self.end - self.start))}s",
            )))
        except Exception as e:
            console.debug(f"Failed to send flood log: {e}\n{traceback.format_exc()}")
        if not self.auto_archive_enabled_default:  # Restore auto archive setting
            try:
                await bot.invoke(SetGlobalPrivacySettings(
                    settings=GlobalPrivacySettings(archive_and_mute_new_noncontact_peers=False)
                ))
                console.debug("Auto archive disabled")
            except Exception as e:
                console.debug(f"Failed to disable auto archive: {e}\n{traceback.format_exc()}")
        flood_act = setting.get("flood_act")
        if flood_act == "asis":
            if not the_order.task or the_order.task.done():
                the_order.task = asyncio.create_task(the_order.worker())
            for user_id in self.user_ids:
                await the_order.queue.put((user_id,))
                await asyncio.sleep(5)
        elif flood_act == "captcha":
            if not captcha_task.task or captcha_task.task.done():
                captcha_task.task = asyncio.create_task(captcha_task.worker())
            for user_id in self.user_ids:
                if (setting.pending_challenge_list.check_id(user_id) or curr_captcha.get(user_id) or
                        setting.get_challenge_state(user_id)):
                    continue
                await self.queue.put((user_id, None, None, None))
                setting.pending_challenge_list.add_id(user_id)
                console.debug(f"User {user_id} added to challenge queue")
                await asyncio.sleep(8)
        self.user_ids.clear()
        self.start = self.end = self.update = self.auto_archive_enabled_default = None
        self.del_state()


@dataclass
class CaptchaTask:
    """A class to start, resume and verify the captcha challenge
    and contains some nice function like archiving user, getting user's settings

    The main function of this class is to queue & start a captcha for the user
    """
    queue = asyncio.Queue()
    task: Optional[asyncio.Task] = None
    flood_text = "[CaptchaTask] Flood Triggered: wait %is, Command: %s, Target: %s"

    def __post_init__(self):
        if pending := setting.pending_challenge_list.get_subs():
            console.debug(f"Pending user(s) to challenge: {len(pending)}")
            for user_id in pending:
                self.queue.put_nowait((user_id, None, None, None))

    @staticmethod
    async def archive(user_id: int, *, un_archive: bool = False):
        from pyrogram.raw.functions.account import UpdateNotifySettings
        from pyrogram.raw.types import InputNotifyPeer, InputPeerNotifySettings
        notify_setting = InputPeerNotifySettings(**{
            "mute_until": None if un_archive else 2147483647,
            "show_previews": True if un_archive else None,
            "silent": False if un_archive else None
        })
        peer = InputNotifyPeer(peer=await bot.resolve_peer(user_id))
        for _ in range(3):
            try:
                await bot.invoke(UpdateNotifySettings(peer=peer, settings=notify_setting))
                await (bot.unarchive_chats if un_archive else bot.archive_chats)(user_id)
                break
            except FloodWait as e:
                console.debug(f"{'Un' if un_archive else ''}Archive triggered flood for {user_id}, wait {e.value}s")
                await asyncio.sleep(e.value)
            except Exception as e:
                console.debug(f"{'Un' if un_archive else ''}Archive failed for {user_id}, {e}")

    @staticmethod
    async def get_user_settings(user_id: int) -> (bool, bool):
        can_report = True
        auto_archived = False
        for _ in range(3):
            try:
                peer_settings: PeerSettings = await bot.invoke(
                    messages.GetPeerSettings(peer=await bot.resolve_peer(user_id)))
                can_report = peer_settings.settings.report_spam
                auto_archived = peer_settings.settings.autoarchived
                break
            except FloodWait as e:
                console.debug(f"GetPeerSettings triggered flood for {user_id}, wait {e.value}s")
                await asyncio.sleep(e.value)
            except Exception as e:
                console.debug(f"GetPeerSettings failed for {user_id}, {e}")
        return can_report, auto_archived

    async def worker(self):
        console.debug("Captcha Challenge Worker started")
        while True:
            user_id: Optional[int] = None
            try:
                user_id, msg, can_report, auto_archived = await self.queue.get()
                user = msg and msg.from_user or await bot.get_users(user_id)
                if can_report is None or auto_archived is None:
                    can_report, auto_archived = await self.get_user_settings(user_id)
                if (last_captcha := setting.get_challenge_state(user_id)) and not curr_captcha.get(user_id):
                    # Resume last captcha challenge
                    if last_captcha["type"] not in captcha_challenges:
                        console.info("Failed to resume last captcha challenge: "
                                     f"Unknown challenge type {last_captcha['type']}")
                        continue
                    await captcha_challenges[last_captcha["type"]].resume(user=user, msg=msg, state=last_captcha)
                    continue
                # Start a captcha challenge
                await self.archive(user_id)
                captcha = (captcha_challenges.get(setting.get("type", "math"), MathChallenge)
                           (msg.from_user, can_report))
                captcha.log_msg(msg and (msg.text or msg.caption or "") or None)
                captcha = await captcha.start() or captcha
                curr_captcha[user_id] = captcha
                setting.pending_challenge_list.del_id(user_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                await log(f"Error occurred when challenging user: {e}\n{traceback.format_exc()}")
            finally:
                user_id and self.queue.task_done()

    async def add(self, user_id: int, msg: Optional[Message], can_report: Optional[bool],
                  auto_archived: Optional[bool]):
        await the_world_eye.add_synchronize(user_id)
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.worker())
        if not (setting.pending_challenge_list.check_id(user_id) or curr_captcha.get(user_id) or
                setting.get_challenge_state(user_id)):
            setting.pending_challenge_list.add_id(user_id)
            self.queue.put_nowait((user_id, msg, can_report, auto_archived))
            console.debug(f"User {user_id} added to challenge queue")


@dataclass
class CaptchaChallenge:
    type: str
    user: User
    input: bool
    logs: List[str] = field(init=False, default_factory=list)
    captcha_write_lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    # User Settings
    can_report: bool = True

    # Post Init Value
    captcha_start: int = 0
    challenge_msg_id: Optional[int] = None
    timer_task: Optional[asyncio.Task] = None

    # region Logging

    def log_msg(self, msg: Optional[str]):
        if isinstance(msg, str) and not msg.strip():
            return
        self.logs.append(isinstance(msg, str) and msg.strip() or msg)

    async def send_log(self, ban_code: Optional[str] = None):
        from io import BytesIO
        if not setting.get("collect", True):
            return
        import json
        user = self.user
        log_file = BytesIO(json.dumps(self.logs, indent=4).encode())
        log_file.name = f"{user.id}_{self.captcha_start}.json"
        caption = [f"UID: {code(str(user.id))}" + (f" @{user.username}" if self.user.username else ""),
                   f"Mention: {gen_link(str(user.id), f'tg://openmessage?user_id={user.id}')}"]
        if user.first_name or user.last_name:
            user_full_name = []
            user.first_name and user_full_name.append(user.first_name)
            user.last_name and user_full_name.append(user.last_name)
            caption.append(f"Name: {code(' '.join(user_full_name))}")
        elif user.is_deleted:
            caption.append(f"Name: {bold('Deleted Account')}")
        if user.is_scam or user.is_fake or user.is_premium:
            tags = []
            user.is_scam and tags.append(code("Scam"))
            user.is_fake and tags.append(code("Fake"))
            user.is_premium and tags.append(code("Premium"))
            caption.append(f"Tags: {', '.join(tags)}")
        user.language_code and caption.append(f"Language: {code(user.language_code)}")
        user.dc_id and caption.append(f"DC: {code(str(user.dc_id))}")
        user.phone_number and caption.append(f"Phone: {code(user.phone_number)}")
        self.type and caption.append(f"Captcha Type: {code(self.type)}")
        ban_code and caption.append(f"Block Reason: {code(ban_code)}")
        send = False
        has_exp = False
        try:
            await bot.unblock_user(log_collect_bot)
        except Exception as e:
            console.error(f"Failed to unblock log collect bot: {e}\n{traceback.format_exc()}")
        for _ in range(3):
            try:
                await bot.send_document(
                    log_collect_bot, log_file, caption="\n".join(caption), parse_mode=ParseMode.HTML)
                send = True
                break
            except Exception as e:
                console.error(f"Failed to send log to log collector bot: {e}\n{traceback.format_exc()}")
                has_exp = True
        if not send and not has_exp:
            return await log("Failed to send log")
        await log(f"Log collected from user {user.id}")

    # endregion

    # region State

    def save_state(self, extra: Optional[dict] = None):
        self.captcha_start = self.captcha_start or int(time.time())
        data = {
            "type": self.type,
            "start": self.captcha_start,
            "logs": self.logs,
            "msg_id": self.challenge_msg_id,
            "report": self.can_report
        }
        extra and data.update(extra)
        setting.set_challenge_state(self.user.id, data)

    def update_state(self, changes: Optional[dict] = None):
        data = setting.get_challenge_state(self.user.id)
        changes and data.update(changes)
        setting.set_challenge_state(self.user.id, data)

    def del_state(self):
        setting.del_challenge_state(self.user.id)

    # endregion

    # region Verify Result

    async def _verify_success(self):
        setting.whitelist.add_id(self.user.id)
        setting.set("pass", setting.get("pass", 0) + 1)
        success_msg = setting.get("welcome") or lang("verify_passed", self.user.language_code)
        welcome_msg: Optional[Message] = None
        try:
            if self.challenge_msg_id:
                welcome_msg = await bot.edit_message_text(self.user.id, self.challenge_msg_id, success_msg)
        except Exception as e:
            console.error(f"Failed to edit welcome message: {e}\n{traceback.format_exc()}")
        else:
            try:
                welcome_msg = await bot.send_message(self.user.id, success_msg)
                self.challenge_msg_id = welcome_msg.id
            except Exception as e:
                console.error(f"Failed to send welcome message: {e}\n{traceback.format_exc()}")
        await asyncio.sleep(3)
        welcome_msg and await welcome_msg.safe_delete()
        await CaptchaTask.archive(self.user.id, un_archive=True)

    async def _verify_failed(self):
        try:
            self.challenge_msg_id and await bot.delete_messages(self.user.id, self.challenge_msg_id)
            (self.can_report and setting.get("report") and
             await bot.invoke(messages.ReportSpam(peer=await bot.resolve_peer(self.user.id))))
        except Exception as e:
            console.debug(f"Error occurred when executing verify failed function: {e}\n{traceback.format_exc()}")
        await the_order.active(self.user.id, "verify_failed")
        await self.send_log()

    async def action(self, success: bool):
        self.del_state()
        self.remove_timer()
        await getattr(self, f"_verify_{'success' if success else 'failed'}")()
        console.debug(f"User {self.user.id} verify {'success' if success else 'failed'}")

    # endregion

    # region Timer

    async def _challenge_timer(self, timeout: int):
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return
        except Exception as e:
            console.error(f"Error occurred when running challenge timer: {e}\n{traceback.format_exc()}")
        async with self.captcha_write_lock:
            console.debug(f"User {self.user.id} verification timed out")
            await self.action(False)
        if curr_captcha.get(self.user.id):
            del curr_captcha[self.user.id]

    def reset_timer(self, timeout: Optional[int] = None):
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        timeout = timeout is not None and timeout or setting.get(
            f"{self.type == 'img' and 'img_' or ''}timeout", self.type == "img" and 300 or 30)
        if timeout > 0:
            self.timer_task = asyncio.create_task(self._challenge_timer(timeout))
        console.debug(f"User {self.user.id} verification timer reset")
        return self

    def remove_timer(self):
        if task := self.timer_task:
            task.cancel()
        return self

    # endregion

    @classmethod
    async def resume(cls, *, user: User, msg: Optional[Message] = None, state: dict):
        console.debug(f"User {user.id} resumed captcha challenge {state['type']}")

    async def start(self):
        console.debug(f"User {self.user.id} started {self.type} captcha challenge")


class MathChallenge(CaptchaChallenge):
    answer: int

    def __init__(self, user: User, can_report: bool):
        super().__init__("math", user, True, can_report)

    @classmethod
    async def resume(cls, *, user: User, msg: Optional[Message] = None, state: dict):
        captcha = cls(user, state['report'])
        captcha.captcha_start = state['start']
        captcha.logs = state['logs']
        captcha.challenge_msg_id = state['msg_id']
        captcha.answer = state['answer']
        if (timeout := setting.get("timeout", 30)) > 0:
            time_passed = int(time.time()) - int(state['start'])
            if time_passed > timeout:
                # Timeout
                return await captcha.action(False)
            if msg:  # Verify result
                await captcha.verify(msg.text or msg.caption or "")
            else:  # Restore timer
                captcha.reset_timer(timeout - time_passed)
        await super(MathChallenge, captcha).resume(user=user, msg=msg, state=state)

    async def start(self):
        if self.captcha_write_lock.locked():
            return
        async with self.captcha_write_lock:
            import random
            full_lang = self.user.language_code
            first_value, second_value = random.randint(1, 10), random.randint(1, 10)
            timeout = setting.get("timeout", 30)
            operator = random.choice(("+", "-", "*"))
            expression = f"{first_value} {operator} {second_value}"
            challenge_msg = None
            for _ in range(3):
                try:
                    challenge_msg = await bot.send_message(self.user.id, "\n".join((
                        lang('verify_challenge', full_lang),
                        "",
                        code(f"{expression} = ?"),
                        "\n" + lang('verify_challenge_timed', full_lang) % timeout if timeout > 0 else ""
                    )), parse_mode=ParseMode.HTML)
                    break
                except FloodWait as e:
                    console.debug(f"Math captcha triggered flood for {e.value} second(s)")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    console.error(f"Failed to send challenge message to {self.user.id}: {e}\n{traceback.format_exc()}")
                    await asyncio.sleep(10)
            if not challenge_msg:
                return await log(f"Failed to send math captcha challenge to {self.user.id}")
            self.challenge_msg_id = challenge_msg.id
            self.answer = eval(expression)
            self.save_state({"answer": self.answer})
            self.reset_timer(timeout)
            await super(MathChallenge, self).start()

    async def verify(self, answer: str):
        if self.captcha_write_lock.locked():
            return
        async with self.captcha_write_lock:
            try:
                user_answer = int("".join(re.findall(r"\d+", answer)))
                if "-" in answer:
                    user_answer = -user_answer
            except ValueError:
                return await the_order.active(self.user.id, "verify_failed")
        await self.action(user_answer == self.answer)
        return user_answer == self.answer


class ImageChallenge(CaptchaChallenge):
    try_count: int

    def __init__(self, user: User, can_report: bool):
        super().__init__("img", user, False, can_report)
        self.try_count = 0

    @classmethod
    async def resume(cls, *, user: User, msg: Optional[Message] = None, state: dict):
        captcha = cls(user, state['report'])
        captcha.captcha_start = state['start']
        captcha.logs = state['logs']
        captcha.challenge_msg_id = state['msg_id']
        captcha.try_count = state['try_count']
        if captcha.try_count >= setting.get("img_max_retry", 3):
            return await captcha.action(False)
        if (timeout := setting.get("img_timeout", 300)) > 0:  # Restore timer
            time_passed = int(time.time()) - int(state['last_active'])
            if time_passed > timeout:
                # Timeout
                return await captcha.action(False)
            captcha.reset_timer(timeout - time_passed)
        curr_captcha[user.id] = captcha
        await super(ImageChallenge, captcha).resume(user=user, msg=msg, state=state)

    async def start(self):
        from pyrogram.raw.types import UpdateMessageID
        if self.captcha_write_lock.locked():
            return
        async with self.captcha_write_lock:
            while True:
                try:
                    if (not (result := await bot.get_inline_bot_results(
                            img_captcha_bot, setting.get("img_type", "func"))) or
                            not result.results):
                        console.debug(f"Failed to get captcha results from {img_captcha_bot}, fallback")
                        break  # Fallback
                    # From now on, wait for bot result
                    updates = await bot.send_inline_bot_result(self.user.id, result.query_id, result.results[0].id)
                    for update in updates.updates:
                        if isinstance(update, UpdateMessageID):
                            self.challenge_msg_id = update.id
                            self.save_state({"try_count": self.try_count, "last_active": int(time.time())})
                            await bot.block_user(self.user.id)
                            self.reset_timer()
                            await super(ImageChallenge, self).start()
                            return
                    console.debug(f"Failed to send image captcha challenge to {self.user.id}, fallback")
                    break
                except TimeoutError:
                    console.debug(f"Image captcha bot timeout for {self.user.id}, fallback")
                    break  # Fallback
                except FloodWait as e:
                    console.debug(f"Image captcha triggered flood for {self.user.id}, wait {e.value}")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    console.error(
                        f"Failed to send image captcha challenge to {self.user.id}: {e}\n{traceback.format_exc()}")
                    await asyncio.sleep(10)
            console.debug("Failed to get image captcha, fallback to math captcha.")
            fallback_captcha = MathChallenge(self.user, self.can_report)
            await fallback_captcha.start()
            return fallback_captcha

    async def verify(self, success: bool):
        if success:
            await bot.unblock_user(self.user.id)
            self.challenge_msg_id = 0
            return await self.action(success)
        else:
            self.try_count += 1
            if self.try_count >= setting.get("img_max_retry", 3):
                await self.action(False)
                return True
            console.debug(f"User failed to complete image captcha challenge, try count: {self.try_count}")
            self.update_state({"try_count": self.try_count})


# endregion

@dataclass
class Rule:
    user: User
    msg: Message

    can_report: Optional[bool] = None
    auto_archived: Optional[bool] = None

    def _precondition(self) -> bool:
        return (self.user.id in (347437156, 583325201, 1148248480) or  # Skip for PGM/PMC Developers
                self.msg.from_user.is_contact or
                self.msg.from_user.is_verified or
                self.user.is_self or
                self.msg.chat.type == ChatType.BOT or
                setting.is_verified(self.user.id))

    def _get_text(self) -> str:
        return self.msg.text or self.msg.caption or ""

    async def _get_user_settings(self) -> (bool, bool):
        if isinstance(self.can_report, bool):
            return self.can_report, self.auto_archived
        return await captcha_task.get_user_settings(self.user.id)

    async def _run_rules(self, *, outgoing: bool = False):
        if self._precondition():
            return
        members = inspect.getmembers(self, inspect.iscoroutinefunction)
        members.sort(key=sort_line_number)
        for name, func in members:
            docs = func.__doc__ or ""
            if (not name.startswith("_") and (
                    "outgoing" in docs and outgoing and await func() or
                    "outgoing" not in docs and await func()
            )):
                break

    @staticmethod
    def _get_rules_priority() -> tuple:
        prio_list = []
        members = inspect.getmembers(Rule, inspect.iscoroutinefunction)
        members.sort(key=sort_line_number)
        for name, func in members:
            if name.startswith("_"):
                continue
            docs = func.__doc__ or ""
            if "no_prio" not in docs:
                if result := re.search(r"name:\s?(.+)", docs):
                    name = result[1]
                prio_list.append(name)
        return tuple(prio_list)

    async def initiative(self) -> bool:
        """outgoing"""
        initiative = setting.get("initiative", False)
        initiative and setting.whitelist.add_id(self.user.id)
        return initiative

    async def flooding(self) -> bool:
        """name: flood"""
        if the_world_eye.triggered:
            _, auto_archived = await self._get_user_settings()
            not auto_archived and await captcha_task.archive(self.user.id)
        return the_world_eye.triggered

    async def disable_pm(self) -> bool:
        disabled = setting.get('disable', False)
        disabled and await the_order.active(self.user.id, "disable_pm_enabled")
        return disabled

    async def chat_history(self) -> bool:
        if (history_count := setting.get("history_count")) is not None:
            count = 0
            async for _ in bot.get_chat_history(self.user.id, offset_id=self.msg.id, offset=-history_count):
                count += 1
            if count >= history_count:
                setting.whitelist.add_id(self.user.id)
                return True
        return False

    async def groups_in_common(self) -> bool:
        from pyrogram.raw.functions.users import GetFullUser
        if (common_groups := setting.get("groups_in_common")) is not None:
            for _ in range(3):
                try:
                    user_full = await bot.invoke(GetFullUser(id=await bot.resolve_peer(self.user.id)))
                    if user_full.common_chats_count >= common_groups:
                        setting.whitelist.add_id(self.user.id)
                        return True
                except FloodWait as e:
                    console.debug(f"Get Common Groups FloodWait: {e.value}s")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    console.error(f"Get Common Groups Error: {e}\n{traceback.format_exc()}")
        return False

    async def premium(self) -> bool:
        if premium := setting.get("premium", False):
            if premium == "only" and not self.msg.from_user.is_premium:
                await the_order.active(self.user.id, "premium_only")
            elif not self.msg.from_user.is_premium:
                return False
            elif premium == "ban":
                await the_order.active(self.user.id, "premium_ban")
        return premium

    # Whitelist / Blacklist
    async def word_filter(self) -> bool:
        """name: whitelist > blacklist"""
        text = self._get_text()
        if text is None:
            return False
        if array := setting.get("whitelist"):
            for word in array.split(","):
                if word not in text:
                    continue
                setting.whitelist.add_id(self.user.id)
                return True
        if array := setting.get("blacklist"):
            for word in array.split(","):
                if word not in text:
                    continue
                reason_code = "blacklist_triggered"
                await the_order.active(self.user.id, reason_code)
                # Collect logs
                can_report, _ = await self._get_user_settings()
                captcha = CaptchaChallenge("", self.user, False, can_report)
                captcha.log_msg(text)
                await captcha.send_log(reason_code)
                return True
        return False

    async def add_captcha(self) -> bool:
        """name: captcha"""
        user_id = self.user.id
        if setting.get_challenge_state(user_id) and not curr_captcha.get(user_id) or not curr_captcha.get(user_id):
            # Put in challenge queue
            await captcha_task.add(user_id, self.msg, *(await self._get_user_settings()))
            return True
        return False

    async def verify_challenge_answer(self) -> bool:
        """no_priority"""
        user_id = self.user.id
        if (captcha := curr_captcha.get(user_id)) and captcha.input:
            text = self._get_text()
            captcha.log_msg(text)
            await captcha.verify(text) and await self.msg.safe_delete()
            del curr_captcha[user_id]
            return True
        return False


# Watches every image captcha result
@listener(is_plugin=False, incoming=True, outgoing=True, privates_only=True)
async def image_captcha_listener(_, msg: Message):
    # Ignores non-private chat, not via bot, username not equal to image bot
    if msg.chat.type != ChatType.PRIVATE or not msg.via_bot or msg.via_bot.username != img_captcha_bot:
        return
    user_id = msg.chat.id
    if (last_captcha := sqlite.get(f"pmcaptcha.challenge.{user_id}")) and not curr_captcha.get(user_id):
        # Resume last captcha challenge
        if last_captcha['type'] != "img":
            return await log("Failed to resume last captcha challenge: "
                             f"Unknown challenge type {last_captcha['type']}")
        await ImageChallenge.resume(user=msg.from_user, state=last_captcha)
    if not curr_captcha.get(user_id):  # User not in verify state
        return
    captcha = curr_captcha[user_id]
    captcha.reset_timer().update_state({"last_active": int(time.time())})
    if "CAPTCHA_SOLVED" in msg.caption:
        await msg.safe_delete()
        await captcha.verify(True)
        del curr_captcha[user_id]
    elif "CAPTCHA_FAILED" in msg.caption:
        if "forced" in msg.caption:
            await captcha.action(False)
            del curr_captcha[user_id]
            return
        if await captcha.verify(False):
            del curr_captcha[user_id]
            await msg.safe_delete()
    elif "CAPTCHA_FALLBACK" in msg.caption:
        await msg.safe_delete()
        # Fallback to selected captcha type
        captcha_type = msg.caption.replace("CAPTCHA_FALLBACK", "").strip()
        console.debug(f"Image bot return fallback request, fallback to {captcha_type}")
        if captcha_type == "math":
            captcha = MathChallenge(msg.from_user, captcha.can_report)
            await captcha.start()
            curr_captcha[user_id] = captcha
            return


@listener(is_plugin=False, outgoing=True, privates_only=True)
async def initiative_listener(_, msg: Message):
    rules = Rule(msg.from_user, msg)
    await rules._run_rules(outgoing=True)


@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=True, privates_only=True)
async def chat_listener(_, msg: Message):
    rules = Rule(msg.from_user, msg)
    await rules._run_rules()


@listener(is_plugin=True, outgoing=True,
          command=cmd_name, parameters=f"<{lang('vocab_cmd')}> [{lang('cmd_param')}]",
          need_admin=True,
          description=f"{lang('plugin_desc')}\n{(lang('check_usage') % code(f',{cmd_name} h'))}")
async def cmd_entry(_, msg: Message):
    result, err_code, extra = await Command(msg.from_user, msg)._run_command()
    if not result:
        if err_code == "NOT_FOUND":
            return await msg.edit_text(
                f"{lang('cmd_not_found')}: {code(extra)}\n" + lang("check_usage") % code(f',{cmd_name} h'),
                parse_mode=ParseMode.HTML)
        elif err_code == "INVALID_PARAM":
            return await msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)


async def resume_states():
    console.debug("Resuming Captcha States")
    for key, value in sqlite.items():  # type: str, dict
        if key.startswith("pmcaptcha.challenge"):
            user_id = int(key.split(".")[2])
            if user_id not in curr_captcha and (challenge := captcha_challenges.get(value.get('type'))):
                # Resume challenge state
                try:
                    user = await bot.get_users(user_id)
                    await challenge.resume(user=user, state=value)
                except Exception as e:
                    console.error(f"Error occurred when resuming captcha state: {e}\n{traceback.format_exc()}")
    console.debug("Captcha State Resume Completed")


if __name__ == "plugins.pmcaptcha":
    # Force disabled for old PMCaptcha
    globals().get("SubCommand") and exit(0)
    # Flood Username confirm
    user_want_set_flood_username = None
    console = logs.getChild(cmd_name)
    captcha_challenges = {
        "math": MathChallenge,
        "img": ImageChallenge
    }


    def _cancel_task(task: asyncio.Task):
        task and task.cancel()


    gbl = globals()
    for k, v in {
        "curr_captcha": {},
        "setting": Setting("pmcaptcha"),
    }.items():
        if k in gbl:
            del gbl[k]
        gbl[k] = v
    curr_captcha = globals().get("curr_captcha", {})
    if setting := globals().get("setting"):
        del setting
    # noinspection PyRedeclaration
    setting = Setting("pmcaptcha")
    if logging := gbl.get("logging"):
        _cancel_task(logging.task)
        del logging
    # noinspection PyRedeclaration
    logging = Log()
    if the_world_eye := gbl.get("the_world_eye"):
        _cancel_task(the_world_eye.watcher)
        del the_world_eye
    gbl["the_world_eye"] = TheWorldEye()
    if the_order := gbl.get("the_order"):
        _cancel_task(the_order.task)
        del the_order
    gbl["the_order"] = TheOrder()
    if captcha_task := gbl.get("captcha_task"):
        _cancel_task(captcha_task.task)
        del captcha_task
    gbl["captcha_task"] = TheOrder()
    if not (resume_task := globals().get("resume_task")) or resume_task.done():
        resume_task = asyncio.create_task(resume_states())
