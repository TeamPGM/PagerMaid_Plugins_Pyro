import json
from requests import get
from pyrogram import Client

from pagermaid.listener import listener
from pagermaid.utils import alias_command, Message, client


async def obtain_message(context) -> str:
    reply = context.reply_to_message
    message = context.arguments
    if reply and not message:
        message = reply.text
    if not message:
        raise ValueError(lang('msg_ValueError'))
    return message


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


@listener(is_plugin=True, outgoing=True, command="wiki", description="查询维基百科词条", parameters="<词组>")
async def wiki(_: Client, context: Message):
    await context.edit("获取中 . . .")
    try:
        message = await obtain_message(context)
    except ValueError:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    try:
        wiki_json = json.loads(get("https://zh.wikipedia.org/w/api.php?action=query&list=search&format=json&formatversion=2&srsearch=" + message).content.decode(
            "utf-8"))
    except:
        await context.edit("出错了呜呜呜 ~ 无法访问到维基百科。")
        return
    try:
        if not len(wiki_json['query']['search']) == 0:
            wiki_title = wiki_json['query']['search'][0]['title']
            wiki_content = wiki_json['query']['search'][0]['snippet'].replace('<span class=\"searchmatch\">',
                                                                              '**').replace(
                '</span>', '**')
            wiki_time = wiki_json['query']['search'][0]['timestamp'].replace('T', ' ').replace('Z', ' ')
            message = '词条： [' + wiki_title + '](https://zh.wikipedia.org/zh-cn/' + wiki_title + ')\n\n' + \
                      wiki_content + '...\n\n此词条最后修订于 ' + wiki_time
        else:
            message = "没有匹配到相关词条"
    except KeyError:
        message = wiki_json['error']['info']
    await context.edit(message)
