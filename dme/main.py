""" Module to message deletion. """

import contextlib

from typing import TYPE_CHECKING

from pagermaid.enums import Client, Message
from pagermaid.listener import listener, _lock
from pagermaid.modules.prune import self_prune
from pagermaid.static import read_context
from pagermaid.utils import lang

if TYPE_CHECKING:
    from pagermaid.enums.command import CommandHandler


@listener(
    is_plugin=False,
    command="dme",
    need_admin=True,
    description=lang("sp_des"),
    parameters=lang("sp_parameters"),
)
async def dme(bot: Client, message: Message):
    """Deletes specific amount of messages you sent."""
    async with _lock:
        with contextlib.suppress(Exception):
            del read_context[(message.chat.id, message.id)]
    _self_prune: "CommandHandler" = self_prune
    await _self_prune.handler(bot, message)
