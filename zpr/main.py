import contextlib
import shutil
from pagermaid.listener import listener
from pagermaid.enums import Client, Message, AsyncClient
from pyrogram.types import InputMediaPhoto
from pyrogram.errors import RPCError
from pathlib import Path

# pixiv反代服务器
pixiv_img_host = "i.pixiv.cat"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.2651.74"
}
data_path = Path("data/zpr")

async def get_result(message, request, r18=0, tag="", num=1):
    data_path.mkdir(parents=True, exist_ok=True)
    des = "出错了，没有纸片人看了。"
    data = await request.get(
        f"https://api.lolicon.app/setu/v2?num={num}&r18={r18}&tag={tag}&size=regular&size=original&proxy={pixiv_img_host}&excludeAI=true",
        headers=headers,
        timeout=10,
    )
    spoiler = r18 == 1
    if data.status_code != 200:
        return None, "连接二次元大门出错。。。"
    await message.edit("已进入二次元 . . .")
    try:
        result = data.json()["data"]
    except Exception:
        return None, "解析JSON出错。"
    setu_list = []  # 发送
    await message.edit("努力获取中 。。。")
    for i in range(int(num)):
        urls = result[i]["urls"]["regular"]
        original = result[i]["urls"]["original"]
        pid = result[i]["pid"]
        title = result[i]["title"]
        width = result[i]["width"]
        height = result[i]["height"]
        img_name = f"{result[i]['pid']}_{i}.jpg"
        file_path = data_path / img_name
        try:
            img = await request.get(urls, headers=headers, timeout=10)
            if img.status_code != 200:
                continue
            with open(file_path, mode="wb") as f:
                f.write(img.content)
        except Exception:
            return None, None, "连接二次元出错。。。"
        setu_list.append(InputMediaPhoto(media=str(file_path), caption=f"**{title}**\nPID:[{pid}](https://www.pixiv.net/artworks/{pid})\n查看原图:[点击查看]({original})\n原图尺寸:{width}x{height}", has_spoiler=spoiler))
    return setu_list, des if setu_list else None

@listener(command="zpr", description="随机获取一组涩涩纸片人。", parameters="{tag} {r18} {num}")
async def zpr(client: Client, message: Message, request: AsyncClient):
    message = await message.edit("正在前往二次元。。。")
    p = message.parameter
    n = 1
    r = 0
    t = ""
    try:
        if len(p) > 0:
            if p[0].isdigit():
                n = p[0]
            elif p[0] == "r18":
                r = 1
                if len(p) > 1 and p[1].isdigit():
                    n = p[1]
            else:
                t = p[0]
                if len(p) > 1:
                    if p[1].isdigit():
                        n = p[1]
                    elif p[1] == "r18":
                        r = 1
                        if len(p) > 2 and p[2].isdigit():
                            n = p[2]
        photoList, des = await get_result(
            message, request, r18=r, tag=t, num=n
        )
        if not photoList:
            shutil.rmtree("data/zpr")
            return await message.edit(des)
        with contextlib.suppress(Exception):
            await message.edit("传送中。。。")
        try:
            await client.send_media_group(
                message.chat.id,
                photoList,
                reply_to_message_id=message.reply_to_message_id,
                message_thread_id=message.message_thread_id,
            )
        except RPCError as e:
            return await message.edit(
                "此群组不允许发送媒体。"
                if e.ID == "CHAT_SEND_MEDIA_FORBIDDEN"
                else f"发生错误：\n`{e}`"
            )
    except Exception as e:
        return await message.edit(f"发生错误：\n`{e}`")
    shutil.rmtree("data/zpr")
    await message.safe_delete()
