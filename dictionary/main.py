""" PagerMaid Plugin to provide a dictionary lookup. """

from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.utils import pip_install, alias_command

pip_install("PyDictionary")

from PyDictionary import PyDictionary

dictionary_data = PyDictionary()


@listener(command="dictionary", parameters="[单词]", description="查询英语单词的意思")
async def get_word_mean(message: Message):
    """Look up a word in the dictionary."""
    word = message.arguments
    if not word:
        return await message.edit(
            f"[dictionary] 使用方法：`,{alias_command('dictionary')} <单词>`"
        )

    result = dictionary_data.meaning(word)
    output = f"<b>Word :</b> <i>{word}</i>\n\n"
    if result:
        try:
            for a, b in result.items():
                output += f"<b>{a}</b>\n"
                for i in b:
                    output += f"☞<i>{i}</i>\n"
            await message.edit(output)
        except Exception as e:
            await message.edit(f"[dictionary] 无法查询到单词的意思：{e}")
    else:
        await message.edit("[dictionary] 无法查询到单词的意思")
