from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import client as requests


async def post(text):
    url = 'https://lab.magiconch.com/api/nbnhhsh/guess'
    data = {'text': text}
    return await requests.post(url, data=data)


@listener(command="hhsh",
          parameters="<text>",
          description="能不能好好说话？")
async def nbnhhsh(message: Message):
    text = None
    if message.arguments:
        text = message.arguments
    elif message.reply_to_message:
        text = message.reply_to_message.text
    if not text:
        return await message.edit("请输入或回复一个文本,多个关键词用逗号隔开。")
    try:
        message: Message = await message.edit(f"{text}查询中...")
    except Exception:
        return await message.edit("出错了呜呜呜 ~ 无效的参数。")
    try:
        data = await post(text)
        data = data.json()
    except Exception as e:
        return await message.edit(f"出错了呜呜呜 ~ 查询失败。{e}")

    reply = ""
    if len(data) > 0:
        for hua in data:
            reply += f"黑话 : {hua['name']}\n可能的意思 : "
            if 'trans' in hua:
                for keyWord in hua['trans']:
                    reply += f"{keyWord} "
                reply += "\n"
            else:
                reply += f"{hua['name']}~~\n呜呜呜~我也听不懂捏~\n"
    else:
        reply += "呜呜呜~我也听不懂捏~"
    await message.edit(reply)
