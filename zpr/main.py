import contextlib
import shutil
from os import makedirs
from os.path import exists, dirname, abspath
from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove
from pagermaid.enums import Client, Message, AsyncClient
from pyrogram.types import InputMediaPhoto

async def get_result(message, request, r18=0):
    # r18: 0为非 R18，1为 R18，2为混合（在库中的分类，不等同于作品本身的 R18 标识）
    # num: 图片的数量
    # size: 返回图片的尺寸质量
    zpr_path = f"{dirname(abspath(__file__))}/zpr/"
    if not exists(zpr_path):
        makedirs(zpr_path)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.42'
    }
    size = "regular"
    des = "出错了，没有纸片人看了。"
    data = await request.get((f"https://api.lolicon.app/setu/v2?num=5&r18={r18}&size={size}"), headers=headers, timeout=10)
    if data.status_code != 200:
        return None, None, "连接二次元大门出错。。。"
    await message.edit("已进入二次元 . . .")
    try:
        result = data.json()['data']
    except Exception:
        return None, None, "解析JSON出错。"
    setuList = []  # 发送
    await message.edit("努力获取中 。。。")
    for i in range(5):
        urls = result[i]['urls'][size].replace('i.pixiv.re', 'img.misaka.gay')
        imgname = (f"{result[i]['pid']}_{i}.jpg")
        try:
            img = await request.get(urls, headers=headers, timeout=10)
            with open(f"{zpr_path}{imgname}", mode="wb") as f:
                f.write(img.content)
        except Exception:
            return None, None, "连接二次元出错。。。"
        setuList.append(InputMediaPhoto(f"{zpr_path}{imgname}"))
    return setuList, zpr_path, des if setuList else None

@listener(command="zpr",
          description="随机获取一组涩涩纸片人。",
          parameters="{r18}")
async def zpr(client: Client, message: Message, request: AsyncClient):
    arguments = message.arguments.upper().strip()
    message = await message.edit("正在前往二次元。。。")
    try:
        photoList, zpr_path, des = await get_result(message, request, r18=1 if arguments == "R18" else 0)
        if not photoList:
            shutil.rmtree(zpr_path)
            return await message.edit(des)
        with contextlib.suppress(Exception):
            message = await message.edit("传送中。。。")
        await client.send_media_group(message.chat.id, photoList)
    except Exception as e:
        await client.send_message(message.chat.id, f"{des}\n\n错误信息：\n`{e}`")
    shutil.rmtree(zpr_path)
    await message.safe_delete()
