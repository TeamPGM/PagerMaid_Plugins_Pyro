from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient
from urllib.parse import quote


@listener(
    command="qqmusic",
    description="qq音乐搜索",
    parameters="[歌名]",
)
async def qq_music(message: Message, client: AsyncClient):
    text = message.obtain_message()
    if not text:
        await message.edit("请指定歌名。")
        return
    key = quote(text)
    msg: Message = await message.edit("正在查询，请稍候...")
    try:
        res = await client.get(
            f"https://zj.v.api.aa1.cn/api/qqmusic/?songName={key}&pageNum=1&pageSize=1&type=qq",
            timeout=10.0,
        )
        if res.status_code == 200:
            resp = res.json()
            data = resp["list"]
            if len(data) == 0:
                return await msg.edit("没有找到相关音乐")
            uri = data[0].get("url")
            cover = data[0].get("cover")
            if not uri:
                return await msg.edit("获取音乐链接失败")
            await msg.edit("正在发送音乐，请稍候...")
            try:
                await message.reply_audio(
                    uri,
                    thumb=cover or None,
                    caption=f"{text}",
                    reply_to_message_id=message.reply_to_message_id
                    or message.reply_to_top_message_id,
                )
                await msg.safe_delete()
            except Exception as e:
                await msg.edit(f"发送音乐失败 ~ {e.__class__.__name__}")
        else:
            await msg.edit(f"获取音乐失败 ~ 接口返回 {res.status_code}")
    except Exception as e:
        await msg.edit(f"出错了呜呜呜 ~ {e.__class__.__name__}")
