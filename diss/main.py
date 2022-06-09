from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, client, edit_delete


@listener(command="diss", description="儒雅随和版祖安语录。")
async def diss(_: Client, message: Message):
    for i in range(5):  # 最多尝试5次
        req = await client.get("https://api.oddfar.com/yl/q.php?c=1009&encode=text")
        if req.status_code == 200:
            return await context.edit(req.text)
    await edit_delete(message, "出错了呜呜呜 ~ 试了好多好多次都无法访问到 API 服务器 。")
