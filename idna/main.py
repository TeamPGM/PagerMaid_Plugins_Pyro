# pyright: basic


from pagermaid.enums import Message
from pagermaid.listener import listener


@listener(command="punyencode",
          description="编码至 Punycode",
          parameters="<待编码内容>")
async def punyencode(message: Message):
    content = message.arguments
    encoded = content.encode("idna").decode()
    await message.edit(f"`{encoded}`")


@listener(command="punydecode",
          description="从 Punycode 解码",
          parameters="<待解码内容>")
async def punydecode(message: Message):
    content = message.arguments
    decoded = content.encode().decode("idna")
    await message.edit(f"`{decoded}`")
