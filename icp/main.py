from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import pip_install, Message, client

pip_install("requests")
pip_install("tld")

import time
import hashlib
import requests
from random import randint
from tld import get_fld

def post_data(path, data, content, token):
    url = 'https://hlwicpfwc.miit.gov.cn/icpproject_query/api/'
    clientIp = (
        (f'{str(randint(1, 254))}.{str(randint(1, 254))}' + '.')
        + str(randint(1, 254))
        + '.'
    ) + str(randint(1, 254))

    headers = {
        'Content-Type': content,
        'Origin': 'https://beian.miit.gov.cn/',
        'Referer': 'https://beian.miit.gov.cn/',
        'token': token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        'Client-IP': clientIp,
        'X-Forwarded-For': clientIp
    }
    return requests.post(url+path, data=data, headers=headers)


async def icp_search(domain):
    md5 = hashlib.md5()
    timeStamp = int(time.time())
    authKey = f'testtest{timeStamp}'
    md5.update(authKey.encode('utf-8'))
    authKey = md5.hexdigest()
    try:
        token = post_data(
            'auth',
            f'authKey={authKey}&timeStamp={timeStamp}',
            'application/x-www-form-urlencoded;charset=UTF-8',
            '0',
        )

        token = token.json()
        if(token['code'] == 200):
            token = token['params']['bussiness']
        else:
            # raise Exception({'isBeian': False, 'msg': '获取token失败'})
            return {'isBeian': False, 'msg': '获取token失败'}
    except Exception as e:
        return e
    try:
        query = post_data('icpAbbreviateInfo/queryByCondition', '{"pageNum":"","pageSize":"","unitName":"%s"}' % (
            domain), 'application/json;charset=UTF-8', token)
        query = query.json()
        if query['code'] != 200:
            # raise Exception({'isBeian': False, 'msg': '查询失败'})
            return{'isBeian': False, 'msg': '查询失败'}
        icpList = query['params']['list']
        if len(icpList) <= 0:
            # raise Exception({'isBeian': False, 'msg': '成功'})
            return{'isBeian': False, 'msg': '成功'}
        for icp in icpList:
            return{'isBeian': True, 'msg': '成功', 'natureName': icp['natureName'], 'limitAccess': icp['limitAccess'], 'unitName': icp['unitName'], 'serviceLicence': icp['serviceLicence'], 'updateRecordTime': icp['updateRecordTime']}
    except Exception as e:
        return e


@listener(command="beian",
          description="查看域名是否已备案")
async def beian(context: Message):
    try:
        if context.arguments:
            url = context.arguments
        elif context.reply_to_message:
            url = context.reply_to_message.text
        else:
            await context.edit("请输入或回复一个域名或链接。")
            return
        if url:
            url = get_fld(url, fix_protocol=True)
        else:
            await context.edit("出错了呜呜呜 ~ 无效的参数。")
        await context.edit(f"查询中...{url}")
    except ValueError:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    except tld.exceptions.FldBadUrl:
        await context.edit("出错了呜呜呜 ~ 无效的参数。")
        return
    try:
        data = await icp_search(url)
    except:
        await context.edit("出错了呜呜呜 ~ 查询失败。")
        return

    if data['isBeian']:
        await context.edit("域名已备案！\n\n" + "域名：" + url + "\n" + "主体：" + data['unitName'] + "\n" + "备案时间：" + data['updateRecordTime'] + "\n" + "备案类型：" + data['natureName'] + "\n" + "备案号：" + data['serviceLicence'] + "\n" + "是否限制访问：" + data['limitAccess'])
    elif data['msg'] == '成功':
        await context.edit("域名未备案！\n\n" + "域名：" + url)
    else:
        await context.edit("出错了呜呜呜 ~ " + data['msg']+"。")
