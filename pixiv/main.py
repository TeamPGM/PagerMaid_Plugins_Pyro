# pyright: basic

import copy
import os
import random
from dataclasses import dataclass
from typing import (Any, Awaitable, Callable, Dict, List, NamedTuple, Optional,
                    Tuple)

import yaml

from pagermaid import logs
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.utils import pip_install


def install_dependencies() -> None:
    pip_install("pixivpy-async")
    pip_install("aiohttp_socks")


install_dependencies()

from pixivpy_async import AppPixivAPI

VERSION = "1.00"
PREFIX = ","
CONFIG_PATH = r"pixiv.yml"
PLUGIN_NAME = "pixiv"

HELP_URL = r"https://www.huajitech.net/pagermaid-pixiv-plugin-help/"


try:
    with open(CONFIG_PATH, mode="r") as config_file:
        _config: Dict[str, Any] = yaml.safe_load(config_file)
except FileNotFoundError:
    _config: Dict[str, Any] = {}


def strtolist(value: Optional[str]) -> List[str]:
    return value.split(",") if value else []


Handler = Callable[[Client, Message], Awaitable[None]]


class PluginConfig:
    proxy: Optional[str] = os.environ.get("PLUGIN_PIXIV_PROXY") or _config.get("proxy")

    refresh_token: Optional[str] = os.environ.get(
        "PLUGIN_PIXIV_REFRESH_TOKEN"
    ) or _config.get("refresh_token")

    message_elements: List[str] = (
        strtolist(os.environ.get("PLUGIN_PIXIV_MESSAGE_ELEMENTS"))
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


command_map: Dict[str, HandlerInfo] = {}


def command(
    command: str, description: str, usage: str = ""
) -> Callable[[Handler], Handler]:
    def decorator(func: Handler):
        command_map[command] = HandlerInfo(func, usage, description)
        return func

    return decorator


def generate_usage() -> str:
    return "\n".join(
        f"`{PREFIX}{PLUGIN_NAME} {command} {info.usage}`\n{info.description}"
        for command, info in command_map.items()
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
    return [illust for illust in illusts if needed.intersection(illust.tags) or True]


async def get_api() -> AppPixivAPI:
    api = AppPixivAPI(proxy=PluginConfig.proxy)

    if PluginConfig.refresh_token is None:
        logs.info(f"未设置 {PLUGIN_NAME} 插件登录所需的 refresh_token，将以游客身份工作。")
    else:
        await api.login(refresh_token=PluginConfig.refresh_token)

    return api


async def send_illust(client: Client, chat_id: int, illust: Illust) -> None:
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
            f'作者: <a href="https://www.pixiv.net/user/{illust.author_id}">{illust.author_name}</a> ({illust.author_account})\n'
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
        await client.send_photo(chat_id, illust.image_urls["large"], caption)
    else:
        await client.send_message(chat_id, caption)


async def report_error(origin_message: Message, ex: Exception) -> None:
    message = f"{type(ex).__name__}: {ex}"
    await origin_message.edit("呜呜呜 ~ 出错了:\n" + message)
    logs.error(message)


@command("search", "通过关键词（可传入多个）搜索 Pixiv 相关插图，并随机选取一张图发送", "<关键词> ... [R-18 / R-18G]")
async def search(client: Client, message: Message) -> None:
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
    await send_illust(client, message.chat.id, illust)
    await message.safe_delete()


@command(
    "recommend",
    "获取 Pixiv 每日推荐，可传入多个 Tag 参数筛选目标结果，并随机选取一张图发送",
    "[Tag] ... [R-18 / R-18G]",
)
async def recommend(client: Client, message: Message) -> None:
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
    await send_illust(client, message.chat.id, illust)
    await message.safe_delete()


@command("help", "获取插件帮助")
async def help(client: Client, message: Message) -> None:
    await message.edit(
        f"{PLUGIN_NAME} 插件使用帮助: {HELP_URL}", disable_web_page_preview=True
    )


@listener(
    command=PLUGIN_NAME,
    description=generate_usage(),
    parameters=f"{{{'|'.join(command_map.keys())}}}",
)
async def message_handler(client: Client, message: Message) -> None:
    command: str = message.parameter[0]
    info = command_map.get(command)
    if not info:
        await message.edit(f"我看不懂你发了什么诶。要不发送 `{PREFIX}help {PLUGIN_NAME}` 看看？")
        return
    new_message = copy.copy(message)
    new_message.arguments = new_message.arguments[len(command) + 1 :]
    new_message.parameter = new_message.parameter[1:]
    new_message.bind(client)
    try:
        return await info.func(client, new_message)
    except Exception as ex:
        await report_error(message, ex)
