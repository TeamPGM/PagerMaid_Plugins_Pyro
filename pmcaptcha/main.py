# pmcaptcha - a pagermaid-pyro plugin by cloudreflection
# https://t.me/cloudreflection_channel/268
# ver 2022/06/24

from pyrogram import Client
from pyrogram.enums.chat_type import ChatType
from pyrogram.raw.functions.account import UpdateNotifySettings
from pyrogram.raw.functions.messages import DeleteHistory
from pyrogram.raw.types import InputNotifyPeer, InputPeerNotifySettings

from pagermaid import log
from pagermaid.utils import Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite
from pagermaid.sub_utils import Sub

import asyncio
import random

captcha_success = Sub("pmcaptcha.success")
pm_captcha_help_msg = '''```,pmcaptcha```
查询当前私聊用户验证状态

```,pmcaptcha check id```
查询指定id用户验证状态

```,pmcaptcha add [id]```
将id加入已验证，如未指定为当前私聊用户id

```,pmcaptcha del [id]```
移除id验证记录，如未指定为当前私聊用户id

```,pmcaptcha wel [message]```
查看或设置验证通过时发送的消息
使用 ```,pmcaptcha wel -clear``` 可恢复默认规则

```,pmcaptcha bl [list]```
查看或设置关键词黑名单列表（英文逗号分隔）
使用 ```,pmcaptcha bl -clear``` 可清空列表

```,pmcaptcha wait [int]```
查看或设置超时时间，默认为 30 秒
使用```,pmcaptcha wait off```可关闭验证时间限制

```,pmcaptcha disablepm [true/false]```
启用/禁止陌生人私聊
此功能会放行联系人和白名单(已通过验证)用户
您可以使用 ,pmcaptcha add 将用户加入白名单

```,pmcaptcha stats```
查看验证计数器
使用 ```,pmcaptcha stats -clear``` 可重置

```,pmcaptcha action [ban/delete/archive/none]```
选择验证失败的处理方式，默认为 archive

```,pmcaptcha premium [allow/ban/only/none]```
选择对premium用户的操作，默认为 none

```,pmcaptcha wl [list]```
查看或设置关键词白名单列表（英文逗号分隔）
使用 ```,pmcaptcha wl -clear``` 可清空列表

设置优先级: disablepm>premium>wl>bl
遇到任何问题请先 ```,apt update``` 更新后复现再反馈
捐赠: cloudreflection.eu.org/donate'''


@listener(is_plugin=False, incoming=False, outgoing=True, ignore_edited=True, privates_only=True)
async def process_pm_captcha_self(_: Client, message: Message):
    if message.chat.id == 777000 or message.chat.type == ChatType.BOT:
        return
    cid = message.chat.id
    if message.text:
        try:
            if message.text[0] == ",":  # 忽略命令
                return
        except UnicodeDecodeError:
            pass
    if captcha_success.check_id(cid):
        return
    else:
        return captcha_success.add_id(cid)


async def do_action_and_read(client, cid, data):
    await client.unarchive_chats(chat_ids=cid)
    await asyncio.sleep(random.randint(0, 100) / 1000)
    await client.read_chat_history(cid)
    await asyncio.sleep(random.randint(0, 100) / 1000)
    action = data.get("action", "archive")
    if action in ["archive", "delete", "ban"]:
        await client.block_user(user_id=cid)
    if action in ["archive"]:
        await client.archive_chats(chat_ids=cid)
    if action in ["delete"]:
        try:
            await client.invoke(DeleteHistory(max_id=0, peer=await client.resolve_peer(cid)))
        except Exception as e:
            pass
    # log
    await log(f"(pmcaptcha) 已对 [{cid}](tg://openmessage?user_id={cid}) 执行 {action} 操作")
    data['banned'] = data.get('banned', 0) + 1
    sqlite['pmcaptcha'] = data


@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=True, privates_only=True)
async def process_pm_captcha(client: Client, message: Message):
    # 忽略联系人、服务消息、机器人消息
    if message.from_user.is_contact or message.from_user.id == 777000 or message.chat.type == ChatType.BOT:
        return
    cid = message.chat.id
    data = sqlite.get("pmcaptcha", {})
    if data.get('disable', False) and not captcha_success.check_id(cid):
        await message.reply('对方已设置禁止私聊，您已被封禁\n\nThe recipient is blocking all private messages. You are now blocked.')
        await do_action_and_read(client, cid, data)
        return
    if premium := data.get("premium", False):
        if premium=="only" and message.from_user.is_premium==False:
            await message.reply('对方已设置仅Telegram Premium用户可私聊，您已被封禁\n\nThe recipient is that only Telegram Premium user can send private messages. You are now blocked.')
            await do_action_and_read(client, cid, data)
            return
        if premium=="ban" and message.from_user.is_premium==True:
            await message.reply('对方已设置禁止Telegram Premium用户私聊，您已被封禁\n\nThe recipient is blocking all private messages from Telegram Premium users. You are now blocked.')
            await do_action_and_read(client, cid, data)
            return
        if premium=="allow" and message.from_user.is_premium==True:
            return
    if (
        not captcha_success.check_id(cid)
        and sqlite.get(f"pmcaptcha.{str(cid)}") is None
    ):
        if data.get("whitelist", False) and message.text is not None: #白名单
            for i in data.get("whitelist", "").split(","):
                if i in message.text:
                    return captcha_success.add_id(cid)
        if data.get("blacklist", False) and message.text is not None: #黑名单
            for i in data.get("blacklist", "").split(","):
                if i in message.text:
                    await message.reply('您触犯了黑名单规则，已被封禁\n\nYou are blocked because of a blacklist violation')
                    await do_action_and_read(client, cid, data)
        try:
            await client.invoke(UpdateNotifySettings(peer=InputNotifyPeer(peer=await client.resolve_peer(cid)),
                                                     settings=InputPeerNotifySettings(silent=True)))
        except:  # noqa
            pass
        await asyncio.sleep(random.randint(0, 100) / 1000)
        await client.read_chat_history(cid)
        await asyncio.sleep(random.randint(0, 100) / 1000)
        await client.archive_chats(chat_ids=cid)
        wait = data.get("wait", 30)
        key1 = random.randint(1, 10)
        key2 = random.randint(1, 10)
        sqlite[f'pmcaptcha.{str(cid)}'] = str(key1 + key2)
        if wait!="已关闭":
            msg = await message.reply(
                '已启用私聊验证。请发送 \"' + str(key1) + '+' + str(key2) + '\" 的答案(阿拉伯数字)来与我私聊\n请在' + str(wait) +
                '秒内完成验证。您只有一次验证机会\n\nPlease answer the following question to prove you are human: \"' +
                str(key1) + '+' + str(key2) + '\"\nYou have ' + str(wait) +
                ' seconds and only one chance to answer.')
            await asyncio.sleep(wait)
            await msg.safe_delete()  # noqa
            if sqlite.get(f'pmcaptcha.{str(cid)}') is not None:
                del sqlite[f'pmcaptcha.{str(cid)}']
                await message.reply('验证超时,您已被封禁\n\nYou failed provide an answer in time. You are now blocked.')
                await do_action_and_read(client, cid, data)
        else:
            await message.reply(
                '已启用私聊验证。请发送 \"' + str(key1) + '+' + str(key2) + '\" 的答案(阿拉伯数字)来与我私聊。\
                您只有一次验证机会\n\nPlease answer the following question to prove you are human: \"' +
                str(key1) + '+' + str(key2) + '\"\nYou have only one chance to answer.')
    elif sqlite.get(f"pmcaptcha.{str(cid)}"):
        if message.text == sqlite.get(f"pmcaptcha.{str(cid)}"):
            await message.safe_delete()
            del sqlite[f'pmcaptcha.{str(cid)}']
            captcha_success.add_id(cid)
            try:
                await client.invoke(UpdateNotifySettings(peer=InputNotifyPeer(peer=await client.resolve_peer(cid)),
                                                         settings=InputPeerNotifySettings(silent=False)))
            except:  # noqa
                pass
            await asyncio.sleep(random.randint(0, 100) / 1000)
            await message.reply(data.get("Welcome", "验证通过\n\nYou have passed the captcha."))
            await asyncio.sleep(random.randint(0, 100) / 1000)
            await client.unarchive_chats(chat_ids=cid)
            data['pass'] = data.get('pass', 0) + 1
            sqlite['pmcaptcha'] = data
        else:
            del sqlite[f'pmcaptcha.{str(cid)}']
            await message.reply('验证错误，您已被封禁\n\nYou provided an incorrect answer. You are now blocked.')
            await do_action_and_read(client, cid, data)


@listener(is_plugin=True, outgoing=True, command="pmcaptcha",
          need_admin=True,
          description='一个简单的私聊人机验证  请使用 ```,pmcaptcha h``` 查看可用命令')
async def pm_captcha(client: Client, message: Message):
    cid_ = str(message.chat.id)
    data = sqlite.get("pmcaptcha", {})
    if len(message.parameter) == 0:
        if message.chat.type != ChatType.PRIVATE:
            await message.edit('请在私聊时使用此命令，或添加参数执行')
            await asyncio.sleep(3)
            await message.safe_delete()
        text = "已验证用户" if captcha_success.check_id(message.chat.id) else "未验证/验证中用户"
        await message.edit(text)
    elif len(message.parameter) == 1:
        if message.parameter[0] == "bl":
            await message.edit(
                '当前黑名单规则:\n' + str(data.get('blacklist', '无')) + '\n如需编辑，请使用 ,pmcaptcha bl +关键词（英文逗号分隔）')
        if message.parameter[0] == "wl":
            await message.edit(
                '当前白名单规则:\n' + str(data.get('whitelist', '无')) + '\n如需编辑，请使用 ,pmcaptcha wl +关键词（英文逗号分隔）')
        elif message.parameter[0] == 'wel':
            await message.edit(
                '当前通过时消息规则:\n' + str(data.get('welcome', '无')) + '\n如需编辑，请使用 ,pmcaptcha wel +要发送的消息')
        elif message.parameter[0] == 'wait':
            await message.edit(
                '当前验证等待时间(秒): ' + str(data.get('wait', '30')) + '\n如需编辑，请使用 ,pmcaptcha wait +等待秒数(整数)或使用 ,pmcaptcha wait off 关闭该功能')
        elif message.parameter[0] == 'h':
            await message.edit(pm_captcha_help_msg)
            if message.chat.type != ChatType.PRIVATE:
                await asyncio.sleep(5)
                return await message.safe_delete()
        elif message.parameter[0] == 'disablepm':
            status = '开启' if data.get('disable', False) else '关闭'
            await message.edit(
                (
                    (
                        f'当前禁止私聊状态: 已{status}'
                        + '\n如需修改 请使用 ,pmcaptcha disablepm true/false'
                    )
                    + '\n此功能会放行联系人和白名单(已通过验证)用户'
                )
            )

        elif message.parameter[0] == 'stats':
            await message.edit('自上次重置起，已进行验证 ' + str(data.get('pass', 0) + data.get('banned', 0)) +
                               ' 次\n其中，通过验证 ' + str(data.get('pass', 0)) + ' 次，拦截 ' + str(data.get('banned', 0)) + ' 次')
        elif message.parameter[0] == 'premium':
            premium_action={"allow":"不验证Premium用户私聊","ban":"禁止Premium用户私聊","only":"仅允许Premium用户私聊","none":"无操作"}
            await message.edit(
                '当前对Premium用户的操作为: '+ premium_action.get(data.get("premium","none"))+'\n如需编辑，请使用 ,pmcaptcha premium [allow/ban/only/none] 修改')
        elif message.chat.type != ChatType.PRIVATE:
            await message.edit('请在私聊时使用此命令，或添加id参数执行')
            await asyncio.sleep(3)
            await message.safe_delete()
        elif message.parameter[0] == 'add':
            await message.edit(f'已将id {cid_} 添加至白名单')
            captcha_success.add_id(message.chat.id)
        elif message.parameter[0] == 'del':
            if captcha_success.del_id(message.chat.id):
                await message.edit(f'已删除id {cid_} 的验证记录')
            else:
                await message.edit('记录不存在')
        else:
            await message.edit('参数错误')
    elif message.parameter[0] == 'add':
        if message.parameter[1].isnumeric():
            await message.edit(f'已将id {message.parameter[1]} 添加至白名单')
            captcha_success.add_id(int(message.parameter[1]))
            await client.unarchive_chats(chat_ids=int(message.parameter[1]))
        else:
            await message.edit('参数错误')
    elif message.parameter[0] == 'del':
        if message.parameter[1].isnumeric():
            if captcha_success.del_id(int(message.parameter[1])):
                await message.edit(f'已删除id {message.parameter[1]} 的验证记录')
            else:
                await message.edit('记录不存在')
        else:
            await message.edit('参数错误')
    elif message.parameter[0] == 'wel':
        if message.parameter[1] == '-clear':
            if data.get("welcome", False):
                del data["welcome"]
                sqlite["pmcaptcha"] = data
            await message.edit('已恢复至默认规则')
            return
        data["welcome"] = " ".join(message.parameter[1:])
        sqlite["pmcaptcha"] = data
        await message.edit('规则已更新')
    elif message.parameter[0] == 'wait':
        if message.parameter[1]=="off":
            data["wait"] = "已关闭"
            sqlite["pmcaptcha"] = data
            await message.edit('已关闭验证时间限制')
        elif message.parameter[1].isnumeric():
            data["wait"] = int(message.parameter[1])
            sqlite["pmcaptcha"] = data
            await message.edit('等待时间已更新')
        else:
            await message.edit('错误:不是整数')
    elif message.parameter[0] == 'bl':
        if message.parameter[1] == '-clear':
            if data.get("blacklist", False):
                del data["blacklist"]
                sqlite["pmcaptcha"] = data
            await message.edit('规则列表已清空')
            return
        data["blacklist"] = " ".join(message.parameter[1:])
        sqlite["pmcaptcha"] = data
        await message.edit('规则已更新')
    elif message.parameter[0] == 'wl':
        if message.parameter[1] == '-clear':
            if data.get("whitelist", False):
                del data["whitelist"]
                sqlite["pmcaptcha"] = data
            await message.edit('规则列表已清空')
            return
        data["whitelist"] = " ".join(message.parameter[1:])
        sqlite["pmcaptcha"] = data
        await message.edit('规则已更新')
    elif message.parameter[0] == 'check':
        if message.parameter[1].isnumeric():
            if captcha_success.check_id(int(message.parameter[1])):
                await message.edit(f'id {message.parameter[1]} 已验证')
            else:
                await message.edit(f'id {message.parameter[1]} 未验证')
        else:
            await message.edit('未知用户/无效id')
    elif message.parameter[0] == 'disablepm':
        if message.parameter[1] == 'true':
            data["disable"] = True
            sqlite["pmcaptcha"] = data
            await message.edit('已禁止非白名单和联系人私聊\n您可以使用 ,pmcaptcha disablepm false 重新启用私聊')
        elif message.parameter[1] == 'false':
            data["disable"] = False
            sqlite["pmcaptcha"] = data
            await message.edit('已关闭禁止私聊，人机验证仍会工作')
    elif message.parameter[0] == 'stats' and message.parameter[1] == '-clear':
        data["pass"] = 0
        data["banned"] = 0
        sqlite["pmcaptcha"] = data
        await message.edit('已重置计数器')
    elif message.parameter[0] == 'action':
        if message.parameter[1] == 'ban':
            data["action"] = 'ban'
            sqlite["pmcaptcha"] = data
            await message.edit('验证失败后将执行**封禁**操作')
        elif message.parameter[1] == 'delete':
            data["action"] = 'delete'
            sqlite["pmcaptcha"] = data
            await message.edit('验证失败后将执行**封禁和删除**会话操作')
        elif message.parameter[1] == 'archive':
            data["action"] = 'archive'
            sqlite["pmcaptcha"] = data
            await message.edit('验证失败后将执行**封禁和归档**会话操作')
        elif message.parameter[1] == 'none':
            data["action"] = 'none'
            sqlite["pmcaptcha"] = data
            await message.edit('验证失败后将不执行任何操作')
        else:
            await message.edit('参数错误。')
    elif message.parameter[0]=="premium":
        if message.parameter[1] == "allow":
            data["premium"] = 'allow'
            sqlite["pmcaptcha"] = data
            await message.edit('将不对 Telegram Premium 用户发起验证')
        if message.parameter[1] == "ban":
            data["premium"] = 'ban'
            sqlite["pmcaptcha"] = data
            await message.edit('将禁止 Telegram Premium 用户私聊')
        if message.parameter[1] == "only":
            data["premium"] = 'only'
            sqlite["pmcaptcha"] = data
            await message.edit('将**仅允许** Telegram Premium 用户私聊')
        if message.parameter[1] == "none":
            del data["premium"]
            sqlite["pmcaptcha"] = data
            await message.edit('将不对 Telegram Premium 用户执行额外操作')
