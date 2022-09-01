import contextlib
import json

from asyncio import sleep

from pagermaid import log
from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import bot
from pagermaid.single_utils import sqlite
from pagermaid.utils import pip_install

pip_install("aiohttp")

import aiohttp


class WebSocket:
    def __init__(self):
        self.uri = sqlite.get("websocket_uri", "")
        self.loop = bot.loop
        self.client = aiohttp.ClientSession(loop=self.loop)
        self.need_stop = False
        self.ws = None
        self.connection = None

    @staticmethod
    def database_have_uri():
        return sqlite.get("websocket_uri", "") != ""

    def restore_uri(self):
        self.uri = sqlite.get("websocket_uri", "")

    async def set_uri(self, uri):
        await self.disconnect()
        self.uri = uri
        sqlite["websocket_uri"] = uri

    def is_connected(self):
        return self.connection is not None

    async def connect(self):
        if self.is_connected():
            await self.disconnect()
        if self.uri:
            self.ws = self.client.ws_connect(self.uri, autoclose=False, autoping=False, timeout=5)
            self.connection = await self.ws._coro

    async def disconnect(self):
        if self.connection:
            with contextlib.suppress(Exception):
                await self.connection.close()
            self.ws = None
            self.connection = None

    async def keep_alive(self):
        if not self.uri:
            return
        i = 0
        while i < 3:
            try:
                await self.connect()
            except Exception:
                i += 1
                if i == 3:
                    await log("[ws] Connection lost, reconnect 3 times failed...")
                await sleep(5)
                continue
            await self.get()
            i = 0
            if self.need_stop:
                await self.disconnect()
                self.need_stop = False
                break

    async def get(self):
        ws_ = self.connection
        if not ws_:
            return
        while True:
            msg = await ws_.receive()
            if msg.type == aiohttp.WSMsgType.TEXT:
                bot.loop.create_task(self.process_message(msg.data))
            elif msg.type == aiohttp.WSMsgType.PING:
                await ws_.pong()
            elif msg.type == aiohttp.WSMsgType.BINARY:
                pass
            elif msg.type != aiohttp.WSMsgType.PONG:
                if msg.type == aiohttp.WSMsgType.CLOSE:
                    await ws_.close()
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f"Error during receive {ws_.exception()}")
                break
        self.ws = None
        self.connection = None

    async def push(self, msg):
        if self.is_connected():
            await self.connection.send_str(msg)

    @staticmethod
    async def process_message(text: str):
        try:
            data = json.loads(text)
        except Exception:
            return
        action = data.get('action', None)
        action_data = data.get('data', None)

        bot_action = getattr(bot, action)
        if bot_action and action_data:
            await bot_action(**action_data)


ws = WebSocket()


@Hook.on_startup()
async def connect_ws():
    try:
        await ws.connect()
        bot.loop.create_task(ws.keep_alive())
    except Exception as e:
        await log(f"[ws] Connection failed: {e}")


@listener(incoming=True, outgoing=True)
async def websocket_push(message: Message):
    with contextlib.suppress(Exception):
        await ws.push(message.__str__())


@listener(command="websocket", description="Websocket Connect", parameters="<uri>")
async def websocket_to_connect(message: Message):
    if message.arguments:
        uri = message.arguments
        if not uri.startswith("ws://"):
            return await message.edit("[ws] 请输入正确的 uri ，例如：ws://127.0.0.1:1080/ws\n\n"
                                      "**请一定使用强路径并且连接到可信 ws ，ws 发送方能够对您的账户执行任意操作！！！**")
        msg: Message = await message.edit("[ws] Websocket 尝试连接中...")
        try:
            if ws.is_connected():
                ws.need_stop = True
            await ws.disconnect()
            await ws.set_uri(uri)
            await ws.connect()
        except Exception as e:
            return await msg.edit(f"[ws] 连接失败：{e}")
        await msg.edit("[ws] Websocket 连接成功")
        bot.loop.create_task(ws.keep_alive())
    elif not ws.is_connected():
        if not ws.database_have_uri():
            return await message.edit("[ws] ws 未链接，请输入正确的 uri ，例如：ws://127.0.0.1:1080/ws\n\n"
                                      "**请一定使用强路径并且连接到可信 ws ，ws 发送方能够对您的账户执行任意操作！！！**")
        ws.restore_uri()
        msg: Message = await message.edit("[ws] Websocket 尝试连接中...")
        try:
            await ws.connect()
        except Exception:
            return await msg.edit("[ws] 连接失败")
        await msg.edit("[ws] Websocket 连接成功")
        bot.loop.create_task(ws.keep_alive())
    else:
        return await message.edit("[ws] Websocket 已连接")
