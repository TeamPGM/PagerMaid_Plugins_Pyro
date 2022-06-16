from pyrogram import Client
from pyrogram.types import User
from pagermaid.listener import listener
from pagermaid.utils import Message, client, execute


async def obtain_message(context) -> str:
    reply = context.reply_to_message
    message = context.arguments
    if reply and not message:
        message = reply.text
    return message


async def get_api(api: str) -> str:
    tmp = ""
    resp = await client.get(api)
    if resp.status_code == 200:
        data = resp.json()
        tmp = "ip:{}\r\nasn:{}\r\norganization:{}\r\ncountry:{}\r\ndescription:{}\r\ntype:{}".format(data["ip"], data["asn"]["number"], data["asn"]["organization"], data["country"]["name"], data["description"], data["type"]["is"])
    if tmp:
        return tmp
    else:
    	return "😂 No Response ~"


@listener(
    is_plugin=True,
    outgoing=True,
    command="ip",
    description="查询ip信息",
    parameters="[ip]/me"
)
async def ip(_: Client, msg: Message):
    address = await obtain_message(msg)
    if not address:
        return await msg.edit("请输入要查询的ip")
    elif address == "me":
        address = ""
    api = "https://ip.186526.xyz/{}?type=json&format=true".format(address)
    text = await get_api(api)
    await msg.edit(f"`{text}`")


@listener(
    is_plugin=True,
    outgoing=True,
    command="pingdc",
    description="查询到各个DC区的延时"
)
async def pingdc(_: Client, msg: Message):
    DCs = {
        1: "149.154.175.50",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130"
    }
    data = []
    for dc in range(1, 6):
        result = await execute(f"ping -c 1 {DCs[dc]} | awk -F '/' " + "'END {print $5}'")
        data.append(result.replace('\n', '') if result else '-1')

    await msg.edit(
        f"🇺🇸 DC1(迈阿密): `{data[0]}ms`\n"
        f"🇳🇱 DC2(阿姆斯特丹): `{data[1]}ms`\n"
        f"🇺🇸 DC3(迈阿密): `{data[2]}ms`\n"
        f"🇳🇱 DC4(阿姆斯特丹): `{data[3]}ms`\n"
        f"🇸🇬 DC5(新加坡): `{data[4]}ms`"
    )

@listener(
    is_plugin=True,
    outgoing=True,
    command="route",
    description="besttrace 路由回程跟踪",
    parameters="[ip]"
)
async def route(_: Client, msg: Message):
    ip = await obtain_message(msg)
    result = await execute(f"mkdir -p shell && cd shell && wget -q https://raw.githubusercontent.com/fscarmen/tools/main/return_pure.sh -O return.sh && bash return.sh {ip}")
    if result:
        if len(result) > 4096:
            await attach_log(result, msg.chat.id, f"{ip}.log", msg.id)
            return
        await msg.edit(result)
    else:
        return


@listener(
    is_plugin=True,
    outgoing=True,
    command="dc",
    description="用户或机器人分配的 DC"
)
async def dc(_: Client, msg: Message):
    reply = msg.reply_to_message
    if msg.arguments:
        return await msg.edit("您好像输入了一个无效的参数。")
    if reply:
        user = await _.get_users(reply.from_user.id)
    if not reply:
        user = await _.get_me()

    dc = user.dc_id
    if dc:
        await msg.edit(f"[dc] 所在数据中心为: **DC{dc}**")
    else:
        await msg.edit("[dc] 需要先设置头像并且对我可见。")
