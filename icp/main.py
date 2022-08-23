import time
import hashlib
from random import randint

from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import client as requests
from pagermaid.utils import pip_install

pip_install("tld")

from tld import get_fld


async def post_data(path, data, content, token):
    url = 'https://hlwicpfwc.miit.gov.cn/icpproject_query/api/'
    client_ip = f'{str(randint(1, 254))}.{str(randint(1, 254))}.{str(randint(1, 254))}.{str(randint(1, 254))}'
    headers = {
        'Content-Type': content,
        'Origin': 'https://beian.miit.gov.cn/',
        'Referer': 'https://beian.miit.gov.cn/',
        'token': token,
        'Client-IP': client_ip,
        'X-Forwarded-For': client_ip
    }
    return await requests.post(url + path, data=data, headers=headers)


async def icp_search(domain):
    md5 = hashlib.md5()
    timestamp = int(time.time())
    auth_key = f'testtest{timestamp}'
    md5.update(auth_key.encode('utf-8'))
    auth_key = md5.hexdigest()
    token = await post_data(
        'auth',
        f'authKey={auth_key}&timeStamp={timestamp}',
        'application/x-www-form-urlencoded;charset=UTF-8',
        '0',
    )
    token = token.json()
    if token.get("code", None) == 200:
        token = token['params']['bussiness']
    else:
        return {'isBeian': False, 'msg': '获取token失败'}

    query = await post_data('icpAbbreviateInfo/queryByCondition', '{"pageNum":"","pageSize":"","unitName":"%s"}' % (
        domain), 'application/json;charset=UTF-8', token)
    query = query.json()
    if query.get("code", None) != 200:
        return {'isBeian': False, 'msg': '查询失败'}
    icp_list = query['params']['list']
    if len(icp_list) <= 0:
        return {'isBeian': False, 'msg': '成功'}
    return {'isBeian': True, 'msg': '成功', 'data': icp_list[0]}


@listener(command="icp",
          parameters="<域名>",
          description="查询域名是否已备案")
async def icp_bei_an(message: Message):
    url = None
    if message.arguments:
        url = message.arguments
    elif message.reply_to_message:
        url = message.reply_to_message.text
    if not url:
        return await message.edit("请输入或回复一个域名或链接。")
    try:
        url = get_fld(url, fix_protocol=True)
        message: Message = await message.edit(f"查询中...{url}")
    except Exception:
        return await message.edit("出错了呜呜呜 ~ 无效的参数。")
    try:
        data = await icp_search(url)
    except Exception as e:
        return await message.edit(f"出错了呜呜呜 ~ 查询失败。{e}")

    if data.get("isBeian", False):
        data = data.get("data", {})
        await message.edit(
            f"域名： {url}\n"
            f"主体： {data.get('unitName', '')}\n"
            f"备案时间： {data.get('updateRecordTime', '')}\n"
            f"备案类型： {data.get('natureName', '')}\n"
            f"备案号： {data.get('serviceLicence', '')}\n"
            f"是否限制访问： {data.get('limitAccess', '')}")
    elif data.get("msg", "") == "成功":
        await message.edit(f"域名 {url} 未备案！")
    else:
        await message.edit("出错了呜呜呜 ~ " + data.get("msg", "") + "。")
