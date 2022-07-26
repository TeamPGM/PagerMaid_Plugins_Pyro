from typing import List, Dict, Optional

from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.services import client as httpx


class JIKIPediaDefinition:
    plaintext: str
    tags: List[Optional[str]]
    title: str
    item_id: int
    image: Optional[str]

    def __init__(self, plaintext: str, tags: List[Dict], title: str, item_id: int, image: Optional[str]):
        self.plaintext = plaintext
        self.tags = []
        for i in tags:
            if name := i.get("name"):
                self.tags.append(name)
        self.title = title
        self.item_id = item_id
        self.image = image

    def format(self):
        plaintext = self.plaintext.replace("\u200b", "").replace("\u200c", "")
        tags = " ".join([f"#{x}" for x in list(self.tags)]) if self.tags else "该词条还没有Tag哦～"

        text = f"词条：【{self.title}】\n\n"
        text += f"{plaintext}\n\n"
        text += f"Tags：{tags}\n"
        text += f"原文：https://jikipedia.com/definition/{self.item_id}"
        return text


class JIKIPedia:
    url = "https://api.jikipedia.com/go/search_entities"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-TW;q=0.9,zh;q=0.8",
        "Client": "web",
        "Client-Version": "2.7.2g",
        "Connection": "keep-alive",
        "Host": "api.jikipedia.com",
        "Origin": "https://jikipedia.com",
        "Referer": "https://jikipedia.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Token": "",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Mobile Safari/537.36",
        "XID": "uNo5bL1nyNCp/Gm7lJAHQ91220HLbMT8jqk9IJYhtHA4ofP+zgxwM6lSDIKiYoppP2k1IW/1Vxc2vOVGxOOVReebsLmWPHhTs7NCRygfDkE=",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
    }

    def __init__(self, key: str):
        self.definitions = []
        self.message = None
        self.data = None
        self.key = key

    async def search(self):
        req = await httpx.post(url=self.url, headers=self.headers, json={"phrase": self.key, "page": 1, "size": 60})
        return self.parse(**req.json())

    def parse(self, **kwargs):
        self.data = kwargs.get("data", None)
        self.definitions = []
        if self.data:
            for i in self.data:
                if definitions := i.get("definitions", None):
                    for j in definitions:
                        plaintext = j.get("plaintext", "")
                        tags = j.get("tags", [])
                        title = j.get("term", {}).get("title", "")
                        if not title:
                            continue
                        item_id = j.get("id", 0)
                        images = j.get("images", [])
                        image = ""
                        if len(images) > 0:
                            image = images[0].get("full", {}).get("path", "")
                        self.definitions.append(JIKIPediaDefinition(plaintext, tags, title, item_id, image))
        self.message = kwargs.get("message", None)
        if issubclass(type(self.message), dict):
            self.message = self.message.get("title", None)


@listener(command="jikipedia",
          parameters="<关键词>",
          description="梗查询")
async def jikipedia(message: Message):
    if not message.arguments:
        return await message.edit("请输入关键词")
    data = JIKIPedia(message.arguments)
    await data.search()
    if not data.definitions:
        return await message.edit("没有找到相关结果")
    text = data.definitions[0].format()
    image = data.definitions[0].image
    if len(data.definitions) > 1:
        text += "\n\n"
        text += "你是否还想找这些："
        suggester = []
        for i in range(1, len(data.definitions)):
            if data.definitions[i].title not in suggester:
                suggester.append(data.definitions[i].title)
            if len(suggester) == 5:
                break
        for i in suggester:
            text += f" 【{i}】"
    if not image:
        await message.edit(text, disable_web_page_preview=True)
    else:
        await message.reply_photo(image, quote=False, caption=text)
        await message.safe_delete()
