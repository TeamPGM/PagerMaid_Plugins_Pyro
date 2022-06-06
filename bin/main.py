import json
import requests
from json.decoder import JSONDecodeError
from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message


@listener(command="bin", 
          description="查询信用卡信息", 
          parameters="<bin（4到8位数字）>")
async def card(_: Client, message: Message):
    await message.edit('正在查询中...')
    try:
        card_bin = message.arguments
    except ValueError:
        await message.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    try:
        r = requests.get("https://lookup.binlist.net/" + card_bin)
    except:
        await message.edit("出错了呜呜呜 ~ 无法访问到binlist。")
        return
    if r.status_code == 404:
        await message.edit("出错了呜呜呜 ~ 目标卡头不存在")
        return
    if r.status_code == 429:
        await message.edit("出错了呜呜呜 ~ 每分钟限额超过，请等待一分钟再试")
        return

    try:
        bin_json = json.loads(r.content.decode("utf-8"))
    except JSONDecodeError:
        await message.edit("出错了呜呜呜 ~ 无效的参数。")
        return

    msg_out = []
    msg_out.extend(["BIN：" + card_bin])
    try:
        msg_out.extend(["卡品牌：" + bin_json['scheme']])
    except (KeyError, TypeError):
        pass
    try:
        msg_out.extend(["卡类型：" + bin_json['type']])
    except (KeyError, TypeError):
        pass
    try:
        msg_out.extend(["卡种类：" + bin_json['brand']])
    except (KeyError, TypeError):
        pass
    try:
        msg_out.extend(["发卡行：" + bin_json['bank']["name"]])
    except (KeyError, TypeError):
        pass
    try:
        if bin_json['prepaid']:
            msg_out.extend(["是否预付：是"])
        else:
            msg_out.extend(["是否预付：否"])
    except (KeyError, TypeError):
        pass
    try:
        msg_out.extend(["发卡国家：" + bin_json['country']['name']])
    except (KeyError, TypeError):
        pass
    await message.edit("\n".join(msg_out))
