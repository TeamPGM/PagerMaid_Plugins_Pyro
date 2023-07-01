from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient
from pagermaid.utils import lang


@listener(command="hitokoto", description=lang("hitokoto_des"))
async def hitokoto(request: AsyncClient, message: Message):
    hitokoto_while = 1
    hitokoto_json = None
    try:
        hitokoto_json = (
            await request.get("https://v1.hitokoto.cn/?charset=utf-8")
        ).json()
    except ValueError:
        while hitokoto_while < 10:
            hitokoto_while += 1
            try:
                hitokoto_json = (
                    await request.get("https://v1.hitokoto.cn/?charset=utf-8")
                ).json()
                break
            except Exception:
                continue
        if not hitokoto_json:
            return
    hitokoto_type = {
        "a": lang("hitokoto_type_anime"),
        "b": lang("hitokoto_type_manga"),
        "c": lang("hitokoto_type_game"),
        "d": lang("hitokoto_type_article"),
        "e": lang("hitokoto_type_original"),
        "f": lang("hitokoto_type_web"),
        "g": lang("hitokoto_type_other"),
        "h": lang("hitokoto_type_movie"),
        "i": lang("hitokoto_type_poem"),
        "j": lang("hitokoto_type_netease_music"),
        "k": lang("hitokoto_type_philosophy"),
        "l": lang("hitokoto_type_meme"),
    }
    add = ""
    if works := hitokoto_json["from"]:
        add += f"《{works}》"
    if works_type := hitokoto_json["type"]:
        add += f"（{hitokoto_type[works_type]}）"
    if from_who := hitokoto_json["from_who"]:
        add += f"{from_who}"
    await message.edit(f"{hitokoto_json['hitokoto']} {add}")
