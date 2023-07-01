import contextlib

from asyncio import sleep

from pyrogram.errors import FloodWait
from pyrogram.raw.functions.contacts import GetBlocked
from pyrogram.raw.types.contacts import BlockedSlice

from pagermaid.listener import listener
from pagermaid.enums import Client, Message


async def clear_blocked_func(client: Client, message: Message):
    offset = 0
    success, failed, skipped = 0, 0, 0
    while True:
        blocked = await client.invoke(GetBlocked(offset=offset, limit=100))
        if not blocked.users:
            break
        for user in blocked.users:
            if (user.bot or user.scam or user.fake) and not user.deleted:
                skipped += 1
                continue
            try:
                await client.unblock_user(user.id)
                success += 1
            except FloodWait as e:
                with contextlib.suppress(Exception):
                    await message.edit(
                        f"🧹 Clearing blocked users...\n\nWill run after {e.value} seconds."
                    )
                await sleep(e.value + 1)
                with contextlib.suppress(Exception):
                    await message.edit("🧹 Clearing blocked users...")
                await client.unblock_user(user.id)
                success += 1
            except Exception:
                failed += 1
        offset += 100
        if (
            isinstance(blocked, BlockedSlice) and offset > blocked.count
        ) or not isinstance(blocked, BlockedSlice):
            break
    return success, failed, skipped


@listener(command="clear_blocked", description="Clear blocked users.", need_admin=True)
async def clear_blocked(client: Client, message: Message):
    """Clear blocked users."""
    message: Message = await message.edit("🧹 Clearing blocked users...")
    try:
        success, failed, skipped = await clear_blocked_func(client, message)
    except Exception as e:
        await message.edit(f"❌ Failed to clear blocked users: {e}")
        return
    await message.edit(
        f"🧹 Clear blocked users complete. \n"
        f"Success: {success}, Failed: {failed}, Skipped: {skipped}"
    )
