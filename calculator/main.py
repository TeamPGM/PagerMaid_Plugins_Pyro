from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, execute


@listener(command="cal",
          description="计算\n示例：\n`-cal 1+1`加法\n`-cal 2-1`减法\n`-cal 1*2`乘法\n`-cal 4/2`除法\n`-cal 4^2`幂运算\n`-cal sqrt(4)`开方",
          parameters="<基本运算>")
async def cal(_: Client, message: Message):
    command = message.arguments
    if not command:
        await message.edit("`出错了呜呜呜 ~ 无效的参数。`")
        return

    await message.edit(f"{command}")
    cmd = f'echo "scale=4;{command}" | bc'
    result = await execute(cmd)

    if result:
        await message.edit(f"{command}=\n`{result}`")
    else:
        return

@listener(command="con",
          description="换算\n示例：\n`-con 2 99`将99转换为2进制",
          parameters="<进制(数字)> <数值>")
async def con(_: Client, message: Message):
    command = message.arguments.split()
    if not command:
        await message.edit("`出错了呜呜呜 ~ 无效的参数。`")
        return

    obase = command[0].upper().strip()
    num = command[1].upper().strip()
    await message.edit(f"{num}")
    cmd = f'echo "obase={obase};{num}" | bc'
    result = await execute(cmd)

    if result:
        await message.edit(f"{num}=\n`{result}`\n{obase}进制")
    else:
        return
