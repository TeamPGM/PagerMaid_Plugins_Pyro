from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import client as requests

import socket


def is_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except Exception:
        return False


def get_ip(domain):
    try:
        ip = socket.gethostbyname(domain)
    except Exception:
        return None
    return ip


async def post(host):
    url = 'https://api.potatonet.idc.wiki/network/simple_health_check/scripts/gfw_check'
    data = {'host': host}
    return await requests.post(url, data=data)


@listener(command="gfw",
          parameters="[text]",
          description="查询是否被墙")
async def gfw(message: Message):
    text = None
    if message.arguments:
        text = message.arguments
    elif message.reply_to_message:
        text = message.reply_to_message.text
    if not text:
        return await message.edit("请输入或回复一个IP或域名。")
    try:
        if not is_ip(text):
            if get_ip(text) is None:
                return await message.edit("出错了呜呜呜 ~ 无效的参数。")
            else:
                text = get_ip(text)
        try:
            message: Message = await message.edit(f"{text} 查询中...")
        except Exception:
            return await message.edit("出错了呜呜呜 ~ 无效的参数。")
        data = await post(text)
        data = data.json()
    except Exception as e:
        return await message.edit(f"出错了呜呜呜 ~ 查询失败。{e}")

    if data['success']:
        if data['data']['tcp']['cn'] == data['data']['tcp']['!cn'] and data['data']['icmp']['cn'] == \
                data['data']['icmp']['!cn']:
            if data['data']['tcp']['cn'] == False and data['data']['icmp']['cn'] == False:
                reply = f"IP: {text}\n状态: 全球不通，不能判断是否被墙"
            else:
                reply = f"IP: {text}\n状态: 未被墙"
        else:
            reply = f"IP: {text}\n状态: 被墙"
    else:
        reply = f"IP: {text}\n状态: 查询失败"
    return await message.edit(reply)
