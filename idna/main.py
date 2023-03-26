# pyright: basic


from pagermaid.enums import Message
from pagermaid.listener import listener


@listener(command="punyencode", description="编码至 Punycode", parameters="[待编码内容]")
async def punyencode(message: Message) -> None:
    if message.arguments:
        try:
            result = message.arguments.encode("idna").decode()
        except Exception:
            result = "呜呜呜 ~ 转换失败了，可能含有非法字符。"
    else:
        result = "请输入参数"
    await message.edit(f"`{result}`")


@listener(command="punydecode", description="从 Punycode 解码", parameters="[待解码内容]")
async def punydecode(message: Message) -> None:
    if message.arguments:
        try:
            result = message.arguments.encode().decode("idna")
        except Exception:
            result = "呜呜呜 ~ 转换失败了，可能含有非法字符。"
    else:
        result = "请输入参数"
    await message.edit(f"`{result}`")
