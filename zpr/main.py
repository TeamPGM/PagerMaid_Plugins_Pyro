import json

from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove
from pagermaid.enums import Client, Message, AsyncClient
from pyrogram.types import InputMediaPhoto

async def get_result(message,request,r18=0):
    # r18: 0为非 R18，1为 R18，2为混合（在库中的分类，不等同于作品本身的 R18 标识）
    # num: 图片的数量
    # size: 返回图片的尺寸质量
    size = "regular"
    data = await request.get((f"https://api.lolicon.app/setu/v2?num=5&r18={r18}&size={size}"))
    if data.status_code != 200:
        return "连接二次元大门出错。。。",None

    await message.edit("已进入二次元 . . .")
    try:
        result = json.loads(data.text)['data']
    except Exception:
        return "解析JSON出错。",None
    setuList = []#发送
    delList = []#删除
    i = 0
    await message.edit("努力获取中 。。。")
    while i < 5:
        urls = result[i]['urls'][size]
        try:
            img =  await request.get(urls)
            imgname = (f"setu{i}.png")
            with open(imgname, mode="wb") as f:
                f.write(img.content)
        except Exception:
            return "连接二次元出错。。。",None
        i += 1
        setuList.append(InputMediaPhoto(imgname))
        delList.append(imgname)
    return setuList,delList if setuList else None

@listener(command="zpr",
          description="随机获取一组涩涩纸片人。",
          parameters="{r18}")
async def ghs(client: Client, message: Message, request: AsyncClient):
    msg = message
    await message.edit("正在前往二次元。。。")

    if message.arguments.upper().strip() == "R18":
        photoList,delList = await get_result(message,request,r18=1)
    else:
        photoList,delList = await get_result(message,request)

    if not photoList:
        return await msg.edit("出错了，没有纸片人看了。")
    try:
        await message.edit("传送中。。。")
        await client.send_media_group(message.chat.id,photoList)
        for i in range(5):
            safe_remove(delList[i])
    except Exception:
        return await msg.edit("出错了，没有纸片人看了。")
    await msg.safe_delete()
    
