""" QR Code related utilities. """

from PIL import Image
from pagermaid import log, Config
from pagermaid.enums import Client, Message
from pagermaid.listener import listener
from pagermaid.single_utils import safe_remove
from pagermaid.utils import lang, pip_install

pip_install("pyqrcode")
pip_install("pypng")
pip_install("pyzbar")

from pyqrcode import create


@listener(is_plugin=False, outgoing=True, command="genqr",
          description=lang('genqr_des'),
          parameters="[string]")
async def gen_qr(client: Client, message: Message):
    """ Generate QR codes. """
    text = message.obtain_message()
    if not text:
        await message.edit(lang('error_prefix'))
        return
    if not Config.SILENT:
        await message.edit(lang('genqr_process'))
    try:
        create(text, error="L", encoding="utf-8", mode="binary").png("qr.webp", scale=6)
        await client.send_document(
            message.chat.id,
            document="qr.webp",
            reply_to_message_id=message.reply_to_message_id or message.reply_to_top_message_id,
        )
    except UnicodeEncodeError:
        await message.edit(f"{lang('error_prefix')}{lang('genqr_e_encode')}")
        return
    except Exception as e:
        await message.edit(f"{lang('error_prefix')}\n{e}")
        return
    finally:
        safe_remove("qr.webp")
        await message.safe_delete()
        await log(f"`{text}` {lang('genqr_ok')}")


@listener(is_plugin=False, outgoing=True, command="parseqr",
          description=lang('parseqr_des'))
async def parse_qr(message: Message):
    """ Parse attachment of replied message as a QR Code and output results. """
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
    except ImportError:
        await message.edit(f"{lang('error_prefix')}请先在系统中安装 zbar 库。")
        return
    success = False
    reply = message.reply_to_message
    if message.document or message.photo or message.sticker:
        target_file_path = await message.download()
    elif reply and (reply.document or reply.photo or reply.sticker):
        target_file_path = await reply.download()
    else:
        return await message.edit(f"{lang('error_prefix')}{lang('parseqr_nofile')}")
    try:
        text = str(pyzbar_decode(Image.open(target_file_path))[0].data)[2:][:-1]
        success = True
        await message.edit(f"**{lang('parseqr_content')}: **\n"
                           f"`{text}`")
    except Exception:
        await message.edit(f"{lang('error_prefix')}{lang('parseqr_e_noqr')}")
        text = None
    finally:
        safe_remove(target_file_path)
    if success:
        await log(f"{lang('parseqr_log')} `{text}`.")
