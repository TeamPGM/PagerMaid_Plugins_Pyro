import contextlib
from typing import Optional

from pyrogram.enums import ChatType
from pyrogram.errors import PhotoCropSizeSmall, ImageProcessFailed, BadRequest
from pyrogram.raw.functions.photos import UploadContactProfilePhoto
from pyrogram.raw.types import InputUser

from pagermaid import Config
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove
from pagermaid.utils import lang


async def get_photo(message: Message) -> Optional[str]:
    if reply := message.reply_to_message:
        if reply.photo:
            return await reply.download()
        elif reply.document and reply.document.mime_type and reply.document.mime_type.startswith("image"):
            return await reply.download()
    elif message.photo:
        return await message.download()
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image"):
        return await message.download()
    return None


async def set_photo(client: Client, user: InputUser, photo: str, me: bool) -> None:
    if me:
        await client.set_profile_photo(photo=photo)
    else:
        try:
            await client.invoke(
                UploadContactProfilePhoto(
                    user_id=user,
                    suggest=False,
                    save=True,
                    file=await client.save_file(photo),
                )
            )
        except BadRequest:
            await set_photo(client, user, photo, True)
    safe_remove(photo)


@listener(
    command="pfp",
    description=lang("pfp_des")
)
async def pfp(client: Client, message: Message):
    """ Sets your profile picture. """
    me = await client.get_me()
    peer = await client.resolve_peer(me.id)
    with contextlib.suppress(Exception):
        if message.chat.type == ChatType.PRIVATE:
            peer = await client.resolve_peer(message.chat.id)
    photo = await get_photo(message)
    if not photo:
        return await message.edit(f"{lang('error_prefix')}{lang('pfp_e_notp')}")
    if not Config.SILENT:
        message = await message.edit(lang('pfp_process'))
    try:
        await set_photo(client, peer, photo, peer.user_id == me.id)
        await message.edit("头像修改成功啦 ~")
        return
    except PhotoCropSizeSmall:
        await message.edit(f"{lang('error_prefix')}{lang('pfp_e_size')}")
    except ImageProcessFailed:
        await message.edit(f"{lang('error_prefix')}{lang('pfp_e_img')}")
    except Exception:
        await message.edit(f"{lang('error_prefix')}{lang('pfp_e_notp')}")
