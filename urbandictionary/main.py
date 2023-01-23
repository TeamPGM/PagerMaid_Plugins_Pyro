from pagermaid.listener import listener
from pagermaid.enums import AsyncClient, Message
from pagermaid.utils import alias_command


@listener(command="urbandictionary",
          parameters="[单词]",
          description="解释英语俚语词汇")
async def get_urban_mean(message: Message, httpx: AsyncClient):
    """ To fetch meaning of the given word from urban dictionary. """
    word = message.arguments
    if not word:
        return await message.edit(f"[urbandictionary] 使用方法：`,{alias_command('urbandictionary')} <单词>`")

    try:
        response = (await httpx.get(f"https://api.urbandictionary.com/v0/define?term={word}")).json()
    except Exception as e:
        return await message.edit(f"[urbandictionary] API 接口无法访问：{e}")

    if len(response["list"]) == 0:
        return await message.edit("[urbandictionary] 无法查询到单词的意思")

    word = response["list"][0]["word"]
    definition = response["list"][0]["definition"]
    example = response["list"][0]["example"]
    result = f"**Word :** __{word}__\n\n" \
             f"**Meaning:**\n" \
             f"`{definition}`\n\n" \
             f"**Example:**\n" \
             f"`{example}`"
    await message.edit(result)
