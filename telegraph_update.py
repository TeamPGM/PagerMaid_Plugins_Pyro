import json
import sys

from telegraph import Telegraph

token = str(sys.argv[1])
path = "PagerMaid-Plugins-11-27"
title = "PagerMaid Pyro 插件列表"
name = "PagerMaid-Modify Update"
url = "https://t.me/PagerMaid_Modify"
temp = """<h3 id="{0}">{0}</h3><p>{1}</p><blockquote>,apt install {0}</blockquote>"""
telegraph = Telegraph(token)


def gen():
    with open("list.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    k = []
    data["list"].sort(key=lambda i: i["name"])
    for i in data["list"]:
        des = i["des_short"]
        if i["des"].startswith("这个人很懒") or i["des"] == i["des_short"]:
            pass
        else:
            des += i["des"]
        k.append(temp.format(i["name"], des))
    return "<hr>".join(k)


telegraph.edit_page(
    path=path, title=title, html_content=gen(), author_name=name, author_url=url
)
