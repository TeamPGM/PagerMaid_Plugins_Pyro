from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient
from pagermaid.single_utils import safe_remove


@listener(command="weather_lite", description="查询天气", parameters="[城市]")
async def weather_lite(request: AsyncClient, message: Message):
    if not message.arguments:
        return await message.edit("请输入城市名称")
    if message.arguments.startswith("_"):
        return await message.edit("请输入正确的城市名称")
    city = message.arguments.strip()
    data = await request.get(f"https://zh.wttr.in/{city}.png")
    if data.status_code != 200:
        return await message.edit("请输入正确的城市名称")
    with open("weather.png", "wb") as f:
        f.write(data.content)
    await message.reply_photo(
        "weather.png",
        reply_to_message_id=message.reply_to_message_id,
        message_thread_id=message.message_thread_id,
        quote=False,
    )
    await message.safe_delete()
    safe_remove("weather.png")
