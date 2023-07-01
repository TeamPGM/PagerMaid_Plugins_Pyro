import contextlib
from urllib.parse import urlparse

from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import client as requests


async def get_ip_info(url: str) -> str:
    data = await requests.get(
        f"http://ip-api.com/json/{url}?fields=status,message,country,regionName,"
        f"city,lat,lon,isp,org,as,mobile,proxy,hosting,query"
    )
    ipinfo_json = data.json()
    if ipinfo_json["status"] == "fail":
        return ""
    elif ipinfo_json["status"] == "success":
        ipinfo_list = [f"查询目标： `{url}`"]
        if ipinfo_json["query"] != url:
            ipinfo_list.extend(["解析地址： `" + ipinfo_json["query"] + "`"])
        ipinfo_list.extend(
            [
                (
                    (
                        "地区： `"
                        + ipinfo_json["country"]
                        + " - "
                        + ipinfo_json["regionName"]
                        + " - "
                        + ipinfo_json["city"]
                    )
                    + "`"
                ),
                "经纬度： `"
                + str(ipinfo_json["lat"])
                + ","
                + str(ipinfo_json["lon"])
                + "`",
                "ISP： `" + ipinfo_json["isp"] + "`",
            ]
        )
        if ipinfo_json["org"] != "":
            ipinfo_list.extend(["组织： `" + ipinfo_json["org"] + "`"])
        with contextlib.suppress(Exception):
            ipinfo_list.extend(
                [
                    "["
                    + ipinfo_json["as"]
                    + "](https://bgp.he.net/"
                    + ipinfo_json["as"].split()[0]
                    + ")"
                ]
            )
        if ipinfo_json["mobile"]:
            ipinfo_list.extend(["此 IP 可能为**蜂窝移动数据 IP**"])
        if ipinfo_json["proxy"]:
            ipinfo_list.extend(["此 IP 可能为**代理 IP**"])
        if ipinfo_json["hosting"]:
            ipinfo_list.extend(["此 IP 可能为**数据中心 IP**"])
        return "\n".join(ipinfo_list)


@listener(command="ip", description="IPINFO （或者回复一句话）", parameters="[ip/域名]")
async def ipinfo(message: Message):
    reply = message.reply_to_message
    message: Message = await message.edit("正在查询中...")
    try:
        if reply:
            for num in range(len(reply.entities)):
                url = reply.text[
                    reply.entities[num].offset : reply.entities[num].offset
                    + reply.entities[num].length
                ]
                url = urlparse(url)
                url = url.hostname or url.path
                await message.edit(await get_ip_info(url))
                return
        elif message.arguments:
            url_ = urlparse(message.arguments)
            url = url_.hostname or url_.path
            if ":" in url and "." not in url and not url_.hostname:
                url = message.arguments
            await message.edit(await get_ip_info(url))
            return
        await message.edit("没有找到要查询的 ip/域名 ...")
    except Exception:
        await message.edit("没有找到要查询的 ip/域名 ...")
