# pyright: basic

import contextlib
import copy
import os
import random
from dataclasses import dataclass
from typing import (Any, Awaitable, Callable, Dict, List, NamedTuple, Optional,
                    Tuple)

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
INTERACTIVE_CONFIG_PATH = r"data/pixiv_interactive.yml"
PLUGIN_NAME = "pixiv"
HELP_URL = r"https://www.huajitech.net/pagermaid-pixiv-plugin-help/"
_config: Dict[str, Any] = {}
_interactive_config: Dict[str, Any] = {}
pixiv_api: Optional[AppPixivAPI] = None

with contextlib.suppress(Exception):
    with open(CONFIG_PATH, mode="r") as config_file:
        _config = yaml.safe_load(config_file)
    with open(INTERACTIVE_CONFIG_PATH, mode="r") as interactive_config_file:
        _interactive_config = yaml.safe_load(interactive_config_file)


def str_to_list(value: Optional[str]) -> List[str]:
    return value.split(",") if value else []


def reversed_dict(d: Dict[Any, Any]) -> Dict[Any, Any]:
    return {v: k for k, v in d.items()}


root_command = lambda: alias_command(PLUGIN_NAME)


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


class InteractiveConfig:
    aliases: Dict[str, str] = _interactive_config.get("aliases") or {}
    reversed_aliases: Dict[str, str] = reversed_dict(aliases)

    @staticmethod
    def apply() -> None:
        _interactive_config["aliases"] = InteractiveConfig.aliases
        with open(INTERACTIVE_CONFIG_PATH, mode="w") as interactive_config_file:
            yaml.safe_dump(_interactive_config, interactive_config_file)


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


subcommands: Dict[str, HandlerInfo] = {}


def subcommand(
    com: str, description: str, usage: str = ""
) -> Callable[[Handler], Handler]:
    def decorator(func: Handler):
        subcommands[com] = HandlerInfo(func, usage, description)
        return func

    return decorator


def subcommand_alias(com: str) -> str:
    return InteractiveConfig.aliases.get(com) or com


def subcommand_from_alias(com: str) -> str:
    return InteractiveConfig.reversed_aliases.get(com) or com


def generate_usage() -> str:
    return "\n".join(
        f"`{PREFIX}{root_command()} {subcommand_alias(com)} {info.usage}`\n{info.description}"
        for com, info in subcommands.items()
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
        and (needed.intersection(illust.tags) if needed else True)
    ]


def illust_filter_by_tags(illusts: List[Illust], keywords: str) -> List[Illust]:
    needed = set(keywords.split())
    return [
        illust
        for illust in illusts
        if (needed.intersection(illust.tags) if needed else True)
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
        await message.edit(f"没有配置 Token 诶，要不发送 `{PREFIX}{root_command()} help` 看看帮助？")
    else:
        error = f"{type(ex).__name__}: {ex}"
        await message.edit("呜呜呜 ~ 出错了:\n" + error)
        logs.error(message)


@subcommand(
    "search", "通过关键词（可传入多个）搜索 Pixiv 相关插图，并随机选取一张图发送", "<关键词> ... [R-18 / R-18G]"
)
async def search(_: Client, message: Message) -> None:
    await message.edit("正在发送中，请耐心等待www")
    keywords = message.arguments
    if not keywords:
        await message.edit("没有关键词我怎么搜索？")
        return
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


@subcommand(
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


@subcommand("help", "获取插件帮助")
async def help_cmd(_: Client, message: Message) -> None:
    await message.edit(
        f"{PLUGIN_NAME} 插件使用帮助: {HELP_URL}", disable_web_page_preview=True
    )


@subcommand("alias", "重定向子命令", "{del <子指令>|list|set <子指令> <重定向子指令>}")
async def alias_cmd(_: Client, message: Message) -> None:
    if not message.arguments:
        await message.edit(f"缺少参数了，要不发送 `{PREFIX}help {root_command()}` 看看帮助？")
        return
    operation = message.parameter[0]
    if operation == "del":
        if len(message.parameter) != 2:
            await message.edit(f"参数错误。要不发送 `{PREFIX}help {root_command()}` 看看帮助？")
            return
        com = message.parameter[1]
        if com not in subcommands:
            await message.edit("未知子指令。")
        elif com not in InteractiveConfig.aliases:
            await message.edit("该子指令未重定向。")
        else:
            del InteractiveConfig.aliases[com]
            InteractiveConfig.apply()
            await message.edit(f"已删除 {com} 重定向。正在重新加载 PagerMaid-Pyro。")
            await reload_all()
    elif operation == "list":
        await message.edit(str(InteractiveConfig.aliases))
    elif operation == "set":
        if len(message.parameter) != 3:
            await message.edit(f"参数错误。要不发送 `{PREFIX}help {root_command()}` 看看帮助？")
            return
        com, alias = message.parameter[1:]
        if com not in subcommands:
            await message.edit("未知子指令。")
        if alias in InteractiveConfig.reversed_aliases or alias in subcommands:
            await message.edit("重定向冲突。")
        else:
            InteractiveConfig.aliases[com] = alias
            InteractiveConfig.apply()
            await message.edit(f"已将 {com} 重定向至 {alias}。正在重新加载 PagerMaid-Pyro。")
            await reload_all()
    else:
        await message.edit(f"参数错误。要不发送 `{PREFIX}help {root_command()}` 看看帮助？")


@listener(
    command=PLUGIN_NAME,
    description=generate_usage(),
    parameters=f"{{{'|'.join(subcommands.keys())}}}",
)
async def message_handler(client: Client, message: Message) -> None:
    try:
        com: str = message.parameter[0]
    except IndexError:
        com = ""
    info = subcommands.get(subcommand_from_alias(com))
    if not info:
        await message.edit(f"我看不懂你发了什么诶。要不发送 `{PREFIX}help {root_command()}` 看看？")
        return
    new_message = copy.copy(message)
    new_message.arguments = new_message.arguments[len(com) + 1 :]
    new_message.parameter = new_message.parameter[1:]
    new_message.bind(client)
    try:
        return await info.func(client, new_message)
    except Exception as ex:
        await report_error(message, ex)
