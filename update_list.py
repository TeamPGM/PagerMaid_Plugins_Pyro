import json
import os
from httpx import get

main = get("https://api.github.com/repos/TeamPGM/PagerMaid_Plugins_Pyro/commits/v2").json()
plugins = [i["filename"].split("/")[0] for i in main["files"] if "/main.py" in i["filename"]]
with open("list.json", "r", encoding="utf8") as f:
    list_json = json.load(f)
for plugin in plugins:
    exist = False
    for plug_dict in list_json["list"]:
        if plug_dict["name"] == plugin:
            exist = True
            old_version = float(plug_dict["version"])
            list_json["list"][list_json["list"].index(plug_dict)]["version"] = str(old_version + 0.01)
            break
    if not exist:
        list_json["list"].append(
            {"name": plugin,
             "version": "1.0",
             "section": "chat",
             "maintainer": main['commit']['author']['name'],
             "size": f"{os.path.getsize(f'{plugin}{os.sep}main.py') / 1000} kb",
             "supported": True,
             "des-short": "这个人很懒，什么都没留下",
             "des": "这个人很懒，什么都没有留下。"})
with open("list.json", "w", encoding="utf8") as f:
    json.dump(list_json, f, ensure_ascii=False, indent=4)
print(main['sha'] + " ok！")
