import json
import os
import decimal
from httpx import get

from update_des import update_des

main = get(
    "https://api.github.com/repos/TeamPGM/PagerMaid_Plugins_Pyro/commits/v2"
).json()
plugins = []
alpha_plugins = []
list_json_start = ["", "alpha/"]
for file in main["files"]:
    if "list.json" in file["filename"]:
        print(main["sha"] + " no need！")
        exit()
    if "/main.py" in file["filename"]:
        if file["filename"].startswith("alpha"):
            alpha_plugins.append(file["filename"].split("/")[1])
        else:
            plugins.append(file["filename"].split("/")[0])
delete = bool(main["commit"]["message"].startswith("Delete"))


for idx, plugins_ in enumerate([plugins, alpha_plugins]):
    with open(f"{list_json_start[idx]}list.json", "r", encoding="utf8") as f:
        list_json = json.load(f)
    plugin_map = {i["name"]: i for i in list_json["list"]}
    for plugin in plugins_:
        if plugin in plugin_map:
            if delete:
                plugin_map.pop(plugin)
                list_json["list"] = list(plugin_map.values())
                continue
            plug_dict = plugin_map[plugin]
            old_version = decimal.Decimal(plug_dict["version"])
            plug_dict["version"] = str(old_version + decimal.Decimal("0.01"))
            plug_dict[
                "size"
            ] = f"{os.path.getsize(f'{list_json_start[idx]}{plugin}{os.sep}main.py') / 1000} kb"
        else:
            short_des = main["commit"]["message"].split("\nCo-authored-by")[0].strip()
            list_json["list"].append(
                {
                    "name": plugin,
                    "version": "1.0",
                    "section": "chat",
                    "maintainer": main["commit"]["author"]["name"],
                    "size": f"{os.path.getsize(f'{list_json_start[idx]}{plugin}{os.sep}main.py') / 1000} kb",
                    "supported": True,
                    "des_short": short_des,
                    "des": "",
                }
            )
    with open(f"{list_json_start[idx]}list.json", "w", encoding="utf8") as f:
        json.dump(list_json, f, ensure_ascii=False, indent=4)

update_des()

print(main["sha"] + " ok！")
