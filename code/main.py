# python3
# -*- coding: utf-8 -*-
# @Time    : 2021/11/22 14:17
# @Author  : yzyyz
# @Email   :  youzyyz1384@qq.com
# @File    : run.py
# @Software: PyCharm
import re
import httpx

from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient

codeType = {
    "py": ["python", "py"],
    "cpp": ["cpp", "cpp"],
    "java": ["java", "java"],
    "php": ["php", "php"],
    "js": ["javascript", "js"],
    "c": ["c", "c"],
    "c#": ["csharp", "cs"],
    "go": ["go", "go"],
    "asm": ["assembly", "asm"],
}


async def run(string: str, client: AsyncClient):
    string = string.replace("&amp;", "&").replace("&#91;", "[").replace("&#93;", "]")
    try:
        a = re.findall(
            r"(py|php|java|cpp|js|c#|c|go|asm)\s?(-i)?\s?(\w*)?(\n|\r)((?:.|\n)+)",
            string,
        )[0]
        print(a)
    except Exception:
        return "输入有误汪\n目前仅支持c/cpp/c#/py/php/go/java/js"
    lang, code_str = a[0], a[4]
    if "-i" in string:
        data_json = {
            "files": [{"name": f"main.{codeType[lang][1]}", "content": code_str}],
            "stdin": a[2],
            "command": "",
        }
    else:
        data_json = {
            "files": [{"name": f"main.{codeType[lang][1]}", "content": code_str}],
            "stdin": "",
            "command": "",
        }
    headers = {
        "Authorization": "Token 0123456-789a-bcde-f012-3456789abcde",
        "content-type": "application/",
    }
    res = await client.post(
        url=f"https://glot.io/run/{codeType[lang][0]}?version=latest",
        headers=headers,
        json=data_json,
    )
    if res.status_code != 200:
        return "请求失败了呐~~~"
    if res.json()["stdout"] == "":
        return res.json()["stderr"].strip()
    return f"<b>>>></b> <code>{code_str}</code> \n{res.json()['stdout']}"


@listener(command="code", description="运行代码", parameters="[语言] [-i] [inputText]\n[代码]")
async def code(message: Message, client: AsyncClient):
    await message.edit(await run(message.arguments, client))
