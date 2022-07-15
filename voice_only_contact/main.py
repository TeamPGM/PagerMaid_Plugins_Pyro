import contextlib

from pyrogram import filters

from pagermaid.listener import raw_listener
from pagermaid.single_utils import Message


@raw_listener(filters.private & filters.voice & filters.incoming)
async def voice_only_contact(message: Message):
    with contextlib.suppress(Exception):
        if message.from_user.is_contact:
            return
        await message.delete()
