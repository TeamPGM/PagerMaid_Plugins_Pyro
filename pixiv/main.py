# pyright: basic

import contextlib
import copy
import os
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, NamedTuple, Optional, Tuple

import yaml
from pagermaid import logs
from pagermaid.common.reload import reload_all
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.services import scheduler
from pagermaid.utils import alias_command, pip_install


def install_dependencies() -> None:
    pip_install("pixivpy-async", alias="pixivpy_async")
    pip_install("aiohttp-socks", alias="aiohttp_socks")


install_dependencies()

from pixivpy_async import AppPixivAPI
from pixivpy_async.error import NoTokenError

PREFIX = ","
CONFIG_PATH = r"data/pixiv.yml"
COMMAND_CONFIG_PATH = r"data/pixiv_command.yml"
PLUGIN_NAME = "pixiv"
HELP_URL = r"https://www.huajitech.net/pagermaid-pixiv-plugin-help/"
_config: Dict[str, Any] = {}
pixiv_api: Optional[AppPixivAPI] = None

with contextlib.suppress(Exception):
    with open(CONFIG_PATH, mode="r") as config_file:
        _config = yaml.safe_load(config_file)


def str_to_list(value: Optional[str]) -> List[str]:
    return value.split(",") if value else []


def reversed_dict(d: Dict[Any, Any]) -> Dict[Any, Any]:
    return {v: k for k, v in d.items()}


root_command = alias_command(PLUGIN_NAME)


Handler = Callable[[Client, Message], Awaitable[None]]


class PluginConfig:
    proxy: Optional[str] = os.environ.get("PLUGIN_PIXIV_PROXY") or _config.get("proxy")

    refresh_token: Optional[str] = os.environ.get(
        "PLUGIN_PIXIV_REFRESH_TOKEN"
    ) or _config.get("refresh_token")

    message_elements: List[str] = (
        str_to_list(os.environ.get("PLUGIN_PIXIV_MESSAGE_ELEMENTS"))
        or _config.get("message_elements")
        or [
            "image",
            "id",
            "title",
            "caption",
            "tags",
            "resolution",
            "upload_time",
            "author",
        ]
    )


@dataclass
class Illust:
    id: int
    title: str
    caption: str
    tags: List[str]
    image_urls: Dict[str, str]
    resolution: Tuple[int, int]
    upload_time: str
    author_id: str
    author_account: str
    author_name: str

    @staticmethod
    def from_response(res: Any) -> "Illust":
        return Illust(
            res.id,
            res.title,
            res.caption,
            [tag.translated_name or tag.name for tag in res.tags],
            dict(res.image_urls),
            (res.width, res.height),
            res.create_date,
            res.user.id,
            res.user.account,
            res.user.name,
        )


class HandlerInfo(NamedTuple):
    func: Handler
    usage: str
    description: str


class CommandManager:
    _commands: Dict[str, HandlerInfo]
    _aliases: Dict[str, str]
    _reversed_aliases: Dict[str, str]
    _config_builder: Callable[[Dict[Any, Any]], None]

    def __init__(
        self, config: Dict[Any, Any], config_builder: Callable[[Dict[Any, Any]], None]
    ) -> None:
        self._commands = {}
        self._aliases = {}
        self._reversed_aliases = {}
        self._config_builder = config_builder
        self._read_config(config)

    def _read_config(self, config: Dict[Any, Any]) -> None:
        self._aliases = config.get("aliases") or {}
        self._reversed_aliases = reversed_dict(self._aliases)

    def _serialize(self) -> Dict[Any, Any]:
        return {"aliases": self._aliases}

    def register(self, command: str, handler: HandlerInfo):
        assert command not in self._commands, f"无法找到 {command} 指令。"
        self._commands[command] = handler

    def set_alias(self, command: str, alias: str) -> None:
        assert command in self._commands, f"无法找到 {command} 指令。"
        assert (
            alias not in self._commands and alias not in self._aliases.values()
        ), "重定向指令冲突。"
        self._aliases[command] = alias
        self.update_config()

    def delete_alias(self, command: str) -> None:
        assert command in self._aliases, f"{command} 指令未设置重定向。"
        del self._aliases[command]
        self.update_config()

    def get_aliases(self) -> Dict[str, str]:
        return dict(self._aliases)

    def get_available_commands(self, alias_only: bool = True) -> Dict[str, HandlerInfo]:
        aliases = {
            alias: self._commands[command] for command, alias in self._aliases.items()
        }
        return (
            {
                command: handler
                for command, handler in self._commands.items()
                if command not in self._aliases
            }
            if alias_only
            else dict(self._commands)
        ) | aliases

    def alias_of(self, command: str) -> str:
        alias = self._aliases.get(command) or (
            command if command in self._commands else None
        )
        assert alias, f"{command} 指令未设置重定向。"
        return alias

    def command_of(self, alias: str) -> str:
        command = self._reversed_aliases.get(alias)
        assert command, f"不存在 {alias} 重定向指令。"
        return command

    def update_config(self):
        self._config_builder(self._serialize())

    def subcommand(
        self, command: str, description: str, usage: str = ""
    ) -> Callable[[Handler], Handler]:
        def decorator(func: Handler):
            self.register(command, HandlerInfo(func, usage, description))
            return func

        return decorator


cmdman = CommandManager(
    config=yaml.safe_load(open(COMMAND_CONFIG_PATH, mode="r"))
    if os.path.exists(COMMAND_CONFIG_PATH)
    else {},
    config_builder=lambda d: yaml.safe_dump(d, open(COMMAND_CONFIG_PATH, mode="w")),
)


def generate_usage() -> str:
    return "\n".join(
        f"`{PREFIX}{root_command} {command} {info.usage}`\n{info.description}"
        for command, info in cmdman.get_available_commands(True).items()
    )


def illust_sensitive_content_filter(
    illusts: List[Illust], keywords: str
) -> List[Illust]:
    excluded = ["R-18", "R-18G"]
    needed = set(keywords.split()).intersection(excluded)
    excluded = set(excluded).difference(needed)

    return [
        illust
        for illust in illusts
        if not excluded.intersection(illust.tags)
        and (not needed or len(needed.intersection(illust.tags)) == len(needed))
    ]


def illust_filter_by_tags(illusts: List[Illust], keywords: str) -> List[Illust]:
    needed = set(keywords.split())
    return [
        illust
        for illust in illusts
        if not needed or len(needed.intersection(illust.tags)) == len(needed)
    ]


async def get_api() -> AppPixivAPI:
    global pixiv_api
    if pixiv_api:
        return pixiv_api
    pixiv_api = AppPixivAPI(proxy=PluginConfig.proxy)

    if PluginConfig.refresh_token is None:
        logs.info(f"未设置 {PLUGIN_NAME} 插件登录所需的 refresh_token，将以游客身份工作。")
    else:
        await pixiv_api.login(refresh_token=PluginConfig.refresh_token)

    return pixiv_api


@scheduler.scheduled_job("interval", minutes=30, id="pixiv_fetch_token")
async def fetch_token() -> None:
    if not PluginConfig.refresh_token:
        return
    api = await get_api()
    if api:
        await api.login(refresh_token=PluginConfig.refresh_token)


async def send_illust(message: Message, illust: Illust) -> None:
    elements = PluginConfig.message_elements

    caption = (
        (f"**{illust.title}**\n" if "title" in elements else "")
        + (f"__{illust.caption}__\n\n" if "caption" in elements else "")
        + (
            f'ID: <a href="https://www.pixiv.net/artworks/{illust.id}">{illust.id}</a>\n'
            if "id" in elements
            else ""
        )
        + (
            f'作者: <a href="https://www.pixiv.net/users/{illust.author_id}">{illust.author_name}</a> '
            f"({illust.author_account})\n"
            if "author" in elements
            else ""
        )
        + (f'标签: {", ".join(illust.tags)}\n' if "tags" in elements else "")
        + (
            f"分辨率: {illust.resolution[0]}x{illust.resolution[1]}\n"
            if "resolution" in elements
            else ""
        )
        + (f"上传时间: {illust.upload_time}" if "upload_time" in elements else "")
    )

    if "image" in elements:
        await message.reply_photo(
            illust.image_urls["large"],
            caption=caption,
            quote=False,
            reply_to_message_id=message.reply_to_message_id
            or message.reply_to_top_message_id,
        )
    else:
        await message.reply_text(
            caption,
            reply_to_message_id=message.reply_to_message_id
            or message.reply_to_top_message_id,
        )


async def report_error(message: Message, ex: Exception) -> None:
    if isinstance(ex, NoTokenError):
        await message.edit(f"没有配置 Token 诶，要不发送 `{PREFIX}{root_command} help` 看看帮助？")
    else:
        error = f"{type(ex).__name__}: {ex}"
        await message.edit("呜呜呜 ~ 出错了:\n" + error)
        logs.error(message)


@cmdman.subcommand(
    "search", "通过关键词（可传入多个）搜索 Pixiv 相关插图，并随机选取一张图发送", "<关键词> ... [R-18 / R-18G]"
)
async def search(_: Client, message: Message) -> None:
    keywords = message.arguments
    if not keywords:
        await message.edit("没有关键词我怎么搜索？")
        return
    await message.edit("正在发送中，请耐心等待www")
    api = await get_api()
    response = await api.search_illust(
        keywords, search_target="partial_match_for_tags"
    )  # partial match
    illusts = [Illust.from_response(illust) for illust in response.illusts]
    filtered_illusts = illust_sensitive_content_filter(illusts, keywords)
    if not filtered_illusts:
        await message.edit("呜呜呜 ~ 没有找到相应结果。")
        return
    illust = random.choice(filtered_illusts)
    await send_illust(message, illust)
    await message.safe_delete()


@cmdman.subcommand(
    "recommend",
    "获取 Pixiv 每日推荐，可传入多个 Tag 参数筛选目标结果，并随机选取一张图发送",
    "[Tag] ... [R-18 / R-18G]",
)
async def recommend(_: Client, message: Message) -> None:
    await message.edit("正在发送中，请耐心等待www")
    keywords = message.arguments
    api = await get_api()
    response: Any = await api.illust_recommended()
    illusts = [Illust.from_response(illust) for illust in response.illusts]
    filtered_illusts = illust_filter_by_tags(
        illust_sensitive_content_filter(illusts, keywords), keywords
    )
    if not filtered_illusts:
        await message.edit("呜呜呜 ~ 没有找到相应结果。")
        return
    illust = random.choice(filtered_illusts)
    await send_illust(message, illust)
    await message.safe_delete()


@cmdman.subcommand("help", "获取插件帮助")
async def help_cmd(_: Client, message: Message) -> None:
    await message.edit(
        f"{PLUGIN_NAME} 插件使用帮助: {HELP_URL}", disable_web_page_preview=True
    )


@cmdman.subcommand("id", "根据 ID 获取 Pixiv 相关插图", "<ID>")
async def id_cmd(_: Client, message: Message) -> None:
    try:
        id_ = int(message.arguments)
    except ValueError:
        await message.edit("你输入的不是正确的 ID 诶www")
        return
    await message.edit("正在发送中，请耐心等待www")
    api = await get_api()
    response = await api.illust_detail(id_)
    if not (response := response.get("illust")):
        await message.edit("呜呜呜 ~ 没有找到相应结果。")
        return
    illust = Illust.from_response(response)
    await send_illust(message, illust)
    await message.safe_delete()


@cmdman.subcommand("alias", "重定向子命令", "{del <子指令>|list|set <子指令> <重定向子指令>}")
async def alias_cmd(_: Client, message: Message) -> None:
    if not message.arguments:
        await message.edit(f"缺少参数了，要不发送 `{PREFIX}help {root_command}` 看看帮助？")
        return
    operation = message.parameter[0]
    if operation == "del":
        if len(message.parameter) != 2:
            await message.edit(f"参数错误。要不发送 `{PREFIX}help {root_command}` 看看帮助？")
            return
        command = message.parameter[1]
        cmdman.delete_alias(command)
        await message.edit(f"已删除 `{command}` 重定向。正在重新加载 PagerMaid-Pyro。")
        await reload_all()
    elif operation == "list":
        await message.edit(str(cmdman.get_aliases()))
    elif operation == "set":
        if len(message.parameter) != 3:
            await message.edit(f"参数错误。要不发送 `{PREFIX}help {root_command}` 看看帮助？")
            return
        command, alias = message.parameter[1:]
        cmdman.set_alias(command, alias)
        await message.edit(f"已重定向 `{command}` 至 `{alias}`。正在重新加载 PagerMaid-Pyro。")
        await reload_all()
    else:
        await message.edit(f"参数错误。要不发送 `{PREFIX}help {root_command}` 看看帮助？")


@listener(
    command=PLUGIN_NAME,
    description=generate_usage(),
    parameters=f"{{{'|'.join(cmdman.get_available_commands(True).keys())}}}",
)
async def message_handler(client: Client, message: Message) -> None:
    try:
        command = message.parameter[0]
    except IndexError:
        command = ""
    commands = cmdman.get_available_commands(False)
    info = commands.get(command)
    if not info:
        await message.edit(f"我看不懂你发了什么诶。要不发送 `{PREFIX}help {root_command}` 看看？")
        return
    new_message = copy.copy(message)
    new_message.arguments = new_message.arguments[len(command) + 1 :]
    new_message.parameter = new_message.parameter[1:]
    new_message.bind(client)
    try:
        return await info.func(client, new_message)
    except Exception as ex:
        await report_error(message, ex)
