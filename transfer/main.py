import zipfile
import os
from os.path import exists, isfile

from pagermaid.enums import Client, Message
from pagermaid.listener import listener


async def make_zip(source_dir, output_filename):
    zipf = zipfile.ZipFile(output_filename, "w")
    pre_len = len(os.path.dirname(source_dir))
    for parent, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            pathfile = os.path.join(parent, filename)
            arcname = pathfile[pre_len:].strip(os.path.sep)
            zipf.write(pathfile, arcname)
    zipf.close()


@listener(command="transfer",
          description="上传 / 下载文件",
          parameters="upload [filepath]` 或 `download [filepath]")
async def transfer(bot: Client, message: Message):
    params = message.parameter
    if len(params) < 2:
        message: Message = await message.edit("参数缺失，请使用 `upload [filepath]` 或 `download [filepath]`")
        await message.delay_delete(3)
        return
    params[1] = " ".join(params[1:])
    file_list = params[1].split("\n")
    chat_id = message.chat.id
    if params[0] == "upload":
        index = 1
        for file_path in file_list:
            message: Message = await message.edit(f"正在上传第 {index} 个文件")
            if exists(file_path):
                if isfile(file_path):
                    await bot.send_document(chat_id, file_path, force_document=True)
                else:
                    token = file_path.split("/")
                    token = token[len(token) - 1]
                    await make_zip(file_path, f"/tmp/{token}.zip")
                    await bot.send_document(chat_id, f"/tmp/{token}.zip", force_document=True)
                    os.remove(f"/tmp/{token}.zip")
            index += 1
        message: Message = await message.edit("上传完毕")
    elif params[0] == "download":
        if reply := message.reply_to_message:
            message: Message = await message.edit('无法下载此类型的文件。')
            try:
                _file = await reply.download(in_memory=True)
            except Exception:
                await message.edit('无法下载此类型的文件。')
                return
            if not exists(file_list[0]):
                with open(file_list[0], "wb") as f:
                    f.write(_file.getvalue())
                message: Message = await message.edit(f"保存成功, 保存路径 `{file_list[0]}`")
            else:
                message: Message = await message.edit("路径已存在文件")
        else:
            message: Message = await message.edit("未回复消息或回复消息中不包含文件")
    else:
        message: Message = await message.edit("未知命令，请使用 `upload [filepath]` 或 `download [filepath]`")

    await message.delay_delete(3)
