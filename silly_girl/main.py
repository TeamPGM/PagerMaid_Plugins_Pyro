
from asyncio import sleep
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.single_utils import sqlite
from pagermaid.utils import client, edit_delete
from pagermaid import bot
from pyrogram.enums.chat_type import ChatType
from pagermaid.hook import Hook

import json

class SillyGirl:
    address = ""
    token = ""
    self_user_id = ""
    init = False
    working = False

    def init_connect_info(self, address):
        sillyGirl.self_user_id = bot.me.id
        self.init = True
        if address:
            sqlite["silly_girl_address"] = address
        else:
            address = sqlite.get("silly_girl_address")
        if '@' in address:
            s1 = address.split("//", 1)
            s2 = s1[1].split("@", 1)
            sillyGirl.token = s2[0]
            address = s1[0]+"//"+s2[1]
        sillyGirl.address = address

    async def polls(self):
        while True:
            await self.poll([])

    async def poll(self, data):
        try:
            init = ''
            if sillyGirl.init == False:
                init = "&init=true"
                sillyGirl.init = True
            req_data = await client.post(self.address+"/pgm?token="+self.token+init, json=data)
        except Exception as e:
            print(e)
            await sleep(0.1)
            return
        if not req_data.status_code == 200:
            await sleep(0.1)
            return
        try:
            replies = json.loads(req_data.text)
            results = []
            for reply in replies:
                if reply["delete"]:
                    try:
                        await bot.edit_message(reply["chat_id"], reply["id"], "打错字了，呱呱～")
                    except Exception as e:
                        pass
                    try:
                        await bot.delete_messages(reply["chat_id"], [reply["id"]])
                    except Exception as e:
                        pass
                if reply["id"] != 0:
                    try:
                        await bot.edit_message(reply["chat_id"], reply["id"], reply["text"])
                        continue
                    except Exception as e:
                        continue
                message: Message
                if reply["images"] and len(reply["images"]) != 0:
                    message = await bot.send_photo(
                        reply["chat_id"],
                        reply["images"][0],
                        caption=reply["text"],
                        reply_to_message_id=reply["reply_to"],
                    )
                elif reply["text"] != '':
                    
                    message = await bot.send_message(reply["chat_id"], reply["text"], reply_to_message_id=reply["reply_to"])
                if message:
                    results.append({
                        'id': message.id,
                        'uuid': reply["uuid"],
                    })
            if len(results):
                await sillyGirl.poll(results)
        except Exception as e:
            print(e)
            await sleep(0.1)
            return

sillyGirl = SillyGirl()

@Hook.on_startup()
async def connect_sillyGirl():
    sillyGirl.init_connect_info("")
    bot.loop.create_task(sillyGirl.polls())

    

@listener(is_plugin=True,outgoing=True, ignore_edited=True, command="sillyGirl",description="连接到傻妞服务器", parameters="<auth>")
async def Connect(message: Message):
    try:                   
        await edit_delete(message,"连接中...")
        sillyGirl.init_connect_info(message.arguments)
    except Exception as e:
        print(e)
        pass

@listener(outgoing=True,ignore_edited=True, incoming=True)
async def handle_receive(message: Message):
    try:                   
        reply_to = message.id
        reply = message.reply_to_message
        reply_to_sender_id = 0
        sender_id = 0
        if message.from_user :
            sender_id = message.from_user.id
            if reply:
                reply_to = reply.id
                reply_to_sender_id = reply.from_user.id
        if sillyGirl.init != True:
            sillyGirl.init_connect_info("")
        if sillyGirl.self_user_id == sender_id :
            reply_to = 0 
        await sillyGirl.poll(
        [{
            'id': message.id,
            'chat_id': message.chat.id,
            'text': message.text,
            'sender_id': sender_id,
            'reply_to': reply_to,
            'reply_to_sender_id': reply_to_sender_id,
            'bot_id': sillyGirl.self_user_id,
            'is_group': message.chat.type != ChatType.PRIVATE,
        }])
    except Exception as e:
        print(e)
        pass
    return

    