import secrets

from os import sep

from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove
from pagermaid.utils import client


async def get_wallpaper_url(num):
    json_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&mkt=zh-CN&n=1&idx={str(num)}"
    req = await client.get(json_url)
    url = ""
    copy_right = ""
    if req.status_code == 200:
        data = req.json()
        url = data['images'][0]['url']
        copy_right = data['images'][0]['copyright']
    return url, copy_right


@listener(command="bingwall",
          description="获取Bing每日壁纸（带参数发送原图）")
async def bingwall(message: Message):
    status = False
    filename = f"data{sep}wallpaper.jpg"
    for _ in range(3):
        num = secrets.choice(range(7))
        url, copy_right = await get_wallpaper_url(num)
        image_url = f"https://www.bing.com{url}"
        try:
            if image_url != " ":
                img = await client.get(image_url)
            else:
                continue
            if img.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(img.content)
                if message.arguments:
                    await message.reply_document(
                        filename,
                        caption=f"#bing wallpaper\n"
                                f"{str(copy_right)}",
                        quote=False)
                else:
                    await message.reply_photo(
                        filename,
                        caption=f"#bing wallpaper\n"
                                f"{str(copy_right)}",
                        quote=False)
                status = True
                break  # 成功了就赶紧结束啦！
        except Exception:
            continue
    safe_remove(filename)
    if not status:
        return await message.edit("出错了呜呜呜 ~ 试了好多好多次都无法访问到服务器 。")
    await message.safe_delete()
