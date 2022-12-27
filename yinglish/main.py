import random
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.utils import pip_install

pip_install("jieba")

import jieba
import jieba.posseg as pseg

jieba.setLogLevel(20)


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
async def yinglish(context: Message):
    if not context.arguments:
        await context.edit("你没说话我转换个啥")
    else:
        outputtext = chs2yin(context.arguments)
        await context.edit(f"{outputtext}")
