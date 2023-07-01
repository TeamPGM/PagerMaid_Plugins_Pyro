# pyright: basic


from pagermaid.enums import Message
from pagermaid.listener import listener


@listener(
    command="punyencode", description="编码至 Punycode", parameters="[待编码内容] (支持回复消息)"
)
async def punyencode(message: Message):
    if not (text := message.obtain_message()):
        return await message.edit("请输入参数")
    try:
        encoded = text.encode("idna").decode()
    except Exception:
        return await message.edit("呜呜呜 ~ 转换失败了，可能含有非法字符。")
    await message.edit(f"`{encoded}`")


@listener(
    command="punydecode", description="从 Punycode 解码", parameters="[待解码内容] (支持回复消息)"
)
async def punydecode(message: Message):
    if not (text := message.obtain_message()):
        return await message.edit("请输入参数")
    try:
        decoded = text.encode().decode("idna")
    except Exception:
        return await message.edit("呜呜呜 ~ 转换失败了，可能含有非法字符。")
    await message.edit(f"`{decoded}`")
