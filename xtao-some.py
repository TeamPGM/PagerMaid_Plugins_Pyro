import json

from pyrogram import Client

from pagermaid.listener import listener
from pagermaid.utils import alias_command, Message, client


@listener(is_plugin=True, outgoing=True, command=alias_command("guess"),
          description="能不能好好说话？ - 拼音首字母缩写释义工具（需要回复一句话）")
async def guess(c: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请先输入一个缩写。")
    message = await message.edit("获取中 . . .")

    text = {'text': text}
    guess_json = (await client.post("https://lab.magiconch.com/api/nbnhhsh/guess", json=text)).json()
    guess_res = []
    if not len(guess_json) == 0:
        for num in range(0, len(guess_json)):
            guess_res1 = json.loads(json.dumps(guess_json[num]))
            guess_res1_name = guess_res1['name']
            try:
                guess_res1_ans = ", ".join(guess_res1['trans'])
            except:
                try:
                    guess_res1_ans = ", ".join(guess_res1['inputting'])
                except:
                    guess_res1_ans = "尚未录入"
            guess_res.extend(["词组：" + guess_res1_name + "\n释义：" + guess_res1_ans])
        await message.edit("\n\n".join(guess_res))
    else:
        await message.edit("没有匹配到拼音首字母缩写")
