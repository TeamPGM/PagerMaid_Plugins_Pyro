from pagermaid.listener import listener
from pagermaid.enums import Message, AsyncClient


@listener(command="netease_comment",
          description="随机一条网易云音乐评论。")
async def netease(request: AsyncClient, message: Message):
    for _ in range(5):
        try:
            req = await request.get("https://api.66mz8.com/api/music.163.php?format=json")
            assert req.status_code == 200
            data = req.json()
            res = data['comments'] + '\n\n来自 @' + data[
                'nickname'] + ' 在鸽曲 <a href="' + str(data['music_url']) + '">' + \
                  data['name'] + ' --by' + data['artists_name'] + '</a>' + ' 下方的评论。'
            return await message.edit(res, disable_web_page_preview=False)
        except Exception:
            continue
    await message.edit("出错了呜呜呜 ~ 无法访问到 API 服务器 。")
