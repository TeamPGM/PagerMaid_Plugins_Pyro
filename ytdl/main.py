import contextlib
import os
import pathlib
import shutil

from concurrent.futures import ThreadPoolExecutor

from pagermaid.listener import listener
from pagermaid.utils import pip_install, lang
from pagermaid.enums import Message
from pagermaid.services import bot

pip_install("yt-dlp", version="==2022.9.1", alias="yt_dlp")

import yt_dlp


ytdl_is_downloading = False


def ytdl_download(url) -> dict:
    response = {"status": True, "error": "", "filepath": []}
    output = pathlib.Path("data/ytdl", "%(title).70s.%(ext)s").as_posix()
    ydl_opts = {
        'outtmpl': output,
        'restrictfilenames': False,
        'quiet': True
    }
    formats = [
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio",
        "bestvideo[vcodec^=avc]+bestaudio[acodec^=mp4a]/best[vcodec^=avc]/best",
        None
    ]
    if url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/"):
        formats.insert(0, "bestvideo[ext=mp4]+bestaudio[ext=m4a]")

    for format_ in formats:
        ydl_opts["format"] = format_
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            response["status"] = True
            response["error"] = ""
            break
        except Exception as e:
            response["status"] = False
            response["error"] = str(e)

    if response["status"] is False:
        return response

    for i in os.listdir("data/ytdl"):
        p = pathlib.Path("data/ytdl", i)
        response["status"] = True
        response["filepath"].append(p)

    return response


async def start_download(message: Message, url: str):
    global ytdl_is_downloading
    cid = message.chat.id
    executor = ThreadPoolExecutor()
    try:
        result = await bot.loop.run_in_executor(executor, ytdl_download, url)
    except Exception as e:
        result = {"status": False, "error": str(e)}
    if result["status"]:
        with contextlib.suppress(Exception):
            message: Message = await message.edit("文件上传中，请耐心等待。。。")
        for file in result["filepath"]:
            st_size = os.stat(file).st_size
            if st_size > 2 * 1024 * 1024 * 1024 * 0.99:
                result["status"] = False
                result['error'] = "文件太大，无法发送"
                continue
            try:
                await bot.send_video(cid, video=file, supports_streaming=True)
            except Exception:
                try:
                    await bot.send_document(cid, document=file, force_document=True)
                except Exception as e:
                    result["status"] = False
                    result["error"] = str(e)
    else:
        with contextlib.suppress(Exception):
            await message.edit(f"下载/发送文件失败，发生错误：{result['error']}")
    ytdl_is_downloading = False
    with contextlib.suppress(Exception):
        shutil.rmtree("data/ytdl")
    if result["status"]:
        await message.safe_delete()


@listener(command="ytdl",
          description="Upload Youtube、Bilibili video to telegram",
          parameters="<url>")
async def ytdl(message: Message):
    global ytdl_is_downloading
    if not message.arguments:
        return await message.edit(lang("arg_error"))
    if ytdl_is_downloading:
        return await message.edit("有一个下载任务正在运行中，请不要重复使用命令。")
    ytdl_is_downloading = True
    with contextlib.suppress(Exception):
        shutil.rmtree("data/ytdl")
    url = message.arguments
    message: Message = await message.edit("文件开始后台下载，下载速度取决于你的服务器。\n请<b>不要删除此消息</b>并且耐心等待！！！")
    bot.loop.create_task(start_download(message, url))
