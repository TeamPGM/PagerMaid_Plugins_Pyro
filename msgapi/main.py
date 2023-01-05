from http.server import HTTPServer, BaseHTTPRequestHandler
from json import dumps
from threading import Thread
from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient
from pagermaid.single_utils import sqlite

config = sqlite.get(
    "msgapi", {"chat": [], "port": 51419, "path": "", "webhook": "off"})
recv = '{"code": 1, "chat": 0, "message": "\\u6682\\u65e0\\u6d88\\u606f"}'
pathwarn = "\n警告:未设置访问路径 使用 ,msgapi path 进行设置" if config[
    "path"] == "" and config["webhook"] == "off" else ""


class Resquest(BaseHTTPRequestHandler):
    timeout = 5

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        buf = recv if self.path == "/"+config["path"] else '{"code": 250, "chat": 114514, "message": "\\u626b\\u4f60\\u5417\\u5462"}'  # 指端口(
        self.wfile.write(buf.encode())


class httpd (Thread):
    __server = HTTPServer(("0.0.0.0", config["port"]), Resquest)

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        self.__server.serve_forever()


d = httpd()
if config["webhook"] == "off":
    if config["path"] != "":
        d.start()


@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=False)
async def listen(message: Message, request: AsyncClient):
    global recv
    if message.chat.id not in config["chat"]:
        return
    recv = dumps(
        {"code": 0, "chat": message.chat.id, "message": message.text})
    if config["webhook"] != "off":
        try:
            await request.get(config["webhook"].replace("#MSGAPI", recv))
        except:
            pass


@listener(command="msgapi", description="获取消息简易web api", need_admin=True, parameters=f"add/del [id] 添加/移除当前会话至列表或指定id\nlist 获取会话id列表\nport [端口号] 设置服务端口,默认51419\npath [路径(开头无需加'/')] 访问路径,安全原因必须设置{pathwarn}\nwebhook [url] 启用后会关闭http服务,关闭填off")
async def msgapi(message: Message):
    global config
    if not message.arguments:
        await message.edit(f"Server listen on 0.0.0.0:{config['port']}{pathwarn}" if config["webhook"] == "off" else f"webhook url {config['webhook']}")
        return
    if message.parameter[0] == "list":
        await message.edit(str(config["chat"])+pathwarn)
        return
    if message.parameter[0] == "path" and len(message.parameter) == 2:
        config["path"] = message.parameter[1]
        sqlite["msgapi"] = config
        await message.edit(f"路径已设置为 /{config['path']}{'重启Pagermaid生效' if config['path'] == '' else ''}")
    elif message.parameter[0] == "webhook":
        if len(message.parameter) == 2:
            config["webhook"] = message.parameter[1]
            sqlite["msgapi"] = config
            await message.edit(f"已设置webhook为 {config['webhook']}{'重启Pagermaid生效' if config['webhook'] == 'off' else ''}")
        else:
            await message.edit(f"使用webhook [url] 设置url,收到消息会对其发送get请求,消息部分使用 #MSGAPI 替换,或填入 off 关闭\n如 ,msgapi webhook https://example.com/webhook?message=#MSGAPI ")
    elif message.parameter[0] == "add" or "del":
        cid = [message.chat.id] if len(
            message.parameter) == 1 else message.parameter[1:]
        msg=""
        for i in cid:
            try:
                i = int(i)
            except:
                msg+=f"{i} 无效id\n"
                continue
            if message.parameter[0] == 'add':
                if i in config["chat"]:
                    msg+=(f"{i} 已在列表\n")
                else:
                    config["chat"].append(i)
                    msg+=(f"{i} 添加成功\n")
            elif message.parameter[0] == 'del':
                try:
                    config["chat"].remove(i)
                except:
                    pass
                msg=(f"{str(cid)}已成功移除")
        sqlite["msgapi"] = config
        await message.edit(msg+pathwarn)
    elif message.parameter[0] == "port" and len(message.parameter) == 2:
        if message.parameter[1].isnumeric() is False:
            await message.edit("无效端口号"+pathwarn)
            return
        port = int(message.parameter[1])
        if 0 < port < 65536:
            config["port"] = port
            sqlite["msgapi"] = config
            await message.edit(f"已设置端口号为{message.parameter[1]},重启Pagermaid后生效"+pathwarn)
        else:
            await message.edit("无效端口号"+pathwarn)
            return
    else:
        await message.edit("无效命令"+pathwarn)
