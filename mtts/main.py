import json
import os
from pagermaid.listener import listener
from pagermaid.utils import Message, client
from pymtts import async_Mtts
from pyrogram import Client

CONFIG_PATH = os.path.join(os.getcwd(), "data", "mtts_config.json")
default_config = {
    "short_name": "zh-CN-XiaoxiaoNeural",
    "style": "general",
    "rate": 0,
    "pitch": 0,
    "kmhz": 24
}


async def config_check() -> dict:
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump(default_config, f)
        return default_config

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


async def config_set(configset, cmd) -> bool:
    config = await config_check()
    config[cmd] = configset
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
        return True
    return False


async def save_audio(buffer: bytes) -> str:
    with open(os.path.join(os.getcwd(), "data", "mtts.mp3"), "wb") as f:
        f.write(buffer)
        return os.path.join(os.getcwd(), "data", "mtts.mp3")


@listener(command="mtts", description="文本转语音",
          parameters="[str]\r\nmtts setname [str]\r\nmtts setstyle [str]\r\nmtts list [str]")
async def mtts(_: Client, msg: Message):
    opt = msg.arguments
    replied_msg = msg.reply_to_message
    cmtts = async_Mtts()
    if msg.parameter[0] == "setname":
        model_name = msg.parameter[1]
        status = await config_set(model_name, "short_name")
        if not status:
            await msg.edit("❗️ tts setting  error")
        await msg.edit(
            "successfully set up mtts voice model to:{}".format(model_name))
    elif msg.parameter[0] == "setstyle":
        model_name = msg.parameter[1]
        status = await config_set(model_name, "style")
        if not status:
            await msg.edit("❗️ tts setting  error")
        await msg.edit(
            "successfully set up mtts voice style to:{}".format(model_name))
    elif msg.parameter[0] == "list":
        tag = msg.parameter[1]
        voice_model = await cmtts.get_lang_models()
        s = "code | local name | Gender | LocaleName\r\n"
        for model in voice_model:
            if tag in model.ShortName or tag in model.Locale or tag in model.LocaleName:
                s += "{} | {} | {} | {}\r\n".format(model.ShortName,
                                                    model.LocalName,
                                                    model.Gender,
                                                    model.LocaleName)
        await msg.edit(s)
    elif opt is not None and opt != " " and opt != ' ':
        config = await config_check()
        mp3_buffer = await cmtts.mtts(text=opt,
                                      short_name=config["short_name"],
                                      style=config["style"],
                                      rate=config["rate"],
                                      pitch=config["pitch"],
                                      kmhz=config["kmhz"])
        mp3_path = await save_audio(mp3_buffer)

        if replied_msg is None:
            await msg.reply_voice(mp3_path)
            await msg.delete()
        else:
            await msg.reply_voice(
                mp3_path, reply_to_message_id=replied_msg["message_id"])
            await msg.delete()
    elif replied_msg is not None:
        config = await config_check()
        mp3_buffer = await cmtts.mtts(text=replied_msg["text"],
                                      short_name=config["short_name"],
                                      style=config["style"],
                                      rate=config["rate"],
                                      pitch=config["pitch"],
                                      kmhz=config["kmhz"])
        mp3_path = await save_audio(mp3_buffer)
        await msg.reply_voice(mp3_path,
                              reply_to_message_id=replied_msg["message_id"])
        await msg.delete()
    elif opt is None or opt == " ":
        await msg.edit("error, please use help command to show use case")
