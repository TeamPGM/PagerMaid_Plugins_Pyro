# pmcaptcha - a pagermaid-pyro plugin by cloudreflection
# https://t.me/cloudreflection_channel/268
# ver 2022/06/08

from pyrogram import Client
from pyrogram.enums.chat_type import ChatType
from pyrogram.raw.functions.account import UpdateNotifySettings
from pyrogram.raw.types import InputNotifyPeer, InputPeerNotifySettings

from pagermaid.utils import Message
from pagermaid.listener import listener
from pagermaid.single_utils import sqlite
from pagermaid.sub_utils import Sub

import asyncio
import random

captcha_success = Sub("pmcaptcha.success")


@listener(is_plugin=False, incoming=False, outgoing=True, ignore_edited=True, privates_only=True)
async def process_pm_captcha_self(_: Client, message: Message):
    if message.chat.id == 777000 or message.chat.type == ChatType.BOT:
        return
    cid = message.chat.id
    if message.text:
        try:
            if message.text[0] == ",": #忽略命令
                return
        except UnicodeDecodeError:
            pass
    if captcha_success.check_id(cid):
        return
    else:
        return captcha_success.add_id(cid)


@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=True, privates_only=True)
async def process_pm_captcha(client: Client, message: Message):
    # 忽略联系人、服务消息、机器人消息
    if message.from_user.is_contact or message.from_user.id == 777000 or message.chat.type == ChatType.BOT:
        return
    cid = message.chat.id
    data = sqlite.get("pmcaptcha", {})
    if data.get('disable',False) and not captcha_success.check_id(cid):
        await message.reply('对方已设置禁止私聊，您已被封禁\n\nYou are not allowed to send private messages to me and been banned')
        await client.block_user(user_id=cid)
        await asyncio.sleep(random.randint(0, 100) / 1000)
        return await client.archive_chats(chat_ids=cid)
        data['banned'] = data.get('banned',0) + 1
        sqlite['pmcaptcha'] = data
    if not captcha_success.check_id(cid) and sqlite.get("pmcaptcha." + str(cid)) is None:
        await client.read_chat_history(message.chat.id)
        if data.get("blacklist", False) and message.text is not None:
            for i in data.get("blacklist", "").split(","):
                if i in message.text:
                    await message.reply('您触犯了黑名单规则，已被封禁\n\nYou have violated the blacklist rules and been banned')
                    await client.block_user(user_id=cid)
                    await asyncio.sleep(random.randint(0, 100) / 1000)
                    return await client.archive_chats(chat_ids=cid)
                    data['banned'] = data.get('banned',0) + 1
                    sqlite['pmcaptcha'] = data
        try:
            await client.invoke(UpdateNotifySettings(peer=InputNotifyPeer(peer=await client.resolve_peer(cid)),
                                                     settings=InputPeerNotifySettings(silent=True)))
        except:  # noqa
            pass
        await asyncio.sleep(random.randint(0, 100) / 1000)
        await client.archive_chats(chat_ids=cid)
        wait = data.get("wait", 20)
        key1 = random.randint(1, 10)
        key2 = random.randint(1, 10)
        await asyncio.sleep(random.randint(0, 100) / 1000)
        sqlite['pmcaptcha.' + str(cid)] = str(key1 + key2)
        msg = await message.reply(
            '已启用私聊验证。请发送 \"' + str(key1) + '+' + str(key2) + '\" 的答案(阿拉伯数字)来与我私聊\n请在' + str(wait) +
            '秒内完成验证。您只有一次验证机会\n\nHuman verification is enabled.Please send the answer of this question \"' +
            str(key1) + '+' + str(key2) + '\" (numbers only) first.\nYou have ' + str(wait) +
            ' seconds to complete the verification.')
        await asyncio.sleep(wait)
        await msg.safe_delete()
        if sqlite.get('pmcaptcha.' + str(cid)) is not None:
            del sqlite['pmcaptcha.' + str(cid)]
            await message.reply('验证超时,您已被封禁\n\nVerification timeout.You have been banned.')
            await client.block_user(user_id=cid)
            await asyncio.sleep(random.randint(0, 100) / 1000)
            await client.archive_chats(chat_ids=cid)
            data['banned'] = data.get('banned',0) + 1
            sqlite['pmcaptcha'] = data
    elif sqlite.get("pmcaptcha." + str(cid)):
        if message.text == sqlite.get("pmcaptcha." + str(cid)):
            await message.safe_delete()
            del sqlite['pmcaptcha.' + str(cid)]
            captcha_success.add_id(cid)
            try:
                await client.invoke(UpdateNotifySettings(peer=InputNotifyPeer(peer=await client.resolve_peer(cid)),
                                                         settings=InputPeerNotifySettings(silent=False)))
            except:  # noqa
                pass
            await asyncio.sleep(random.randint(0, 100) / 1000)
            msg = await message.reply(data.get("welcome", "验证通过\n\nVerification Passed"))
            await asyncio.sleep(random.randint(0, 100) / 1000)
            await client.unarchive_chats(chat_ids=cid)
            data['pass'] = data.get('pass',0) + 1
            sqlite['pmcaptcha'] = data
            await asyncio.sleep(5)
            await msg.safe_delete()
        else:
            del sqlite['pmcaptcha.' + str(cid)]
            await message.reply('验证错误，您已被封禁\n\nVerification failed.You have been banned.')
            await client.block_user(user_id=cid)
            await asyncio.sleep(random.randint(0, 100) / 1000)
            await client.archive_chats(chat_ids=cid)
            data['banned'] = data.get('banned',0) + 1
            sqlite['pmcaptcha'] = data


@listener(is_plugin=True, outgoing=True, command="pmcaptcha",
          need_admin=True,
          description='一个简单的私聊人机验证  请使用 ,pmcaptcha h 查看可用命令')
async def pm_captcha(client: Client, message: Message):
    cid_ = str(message.chat.id)
    data = sqlite.get("pmcaptcha", {})
    if len(message.parameter) == 0:
        if message.chat.type != ChatType.PRIVATE:
            await message.edit('请在私聊时使用此命令，或添加参数执行')
            await asyncio.sleep(3)
            await message.safe_delete()
        if captcha_success.check_id(message.chat.id):
            text = "已验证用户"
        else:
            text = "未验证/验证中用户"
        await message.edit(text)
    elif len(message.parameter) == 1:
        if message.parameter[0] == "bl":
            await message.edit(
                '当前黑名单规则:\n' + str(data.get('blacklist', '无')) + '\n如需编辑，请使用 ,pmcaptcha bl +关键词（英文逗号分隔）')
        elif message.parameter[0] == 'wel':
            await message.edit(
                '当前通过时消息规则:\n' + str(data.get('welcome', '无')) + '\n如需编辑，请使用 ,pmcaptcha wel +要发送的消息')
        elif message.parameter[0] == 'wait':
            await message.edit(
                '当前验证等待时间(秒): ' + str(data.get('wait', '无')) + '\n如需编辑，请使用 ,pmcaptcha wait +等待秒数(整数)')
        elif message.parameter[0] == 'h':
            await message.edit(''',pmcaptcha
查询当前私聊用户验证状态

,pmcaptcha check id
查询指定id用户验证状态

,pmcaptcha add [id]
将id加入已验证，如未指定为当前私聊用户id

,pmcaptcha del [id]
移除id验证记录，如未指定为当前私聊用户id

,pmcaptcha wel [message]
查看或设置验证通过时发送的消息
使用 ,pmcaptcha wel -clear 可恢复默认规则

,pmcaptcha bl [list]
查看或设置关键词黑名单列表（英文逗号分隔）
使用 ,pmcaptcha bl -clear 可恢复默认规则

,pmcaptcha wait [int]
查看或设置超时时间

,pmcaptcha disablepm [true/false]
启用/禁止陌生人私聊
此功能会放行联系人和白名单(已通过验证)用户
您可以使用 ,pmcaptcha add 将用户加入白名单

,pmcaptcha stats
查看验证计数器
使用 ,pmcaptcha stats -clear 可重置
''')
        elif message.parameter[0] == 'disablepm':
            if data.get('disable',False):
                status='开启'
            else:
                status='关闭'
            await message.edit('当前禁止私聊状态: 已'+status+
                               '\n如需修改 请使用 ,pmcaptcha disablepm true/false'+
                               '\n此功能会放行联系人和白名单(已通过验证)用户')
        elif message.parameter[0] == 'stats':
            t = str(data.get('banned',0)+data.get('pass',0))
            await message.edit('自上次重置起，已进行验证 '+str(data.get('pass',0)+data.get('banned',0))+
            ' 次\n其中，通过验证 '+str(data.get('pass',0))+' 次，拦截 '+str(data.get('banned',0))+' 次')
        elif message.chat.type != ChatType.PRIVATE:
            await message.edit('请在私聊时使用此命令，或添加id参数执行')
            await asyncio.sleep(3)
            await message.safe_delete()
        elif message.parameter[0] == 'add':
            await message.edit('已将id ' + cid_ + ' 添加至白名单')
            captcha_success.add_id(message.chat.id)
        elif message.parameter[0] == 'del':
            if captcha_success.del_id(message.chat.id):
                await message.edit('已删除id ' + cid_ + ' 的验证记录')
            else:
                await message.edit('记录不存在')
    else:
        if message.parameter[0] == 'add':
            if message.parameter[1].isnumeric():
                await message.edit('已将id ' + message.parameter[1] + ' 添加至白名单')
                captcha_success.add_id(int(message.parameter[1]))
                await client.unarchive_chats(chat_ids=int(message.parameter[1]))
            else:
                await message.edit('参数错误')
        elif message.parameter[0] == 'del':
            if message.parameter[1].isnumeric():
                if captcha_success.del_id(int(message.parameter[1])):
                    await message.edit('已删除id ' + message.parameter[1] + ' 的验证记录')
                else:
                    await message.edit('记录不存在')
            else:
                await message.edit('参数错误')
        elif message.parameter[0] == 'wel':
            if message.parameter[1]=='-clear':
                if data.get("welcome", False):
                    del data["welcome"]
                    sqlite["pmcaptcha"] = data
                await message.edit('已恢复至默认规则')
                return
            data["welcome"] = " ".join(message.parameter[1:])
            sqlite["pmcaptcha"] = data
            await message.edit('规则已更新')
        elif message.parameter[0] == 'wait':
            if message.parameter[1].isnumeric():
                data["wait"] = int(message.parameter[1])
                sqlite["pmcaptcha"] = data
                await message.edit('等待时间已更新')
            else:
                await message.edit('错误:不是整数')
        elif message.parameter[0] == 'bl':
            if message.parameter[1]=='-clear':
                if data.get("blacklist", False):
                    del data["blacklist"]
                    sqlite["pmcaptcha"] = data
                await message.edit('已恢复至默认规则')
                return
            data["blacklist"] = " ".join(message.parameter[1:])
            sqlite["pmcaptcha"] = data
            await message.edit('规则已更新')
        elif message.parameter[0] == 'check':
            if message.parameter[1].isnumeric():
                if captcha_success.check_id(int(message.parameter[1])):
                    await message.edit('id ' + message.parameter[1] + ' 已验证')
                else:
                    await message.edit('id ' + message.parameter[1] + ' 未验证')
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
