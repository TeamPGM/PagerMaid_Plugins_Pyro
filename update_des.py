import json
import os


def update_des():
    list_json_start = ["", "alpha/"]
    for start in list_json_start:
        with open(f"{start}list.json", "r", encoding="utf8") as f:
            list_json = json.load(f)
        for plugin in list_json["list"]:
            if os.path.exists(f"{start}{plugin['name']}{os.sep}DES.md"):
                with open(
                    f"{start}{plugin['name']}{os.sep}DES.md", "r", encoding="utf8"
                ) as f:
                    plugin["des"] = f.read().strip()
        with open(f"{start}list.json", "w", encoding="utf8") as f:
            json.dump(list_json, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    update_des()
