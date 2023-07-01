import json
from pyrogram import Client

from pagermaid.listener import listener
from pagermaid.utils import Message, client


@listener(
    is_plugin=True, command="guess", description="能不能好好说话？ - 拼音首字母缩写释义工具（需要回复一句话）"
)
async def guess(_: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请先输入一个缩写。")
    message = await message.edit("获取中 . . .")

    text = {"text": text}
    guess_json = (
        await client.post("https://lab.magiconch.com/api/nbnhhsh/guess", json=text)
    ).json()
    if len(guess_json) != 0:
        guess_res = []
        for num in range(len(guess_json)):
            guess_res1 = json.loads(json.dumps(guess_json[num]))
            guess_res1_name = guess_res1["name"]
            try:
                guess_res1_ans = ", ".join(guess_res1["trans"])
            except:
                try:
                    guess_res1_ans = ", ".join(guess_res1["inputting"])
                except:
                    guess_res1_ans = "尚未录入"
            guess_res.extend([f"词组：{guess_res1_name}" + "\n释义：" + guess_res1_ans])
        await message.edit("\n\n".join(guess_res))
    else:
        await message.edit("没有匹配到拼音首字母缩写")


@listener(is_plugin=True, command="wiki", description="查询维基百科词条", parameters="[词组]")
async def wiki(_: Client, message: Message):
    text = message.arguments
    if not text:
        return await message.edit("请先输入一个关键词。")
    message = await message.edit("获取中 . . .")
    try:
        req = await client.get(
            f"https://zh.wikipedia.org/w/api.php?action=query&list=search&format=json&formatversion=2&srsearch={text}"
        )

        wiki_json = json.loads(req.content.decode("utf-8"))
    except:
        return await message.edit("出错了呜呜呜 ~ 无法访问到维基百科。")
    try:
        if len(wiki_json["query"]["search"]) != 0:
            wiki_title = wiki_json["query"]["search"][0]["title"]
            wiki_content = (
                wiki_json["query"]["search"][0]["snippet"]
                .replace('<span class="searchmatch">', "**")
                .replace("</span>", "**")
            )
            wiki_time = (
                wiki_json["query"]["search"][0]["timestamp"]
                .replace("T", " ")
                .replace("Z", " ")
            )
            text = (
                (
                    f"词条： [{wiki_title}](https://zh.wikipedia.org/zh-cn/{wiki_title}"
                    + ")\n\n"
                    + wiki_content
                )
                + "...\n\n此词条最后修订于 "
            ) + wiki_time

        else:
            text = "没有匹配到相关词条"
    except KeyError:
        text = wiki_json["error"]["info"]
    await message.edit(text)
