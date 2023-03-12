import contextlib
import shutil
from os import makedirs
from os.path import exists, dirname, abspath
from pagermaid.listener import listener
from pagermaid.enums import Client, Message, AsyncClient
from pyrogram.types import InputMediaPhoto
from pyrogram.errors import RPCError

pixiv_img_host = "pixiv.yuki.sh"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.42'
}


async def get_result(message, request, r18=2):
    # r18: 0为非 R18，1为 R18，2为混合（在库中的分类，不等同于作品本身的 R18 标识）
    # num: 图片的数量
    # size: 返回图片的尺寸质量
    zpr_path = f"{dirname(abspath(__file__))}/zpr/"
    if not exists(zpr_path):
        makedirs(zpr_path)

    size = "regular"
    des = "出错了，没有纸片人看了。"
    data = await request.get(
        f"https://api.lolicon.app/setu/v2?num=5&r18={r18}&size={size}",
        headers=headers,
        timeout=10,
    )
    if data.status_code != 200:
        return None, None, "连接二次元大门出错。。。"
    await message.edit("已进入二次元 . . .")
    try:
        result = data.json()['data']
    except Exception:
        return None, None, "解析JSON出错。"
    setu_list = []  # 发送
    await message.edit("努力获取中 。。。")
    for i in range(5):
        urls = result[i]['urls'][size].replace('i.pixiv.re', pixiv_img_host)
        img_name = f"{result[i]['pid']}_{i}.jpg"
        try:
            img = await request.get(urls, headers=headers, timeout=10)
            with open(f"{zpr_path}{img_name}", mode="wb") as f:
                f.write(img.content)
        except Exception:
            return None, None, "连接二次元出错。。。"
        setu_list.append(InputMediaPhoto(media=f"{zpr_path}{img_name}"))
    return setu_list, zpr_path, des if setu_list else None


@listener(command="zpr",
          description="随机获取一组涩涩纸片人。",
          parameters="{r18}")
async def zpr(client: Client, message: Message, request: AsyncClient):
    arguments = message.arguments.upper().strip()
    message_thread_id = message.reply_to_top_message_id or message.reply_to_message_id
    message = await message.edit("正在前往二次元。。。")
    try:
        photoList, zpr_path, des = await get_result(message, request, r18=2 if arguments == "R18" else 0)
        if not photoList:
            shutil.rmtree(zpr_path)
            return await message.edit(des)
        with contextlib.suppress(Exception):
            await message.edit("传送中。。。")
        try:
            await client.send_media_group(message.chat.id, photoList, reply_to_message_id=message_thread_id)
        except RPCError as e:
            return await message.edit(
                "此群组不允许发送媒体。" if e.ID == "CHAT_SEND_MEDIA_FORBIDDEN" else f"发生错误：\n`{e}`")
    except Exception as e:
        return await message.edit(f"发生错误：\n`{e}`")
    shutil.rmtree(zpr_path)
    await message.safe_delete()
