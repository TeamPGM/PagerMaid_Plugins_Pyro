from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message
from base64 import b64decode, b64encode


@listener(command="b64e",
          description="将文本转为Base64",
          parameters="<text>")
async def b64e(_: Client, message: Message):
    msg = message.arguments
    if not msg:
        return await message.edit("`出错了呜呜呜 ~ 无效的参数。`")

    result = b64encode(msg.encode("utf-8")).decode("utf-8")

    if result:
        await message.edit(f"`{result}`")


@listener(command="b64d",
          description="将Base64转为文本",
          parameters="<text>")
async def b64d(_: Client, message: Message):
    msg = message.arguments
    if not msg:
        return await message.edit("`出错了呜呜呜 ~ 无效的参数。`")
    
    try:
        result = b64decode(msg).decode("utf-8")
    except:
        return await message.edit("`出错了呜呜呜 ~ 无效的参数。`")
    if result:
        await message.edit(f"`{result}`")
