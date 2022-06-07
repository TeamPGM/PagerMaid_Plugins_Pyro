from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, client


@listener(command="whois",
          description="查看域名是否已被注册、注册日期、过期日期、域名状态、DNS解析服务器等。")
async def whois(_: Client, context: Message):
    try:
        message = context.arguments
    except ValueError:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    req = await client.get("https://namebeta.com/api/search/check?query=" + message)
    if req.status_code == 200:
        try:
            data = req.json()["whois"]["whois"].split("For more information")[0].rstrip()
        except:
            await context.edit("出错了呜呜呜 ~ 可能是域名不正确。")
            return
        await context.edit(f"<code>{data}</code>")
    else:
        await context.edit("出错了呜呜呜 ~ 无法访问到 API 服务器 。")
