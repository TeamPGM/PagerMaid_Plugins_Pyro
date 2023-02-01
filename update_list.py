import json
import os
import decimal
from httpx import get

from update_des import update_des

main = get("https://api.github.com/repos/TeamPGM/PagerMaid_Plugins_Pyro/commits/v2").json()
plugins = []
for file in main["files"]:
    if file["filename"] == "list.json":
        print(main['sha'] + " no need！")
        exit()
    if "/main.py" in file["filename"]:
        plugins.append(file["filename"].split("/")[0])
delete = bool(main['commit']['message'].startswith("Delete:"))

with open("list.json", "r", encoding="utf8") as f:
    list_json = json.load(f)
for plugin in plugins:
    exist = False
    for plug_dict in list_json["list"]:
        if plug_dict["name"] == plugin:
            exist = True
            old_version = decimal.Decimal(plug_dict["version"])
            list_json["list"][list_json["list"].index(plug_dict)]["version"] = str(
                old_version + decimal.Decimal("0.01")
            )
            if delete:
                list_json["list"].remove(plug_dict)
            break
    if not exist:
        list_json["list"].append(
            {
                "name": plugin,
                 "version": "1.0",
                 "section": "chat",
                 "maintainer": main['commit']['author']['name'],
                 "size": f"{os.path.getsize(f'{plugin}{os.sep}main.py') / 1000} kb",
                 "supported": True,
                 "des-short": main['commit']['message'],
                 "des": "",
            }
        )
with open("list.json", "w", encoding="utf8") as f:
    json.dump(list_json, f, ensure_ascii=False, indent=4)

update_des()

print(main['sha'] + " ok！")
