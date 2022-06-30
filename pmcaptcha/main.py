"""
PMCaptcha - A PagerMaid-Pyro plugin by cloudreflection
v2 rewritten by Sam
https://t.me/cloudreflection_channel/268
ver 2022/06/30
"""

import re
import html
import random
import asyncio
import inspect
from dataclasses import dataclass
from typing import Optional, Callable, Union, Dict

from pyrogram.errors import FloodWait
from pyrogram.enums.chat_type import ChatType
from pyrogram.enums.parse_mode import ParseMode
from pyrogram.raw.functions.account import UpdateNotifySettings
from pyrogram.raw.functions.messages import DeleteHistory, MarkDialogUnread
from pyrogram.raw.types import InputNotifyPeer, InputPeerNotifySettings, InputDialogPeer

from pagermaid import log, bot
from pagermaid.config import Config
from pagermaid.sub_utils import Sub
from pagermaid.utils import Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite

cmd_name = "pmcaptcha"
version = "2.0"

# Log Collect
log_collect_bot = "CloudreflectionPmcaptchabot"


def lang(lang_id: str) -> str:
    return lang_dict.get(lang_id)[1 if Config.LANGUAGE.startswith("zh") else 0]


def code(text: str) -> str:
    return f"<code>{text}</code>"


def italic(text: str) -> str:
    return f"<i>{text}</i>"


def bold(text: str) -> str:
    return f"<b>{text}</b>"


def gen_link(text: str, url: str) -> str:
    return f"<a href=\"{url}\">{text}</a>"


async def punishment_worker(q: asyncio.Queue):
    data = None
    flood_text = "[PMCaptcha] Flood Triggered: %is, command: %s, target: %s"
    while True:
        data = data or sqlite.get("pmcaptcha", {})
        target = None
        try:
            (target,) = await q.get()
            action = data.get("action", "archive")
            if action in ("ban", "delete", "archive"):
                for _ in range(3):
                    try:
                        await bot.block_user(user_id=target)
                        break
                    except FloodWait as e:
                        await log(flood_text % (e.value, "Block", target))
                        await asyncio.sleep(e.value)
                if action == "delete":
                    try:
                        await bot.invoke(DeleteHistory(max_id=0, peer=await bot.resolve_peer(target)))
                        break
                    except FloodWait as e:
                        await log(flood_text % (e.value, "Delete Message", target))
                        await asyncio.sleep(e.value)
                elif action == "archive":
                    try:
                        await bot.archive_chats(chat_ids=target)
                        break
                    except FloodWait as e:
                        await log(flood_text % (e.value, "Archive", target))
                        await asyncio.sleep(e.value)
            data['banned'] = data.get('banned', 0) + 1
            sqlite['pmcaptcha'] = data
            chat_link = gen_link(str(target), f"tg://openmessage?user_id={target}")
            await log(("[PMCaptcha - The Order] "
                       f"{lang('verify_log_punished') % (chat_link, lang(f'action_{action}'))} (Punishment)"))
        except Exception as e:  # noqa
            import traceback
            await log(f"[PMCaptcha] Error occurred when punishing user: {e}\n{traceback.format_exc()}")
        finally:
            target and q.task_done()


async def log_collect(msg: Message):
    try:
        await bot.unblock_user(log_collect_bot)
    except:  # noqa
        pass
    log_collect_template = f"UID: %s\n{code('%s')}"
    user_id = code(f"{msg.from_user.first_name} {msg.chat.id}")
    if username := msg.from_user.username:
        user_id += f" (@{username})"
    try:
        await bot.send_message(log_collect_bot, log_collect_template % (user_id, html.escape(msg.text)),
                               parse_mode=ParseMode.HTML, disable_web_page_preview=True, disable_notification=True)
    except:  # noqa
        pass
    await log(f"[PMCaptcha] Log collected from user {msg.chat.id}")


whitelist = Sub("pmcaptcha.success")
punishment_queue = asyncio.Queue()
timed_captcha_challenge_task: Dict[int, asyncio.Task] = {}
captcha_challenge_msg: Dict[int, int] = {}
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

    # region Plugin
    "plugin_desc": [
        "Captcha for PM\nPlease use %s to see available commands.",
        f"私聊人机验证插件\n请使用 %s 查看可用命令"
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
    "disable_pm_set": [
        f"Private chat has bee set to {bold('%s')}.",
        f"已设置私聊为{bold('%s')}"
    ],
    "disable_pm_enabled": [
        "Owner has private chat disabled.",
        "对方已禁止私聊。"
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
    "premium_only": [
        "Owner only allows Telegram Premium users to private chat.",
        "对方只允许 Telegram Premium 用户私聊"
    ],
    "premium_ban": [
        "Owner bans Telegram Premium users from private chat.",
        "对方禁止 Telegram Premium 用户私聊"
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
    "verify_blocked": [
        "You were blocked.",
        "您已被封禁"
    ],
    "verify_log_punished": [
        "User %i has been %s.",
        "已对用户 %i 执行`%s`操作"
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
    ]
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
        subcmd_name = "" if cmd_name == subcmd_name else self._get_cmd_with_param(subcmd_name)
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
        if self.msg.chat.type != ChatType.PRIVATE:
            await self.msg.edit(lang('tip_run_in_pm'), parse_mode=ParseMode.HTML)
        else:
            await self.msg.edit(lang(f'verify_{"" if whitelist.check_id(self.msg.chat.id) else "un"}verified'))
        await asyncio.sleep(5)
        await self.msg.safe_delete()

    async def help(self, command: Optional[str] = None):
        """显示指令帮助信息

        :param opt command: 命令名称
        :alias: h
        """
        help_msg = [f"{code('PMCaptcha')} {lang('cmd_list')} (v{version}):", ""]
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
                        + f"\n> {re.search(r'(.+)', func.__doc__)[1].strip()}\n"
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
            _id = _id or self.msg.chat.id
            verified = whitelist.check_id(int(_id))
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
            whitelist.add_id(int(_id))
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
            _id = _id or self.msg.chat.id
            text = lang('remove_verify_log_success' if whitelist.del_id(int(_id)) else 'verify_log_not_found')
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
                lang('tip_edit') % html.escape(f",{cmd_name} wel <{lang('vocab_msg')}>")
            )), parse_mode=ParseMode.HTML)
        message = " ".join(message)
        if message == "-clear":
            if data.get("welcome"):
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
                lang('tip_edit') % html.escape(f",{cmd_name} wl <{lang('vocab_array')}>")
            )), parse_mode=ParseMode.HTML)
        if array == "-clear":
            if data.get("whitelist"):
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
                lang('tip_edit') % html.escape(f",{cmd_name} bl <{lang('vocab_array')}>")
            )), parse_mode=ParseMode.HTML)
        if array == "-clear":
            if data.get("blacklist"):
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
                lang('tip_edit') % html.escape(f",{cmd_name} wait <{lang('vocab_int')}>")
            )), parse_mode=ParseMode.HTML)
        if seconds == "off":
            if data.get("timeout"):
                data["timeout"] = 0
                sqlite["pmcaptcha"] = data
            await self.msg.edit(lang('timeout_off'), parse_mode=ParseMode.HTML)
            return
        try:
            data["timeout"] = int(seconds)
        except ValueError:
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
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
                lang('disable_pm_curr_rule') % lang('enabled' if data.get('disable') else 'disabled'),
                "",
                lang('tip_edit') % html.escape(f",{cmd_name} disablepm <{lang('vocab_bool')}>")
            )), parse_mode=ParseMode.HTML)
        toggle = toggle.lower()[0]
        if toggle not in ("y", "n", "t", "f", "1", "0"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        data["disable"] = toggle in ("y", "t", "1")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('disable_pm_set') % lang("enabled" if data["disable"] else "disabled"),
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
                lang('tip_edit') % html.escape(f",{cmd_name} act <{lang('action_param_name')}>")
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
                lang('tip_edit') % html.escape(f",{cmd_name} prem <{lang('action_param_name')}>")
            )), parse_mode=ParseMode.HTML)
        if action not in ("allow", "ban", "only", "none"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        if action == "none":
            del data["premium"]
        else:
            data["premium"] = action
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang(f'premium_set_{action}'), parse_mode=ParseMode.HTML)

    async def silent(self, toggle: Optional[str] = None):
        """减少信息发送，默认为 no
        开启后，将不会发送封禁提示 (不影响 log 发送)

        :param toggle: 开关 (yes / no)
        :alias: quiet
        """
        data = sqlite.get("pmcaptcha", {})
        if not toggle:
            return await self.msg.edit_text("\n".join((
                lang('silent_curr_rule') % lang('enabled' if data.get('silent', False) else 'disabled'),
                "",
                lang('tip_edit') % html.escape(f",{cmd_name} silent <{lang('vocab_bool')}>")
            )), parse_mode=ParseMode.HTML)
        toggle = toggle.lower()[0]
        if toggle not in ("y", "n", "t", "f", "1", "0"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        data["silent"] = toggle in ("y", "t", "1")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('silent_set') % lang("enabled" if data["silent"] else "disabled"),
                            parse_mode=ParseMode.HTML)

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
                lang('tip_edit') % html.escape(f",{cmd_name} collect <{lang('vocab_bool')}>")
            )), parse_mode=ParseMode.HTML)
        toggle = toggle.lower()[0]
        if toggle not in ("y", "n", "t", "f", "1", "0"):
            return await self.msg.edit(lang('invalid_param'), parse_mode=ParseMode.HTML)
        data["collect"] = toggle in ("y", "t", "1")
        sqlite["pmcaptcha"] = data
        await self.msg.edit(lang('collect_logs_set') % lang("enabled" if data["collect"] else "disabled"))


@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=True, privates_only=True)
async def process_captcha(_, msg: Message):
    async def punish(reason_code: str):
        try:
            not data.get("silent", False) and await msg.reply("\n".join((
                f"{lang_dict[reason_code][1]} ({lang_dict[reason_code][0]})",
                "",
                f"{lang_dict['verify_blocked'][1]} ({lang_dict['verify_blocked'][0]})",
            )))
        except FloodWait:
            pass  # Skip waiting
        return punishment_queue.put_nowait((msg.chat.id,))

    async def _captcha_failed(wait: int):
        await asyncio.sleep(wait)
        if sqlite.get(f"pmcaptcha.{user_id}"):
            del sqlite[f'pmcaptcha.{user_id}']
        await punish("verify_failed")
        if _msg_id := captcha_challenge_msg.get(user_id):
            try:
                await bot.delete_messages(msg.chat.id, _msg_id)
            except:  # noqa
                pass
            del captcha_challenge_msg[user_id]
        # Collect logs
        data.get("collect", False) and await log_collect(msg)

    # 忽略联系人、认证消息、机器人消息
    if msg.from_user.is_contact or msg.from_user.is_verified or msg.chat.type == ChatType.BOT:
        return
    user_id = msg.chat.id
    data = sqlite.get("pmcaptcha", {})
    # Disable PM
    if data.get('disable', False) and not whitelist.check_id(user_id):
        return await punish("disable_pm_enabled")
    # Premium
    elif premium := data.get("premium"):
        if premium == "only" and not msg.from_user.is_premium:
            return await punish("premium_only")
        elif not msg.from_user.is_premium:
            pass
        elif premium == "ban":
            return await punish("premium_ban")
        elif premium == "allow":
            return
    # Black / White list & Captcha
    if not whitelist.check_id(user_id) and not sqlite.get(f"pmcaptcha.{user_id}"):
        if data.get("whitelist") and msg.text is not None:  # 白名单
            for i in data.get("whitelist", "").split(","):
                if i in msg.text:
                    return whitelist.add_id(user_id)
        if data.get("blacklist") and msg.text is not None:  # 黑名单
            for i in data.get("blacklist", "").split(","):
                if i in msg.text:
                    await punish("blacklist_triggered")
                    # Collect logs
                    return data.get("collect", False) and await log_collect(msg)
        try:
            await bot.invoke(UpdateNotifySettings(
                peer=InputNotifyPeer(peer=await bot.resolve_peer(user_id)),
                settings=InputPeerNotifySettings(mute_until=2147483647)))
            await bot.archive_chats(user_id)
        except:  # noqa
            pass
        # Send captcha
        key1 = random.randint(1, 10)
        key2 = random.randint(1, 10)
        timeout = data.get("timeout", 30)
        extra_note = timeout > 0 and "\n" + "\n".join((
            lang_dict['verify_challenge_timed'][1] % timeout,
            lang_dict['verify_challenge_timed'][0] % timeout
        )) or ""
        captcha_msg = None
        for _ in range(3):
            try:
                captcha_msg = await msg.reply("\n".join((
                    lang_dict['verify_challenge'][1],
                    lang_dict['verify_challenge'][0],
                    "",
                    f"{key1} + {key2} = ?",
                    extra_note
                )))
                captcha_challenge_msg[user_id] = captcha_msg.id
                break
            except FloodWait as e:
                await asyncio.sleep(e.value)
                continue
            except:  # noqa
                pass
        if not captcha_msg:
            await log(f"[PMCaptcha] Failed to send captcha challenge to {user_id}")
            return
        sqlite[f'pmcaptcha.{user_id}'] = str(key1 + key2)
        if timeout > 0:
            timed_captcha_challenge_task[user_id] = asyncio.create_task(_captcha_failed(timeout))
    # Verify Captcha Answer
    elif sqlite.get(f"pmcaptcha.{user_id}"):
        correct_answer = int(sqlite[f'pmcaptcha.{user_id}'])
        del sqlite[f'pmcaptcha.{user_id}']
        if task := timed_captcha_challenge_task.get(user_id):
            task.cancel()
            del timed_captcha_challenge_task[user_id], task
        try:
            answer = int(msg.text.strip())
        except ValueError:
            return await punish("verify_failed")
        if answer == correct_answer:
            whitelist.add_id(user_id)
            data['pass'] = data.get('pass', 0) + 1
            sqlite['pmcaptcha'] = data
            try:
                await bot.unarchive_chats(chat_ids=user_id)
                await bot.invoke(
                    UpdateNotifySettings(peer=InputNotifyPeer(peer=await bot.resolve_peer(user_id)),
                                         settings=InputPeerNotifySettings(show_previews=True)))
                await msg.safe_delete()
            except:  # noqa
                pass
            success_msg = data.get("welcome") or "\n".join((
                lang_dict['verify_passed'][1],
                lang_dict['verify_passed'][0],
            ))
            if msg_id := captcha_challenge_msg.get(user_id):
                await bot.edit_message_text(msg.chat.id, msg_id, success_msg)
                del captcha_challenge_msg[user_id]
            else:
                captcha_msg = await msg.reply(success_msg)
                msg_id = captcha_msg.id
            await asyncio.sleep(3)
            try:
                await bot.delete_messages(user_id, msg_id)
                await bot.invoke(MarkDialogUnread(peer=InputDialogPeer(peer=await bot.resolve_peer(user_id)),
                                                  unread=True))
            except:  # noqa
                pass
        else:
            if msg_id := captcha_challenge_msg.get(user_id):
                try:
                    await bot.delete_messages(msg.chat.id, msg_id)
                except:  # noqa
                    pass
                del captcha_challenge_msg[user_id]
            await punish("verify_failed")


@listener(is_plugin=True, outgoing=True,
          command=cmd_name, parameters=f"<{lang('vocab_cmd')}> [{lang('cmd_param')}]",
          need_admin=True,
          description=lang("plugin_desc") % code(f',{cmd_name} h'))
async def cmd_entry(_, msg: Message):
    cmd = len(msg.parameter) > 0 and msg.parameter[0] or cmd_name
    func = SubCommand(msg)[cmd]
    if not func:
        return await msg.edit_text(f"{lang('cmd_not_found')}: {code(cmd)}", parse_mode=ParseMode.HTML)
    args_len = -1 if inspect.getfullargspec(func).varargs else len(inspect.getfullargspec(func).args)
    await func(*(len(msg.parameter) > 1 and msg.parameter[1:args_len] or [None] * (args_len - 1)))
