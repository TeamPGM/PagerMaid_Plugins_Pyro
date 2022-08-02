from pagermaid import Config, log
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.utils import lang, pip_install

pip_install("magic-google", alias="magic_google")

from magic_google import MagicGoogle


@listener(command="google",
          description=lang('google_des'),
          parameters="<query>")
async def google(message: Message):
    """ Searches Google for a string. """
    query = message.arguments
    if not query:
        return await message.edit(lang('arg_error'))
    mg = MagicGoogle()
    query = query.replace(' ', '+')
    if not Config.SILENT:
        message = await message.edit(lang('google_processing'))
    results = ""
    for i in mg.search(query=query, num=5):
        try:
            title = i['text'][:30] + '...'
            link = i['url']
            results += f"\n<a href=\"{link}\">{title}</a> \n"
        except Exception:
            return await message.edit(lang('google_connection_error'))
    await message.edit(f"<b>Google</b> |<code>{query}</code>| 🎙 🔍 \n{results}", disable_web_page_preview=True)
    await log(f"{lang('google_success')} `{query}`")
