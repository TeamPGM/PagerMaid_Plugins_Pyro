from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient


async def get_video_url(client: AsyncClient) -> str:
    res = await client.get("https://tucdn.wpon.cn/api-girl/index.php?wpon=json", timeout=10.0)
    data = res.json()
    return "https:" + data["mp4"]


@listener(command="xjj", description="小姐姐视频")
async def xjj(message: Message, client: AsyncClient):
    if message.chat and message.chat.id == -1001441461877:
        # 用户群禁止使用此功能
        await message.edit("本群禁止使用此功能。")
        return
    await message.edit("小姐姐视频生成中 . . .")
    try:
        url = await get_video_url(client)
        try:
            await message.reply_video(
                url,
                quote=False,
                reply_to_message_id=message.reply_to_message_id,
                message_thread_id=message.message_thread_id,
            )
            await message.safe_delete()
        except Exception as e:
            await message.edit(f"出错了呜呜呜 ~ {e.__class__.__name__}")
    except Exception as e:
        await message.edit(f"出错了呜呜呜 ~ {e.__class__.__name__}")
