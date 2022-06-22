from pagermaid.listener import listener
from pagermaid.utils import Message, lang
from pagermaid.modules.prune import self_prune


@listener(is_plugin=False, command="dme",
          need_admin=True,
          description=lang('sp_des'),
          parameters=lang('sp_parameters'))
async def dme(message: Message):
    """ Deletes specific amount of messages you sent. """
    await self_prune(message)
