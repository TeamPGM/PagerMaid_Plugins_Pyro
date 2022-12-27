from pyrogram import Client
import random
from sys import executable
from pagermaid.listener import listener
from pagermaid.utils import Message, execute

imported = True
try:
    import jieba
    import jieba.posseg as pseg

    jieba.setLogLevel(20)
except ImportError:
    imported = False


def chaos(x, y, chaosrate):
    if random.random() > chaosrate:
        return x
    if x in {'[', ']'}:
        return ''
    if x in {'，'}:
        return '…'
    if x in {'!', '！', }:
        return '‼‼‼'
    if x in {'。'}:
        return '❗'
    if len(x) > 1 and random.random() < 0.1:
        return f'{x[0]}…{x}'
    if len(x) > 1 and random.random() < 0.4:
        return f'{x[0]}♥{x}'
    if y == 'n' and random.random() < 0.1:
        x = '⭕' * len(x)
        return f'…{x}'
    if x in {'\……n', '\♥n'}:
        return '\n'
    if x in {'…………'}:
        return '……'
    if y == 'n' and random.random() < 0.2:
        x = '⭕' * len(x)
    return f'……{x}'


def chs2yin(s, chaosrate=0.8):
    return ''.join(chaos(x, y, chaosrate) for x, y in pseg.cut(s))


@listener(command="yinglish",
          description="能把中文和英文翻译成淫语的翻译机！")
async def yinglish(_: Client, context: Message):
    if not imported:
        try:
            await context.edit("支持库 `jieba` 未安装...\n正在尝试自动安装...")
            result: str = await execute(f'{executable} -m pip install jieba')
            if not result:
                await context.edit(
                    f"自动安装失败..请尝试手动安装 `{executable} -m pip install jieba` 随后，请重启 PagerMaid-Pyro 。")
            else:
                await context.edit("支持库 `jieba` 安装完成，请重启 PagerMaid-Pyro 。")
            return
        except:
            return
    if context.text and not context.via_bot and not context.arguments:
        await context.edit("你没说话我转换个啥")
    elif context.text and context.arguments and not context.via_bot:
        outputtext = chs2yin(context.arguments)
        await context.edit(f"{outputtext}")
        # await log(f"转换啦！从{context.parameter}变成了{str(outputtext)}!!!")
    else:
        await context.edit(context.arguments)
