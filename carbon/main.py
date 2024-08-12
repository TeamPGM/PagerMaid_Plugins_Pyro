import os
from io import BytesIO


from pagermaid.enums import AsyncClient, Message
from pagermaid.listener import listener
from pagermaid.utils import lang


async def make_carbon(code: str, client: AsyncClient) -> BytesIO:
    url = "https://carbonara.solopov.dev/api/cook"
    resp = await client.post(url, json={"code": code}, timeout=60.0)
    image = BytesIO(resp.read())
    image.name = "carbon.png"
    return image


async def get_from_file(message: Message) -> str:
    msg = None
    reply = message.reply_to_message
    if message.document and message.document.mime_type.startswith("text"):
        msg = message
    elif reply and reply.document and reply.document.mime_type.startswith("text"):
        msg = reply
    if msg:
        path = await msg.download()
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            return ""
        finally:
            os.remove(path)
        return text


@listener(command="carbon", description="Take an image of code snippet.", parameters="code")
async def carbon_func(client: AsyncClient, message: Message):
    code = await get_from_file(message)
    if not code:
        code = message.obtain_message()
    if not code:
        return await message.edit(lang("arg_error"))
    message = await message.edit("`Preparing Carbon . . .`")
    carbon = await make_carbon(code, client)
    message = await message.edit("`Uploading . . .`")
    await message.reply_photo(carbon, quote=False)
    await message.safe_delete()
