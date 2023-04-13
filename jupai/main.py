import urllib.parse

from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.utils import lang

ju_pai_api = "https://api.txqq.pro/api/zt.php"


@listener(
    command="jupai",
    description="生成举牌小人",
    parameters="[text/reply]"
)
async def ju_pai(message: Message):
    text = message.obtain_message()
    if not text:
        return await message.edit(lang('arg_error'))
    try:
        image_url = f"{ju_pai_api}?msg={urllib.parse.quote(text)}"
        await message.reply_photo(
            image_url,
            quote=False,
            reply_to_message_id=message.reply_to_message_id or message.reply_to_top_message_id,
        )
        await message.safe_delete()
    except Exception as e:
        await message.edit(f"获取失败 ~ {e.__class__.__name__}")
