from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, lang, alias_command
from pagermaid.modules.prune import self_prune


@listener(is_plugin=False, outgoing=True, command=alias_command("dme"),
          need_admin=True,
          description=lang('sp_des'),
          parameters=lang('sp_parameters'))
async def dme(_: Client, message: Message):
    """ Deletes specific amount of messages you sent. """
    await self_prune(_, message)
