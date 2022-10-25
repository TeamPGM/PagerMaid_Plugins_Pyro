import contextlib
import secrets

from pagermaid import bot, log
from pagermaid.utils import alias_command
from pagermaid.listener import listener
from pagermaid.single_utils import Message
from pagermaid.sub_utils import Sub
from pagermaid.scheduler import add_delete_message_job

lottery_bot = Sub("lottery_bot")
lottery_json = {"start": False, "chat_id": 0, "num": 0, "win": 0, "title": "", "keyword": ""}
create_text = """抽奖活动 <b>{}</b> 已经创建
奖品数量：<b>{}</b>
参与人数达到 <b>{}</b> 人，即可开奖

发送 <code>{}</code> 即可参与抽奖"""
join_text = """感谢参与 <b>{}</b> 抽奖活动
奖品数量：<b>{}</b>
参与人数达到 <b>{}</b> 人，即可开奖
当前参与人数：<b>{}</b> 人"""
end_text = """<b>{}</b> 已开奖，中奖用户：

{}

请私聊发起者领奖，感谢其他用户的参与。"""
end_empty_text = """<b>{}</b> 已开奖，没有中奖用户"""


async def lottery_end():
    lottery_json["start"] = False
    all_user = lottery_bot.get_subs()[:lottery_json["num"]]
    secret_generator = secrets.SystemRandom()
    win_user = []
    win_user_num = min(lottery_json["win"], len(all_user))
    while True:
        temp = secret_generator.choice(all_user)
        if temp not in win_user:
            win_user.append(temp)
        if len(win_user) >= win_user_num:
            break
    win_text = end_text.format(
        lottery_json["title"],
        "\n".join(f"<a href=\"tg://user?id={uid}\">@{uid}</a>" for uid in win_user
                  )) if win_user else end_empty_text.format(lottery_json["title"])
    with contextlib.suppress(Exception):
        await bot.send_message(lottery_json["chat_id"], win_text)
    with contextlib.suppress(Exception):
        await log(win_text)
    lottery_bot.clear_subs()


@listener(incoming=True, outgoing=True, groups_only=True)
async def handle_lottery(_, message: Message):
    if not message.from_user:
        return
    if message.from_user.is_bot:
        return
    if not message.text:
        return
    if not lottery_json["start"]:
        return
    if message.chat.id != lottery_json["chat_id"]:
        return
    if message.text != lottery_json["keyword"]:
        return
    if lottery_bot.check_id(message.from_user.id):
        return
    lottery_bot.add_id(message.from_user.id)
    all_join = len(lottery_bot.get_subs())
    if all_join > (lottery_json["num"]):
        lottery_json["start"] = False
        return await lottery_end()
    with contextlib.suppress(Exception):
        reply = await message.reply(
            join_text.format(
                lottery_json["title"],
                lottery_json["win"],
                lottery_json["num"],
                all_join))
        add_delete_message_job(reply, 15)
    if all_join >= lottery_json["num"]:
        lottery_json["start"] = False
        await lottery_end()


async def create_lottery(chat_id: int, num: int, win: int, title: str, keyword: str):
    if lottery_json["start"]:
        raise FileExistsError
    lottery_bot.clear_subs()
    lottery_json["start"] = True
    lottery_json["chat_id"] = chat_id
    lottery_json["num"] = num
    lottery_json["win"] = win
    lottery_json["title"] = title
    lottery_json["keyword"] = keyword
    with contextlib.suppress(Exception):
        await bot.send_message(chat_id, create_text.format(title, win, num, keyword))


@listener(command="lottery",
          groups_only=True,
          need_admin=True,
          parameters="<奖品数/人数> <关键词> <标题> / 强制开奖",
          description=f"举行抽奖活动\n\n例如：,{alias_command('lottery')} 1/10 测试 测试")
async def lottery(message: Message):
    if not message.arguments:
        return await message.edit(
            f"请输入 奖品数、人数等参数 或者 强制开奖\n\n例如 `,{alias_command('lottery')} 1/10 测试 测试`")
    if message.arguments == "强制开奖":
        await message.edit("强制开奖成功。")
        return await lottery_end()
    if len(message.parameter) < 3:
        return await message.edit("奖品数、人数、关键字和标题不能为空")
    num_list = message.parameter[0].split("/")
    if len(num_list) != 2:
        return await message.edit("奖品数、人数不能为空")
    try:
        num = int(num_list[1])
        win = int(num_list[0])
        if win > num:
            return await message.edit("奖品数不能超过人数")
    except ValueError:
        return await message.edit("人数必须是整数")
    keyword = message.parameter[1]
    title = message.parameter[2]
    if not (keyword and title):
        return await message.edit("奖品数、人数、关键字和标题不能为空")
    try:
        await create_lottery(message.chat.id, num, win, title, keyword)
        await message.safe_delete()
    except FileExistsError:
        return await message.edit("有抽奖活动正在进行，请稍后再试")
