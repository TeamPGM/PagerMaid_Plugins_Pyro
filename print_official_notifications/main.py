from pagermaid import logs
from pagermaid.enums import Message
from pagermaid.listener import listener


@listener(incoming=True, outgoing=True, privates_only=True)
async def print_official_notifications(message: Message):
    if not message.from_user.is_verified:
        return
    logs.info(
        f"Official notification from {message.from_user.first_name}: {message.text}"
    )
