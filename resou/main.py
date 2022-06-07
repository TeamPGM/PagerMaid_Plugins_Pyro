from pyrogram import Client
from json.decoder import JSONDecodeError
from pagermaid.listener import listener
from pagermaid.utils import Message, client


@listener(command="zhrs",
          description="知乎热搜。")
async def zhrs(_: Client, message: Message):
    req = await client.get("https://tenapi.cn/zhihuresou")
    if req.status_code == 200:
        try:
            data = req.json()
        except JSONDecodeError:
            await message.edit("出错了呜呜呜 ~ API 数据解析失败。")
            return
        res = '知乎实时热搜榜：\n'
        for i in range(0, 10):
            res += f'\n{i + 1}.「<a href={data["list"][i]["url"]}>{data["list"][i]["query"]}</a>」'
        await message.edit(res)
    else:
        await message.edit("出错了呜呜呜 ~ 无法访问到 API 服务器 。")


@listener(command="wbrs",
          description="微博热搜。")
async def wbrs(_: Client, message: Message):
    req = await client.get("https://tenapi.cn/resou")
    if req.status_code == 200:
        try:
            data = req.json()
        except JSONDecodeError:
            await message.edit("出错了呜呜呜 ~ API 数据解析失败。")
            return
        res = '微博实时热搜榜：\n'
        for i in range(0, 10):
            res += f'\n{i + 1}.「<a href={data["list"][i]["url"]}>{data["list"][i]["name"]}</a>」  ' \
                   f'热度：{data["list"][i]["hot"]}'
        await message.edit(res)
    else:
        await message.edit("出错了呜呜呜 ~ 无法访问到 API 服务器 。")


@listener(command="dyrs",
          description="抖音热搜。")
async def dyrs(_: Client, message: Message):
    req = await client.get("https://tenapi.cn/douyinresou")
    if req.status_code == 200:
        try:
            data = req.json()
        except JSONDecodeError:
            await message.edit("出错了呜呜呜 ~ API 数据解析失败。")
            return
        res = '抖音实时热搜榜：\n'
        for i in range(0, 10):
            res += f'\n{i + 1}.「{data["list"][i]["name"]}」  热度：{data["list"][i]["hot"]}'
        await message.edit(res)
    else:
        await message.edit("出错了呜呜呜 ~ 无法访问到 API 服务器 。")
