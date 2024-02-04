from io import BytesIO

from pagermaid.enums import Client, Message, AsyncClient
from pagermaid.listener import listener


@listener(command="httpcat", description="获取 HTTP 状态码的图片。", parameters="[http 状态码]")
async def httpcat(client: Client, message: Message, request: AsyncClient):
    try:
        code = int(message.arguments)
    except ValueError:
        return await message.edit("http 状态码错误。")
    if code < 100 or code > 599:
        return await message.edit("http 状态码错误。")
    pic = await request.get(f"https://http.cat/{code}.jpg")
    if pic.status_code != 200:
        return await message.edit("http 状态码错误。")
    io = BytesIO(pic.content)
    io.name = "1.jpg"
    await client.send_photo(
        message.chat.id,
        io,
        reply_to_message_id=message.reply_to_message_id
        if message.outgoing
        else message.id,
        message_thread_id=message.message_thread_id,
    )
    await message.safe_delete()
