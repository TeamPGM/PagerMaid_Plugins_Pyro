"""
自动回复Emoji插件
Author: SuperManito
"""

from pagermaid import bot, log
from pagermaid.single_utils import sqlite
from pagermaid.enums import Client, Message
from pagermaid.utils import lang, edit_delete, pip_install
from pagermaid.listener import listener

pip_install("emoji")

import emoji


# 获取内容中的表情符号，并用|分割
def get_emoji(text):
    emojiArr = emoji.distinct_emoji_list(text)
    if emojiArr:
        delimiter = '|'
        return delimiter.join(emojiArr)
    else:
        return False


@listener(is_plugin=False,
          outgoing=True,
          command="auto_send_reactions",
          description='\n自动回复Emoji插件',
          parameters="`\n自动回复Emoji插件，支持同时设置多个目标生效用户，目前仅支持回复用户在群组中发送的消息，默认在所有已加入的群组中生效\n"
          "\n**设置插件状态**:"
          "\n启用：`,auto_send_reactions enable`"
          "\n停用：`,auto_send_reactions disable`"
          "\n\n**设置目标生效用户**:"
          "\n添加：`,auto_send_reactions set <用户id/用户名> <表情内容>`"
          "\n移除：`,auto_send_reactions unset <用户id/用户名>`"
          "\n支持直接回复消息以进行快速设置，可以省略用户标识参数"
          "\n\n**设置生效群组黑名单**:"
          "\n添加：`,auto_send_reactions block <群组id/群组用户名>`"
          "\n移除：`,auto_send_reactions unblock <群组id/群组用户名>\n")
async def AutoSendReactions(client: Client, message: Message):
    reply = message.reply_to_message

    # 启用插件
    if message.parameter[0] == "enable":
        # for ID in ID_FROM_ARRAY :
        #     # 检查来源频道/群组
        #     try:
        #         channel = await bot.get_chat(ID)
        #     except Exception as e:
        #         errorMsg = f"第{e.__traceback__.tb_lineno}行：{e}"
        #         await message.edit(f"出错了呜呜呜 ~ 无法识别的来源对话。\n\n{errorMsg}")
        #         return

        if not sqlite.get(f"AutoSendReactions.Enable"):
            sqlite[f"AutoSendReactions.Enable"] = 'yes'

        # 返回消息
        await edit_delete(message, "✅ **已启用自动回复表情插件**")

    ## 停用插件
    elif message.parameter[0] == "disable":

        if sqlite.get(f"AutoSendReactions.Enable"):
            del sqlite[f"AutoSendReactions.Enable"]

        # 返回消息
        await edit_delete(message, "❌ **已停用自动回复表情插件**")

    elif (message.parameter[0] == "set") or (message.parameter[0] == "unset"):

        ## 设置插件
        if (message.parameter[0] == "set"):

            if not reply and (len(message.parameter) == 3):
                target = message.parameter[1]
                content = message.parameter[2]
                try:
                    # 获取用户信息
                    user_info = await bot.get_users(target)
                    # 判断参数合法性
                    if not user_info:
                        return await message.edit(f"❌ **目标用户不存在或参数有误**")
                    if not content or not get_emoji(content):
                        return await message.edit(f"❌ **Emoji参数不能为空或不合法**")
                    user_name = user_info.first_name + ' ' + user_info.last_name if user_info.last_name else user_info.first_name
                    # 设置或更新
                    hasSetted = sqlite.get(f"AutoSendReactions.{target}")
                    sqlite[f"AutoSendReactions.{target}"] = content
                    await edit_delete(
                        message,
                        f"✅ 已{'更新' if hasSetted else '添加'}对 __{user_name}__ 的自动回复Emoji设置**"
                    )
                except Exception as e:
                    await message.edit(message, f"❌ **在设置中遇到了一些错误** > {e}")
                    await log(e)  # 打印错误日志

            elif reply and (len(message.parameter) == 2):
                from_user = reply.from_user
                target = from_user.id
                content = message.parameter[1]
                try:
                    # 判断参数合法性
                    if not content or not get_emoji(content):
                        return await message.edit(f"❌ **Emoji参数不能为空或不合法**")
                    user_name = from_user.first_name + ' ' + from_user.last_name if from_user.last_name else from_user.first_name
                    # 设置或更新
                    hasSetted = sqlite.get(f"AutoSendReactions.{target}")
                    sqlite[f"AutoSendReactions.{target}"] = content
                    await edit_delete(
                        message,
                        f"✅ 已{'更新' if hasSetted else '添加'}对 __{user_name}__ 的自动回复Emoji设置"
                    )
                except Exception as e:
                    await message.edit(message, f"❌ **在设置中遇到了一些错误** > {e}")
                    await log(e)  # 打印错误日志
            else:
                return await message.edit(
                    f"{lang('error_prefix')}{lang('arg_error')}")

        ## 取消设置插件
        elif (message.parameter[0] == "unset"):

            if not reply and (len(message.parameter) == 2):
                target = message.parameter[1]
                try:
                    # 获取用户信息
                    user_info = await bot.get_users(target)
                    # 判断参数合法性
                    if not user_info:
                        return await message.edit(f"❌ **目标用户不存在或参数有误**")
                    user_id = user_info.id
                    user_name = user_info.first_name + ' ' + user_info.last_name if user_info.last_name else user_info.first_name
                    # 取消设置
                    hasSetted = sqlite.get(f"AutoSendReactions.{user_id}")
                    if hasSetted:
                        del sqlite[f"AutoSendReactions.{user_id}"]
                        await edit_delete(
                            message, f"✅ 对 __{user_name}__ 的自动回复Emoji设置已删除")
                    else:
                        await edit_delete(
                            message, f"❌ 还没有对 __{user_name}__ 设置自动回复Emoji哦~")
                except Exception as e:
                    await message.edit(message, f"❌ **在设置中遇到了一些错误** > {e}")
                    await log(e)  # 打印错误日志

            elif reply and (len(message.parameter) == 1):
                from_user = reply.from_user
                target = from_user.id
                try:
                    user_name = from_user.first_name + ' ' + from_user.last_name if from_user.last_name else from_user.first_name
                    # 取消设置
                    hasSetted = sqlite.get(f"AutoSendReactions.{target}")
                    if hasSetted:
                        del sqlite[f"AutoSendReactions.{target}"]
                        await edit_delete(
                            message, f"✅ 已删除对 __{user_name}__ 的自动回复Emoji设置")
                    else:
                        await edit_delete(
                            message, f"❌ 还没有对 __{user_name}__ 设置自动回复Emoji哦~")
                except Exception as e:
                    await message.edit(message, f"❌ **在设置中遇到了一些错误** > {e}")
                    await log(e)  # 打印错误日志
            else:
                return await message.edit(
                    f"{lang('error_prefix')}{lang('arg_error')}")

        else:
            return await message.edit(
                f"{lang('error_prefix')}{lang('arg_error')}")

    ## 设置/取消设置黑名单
    elif (message.parameter[0]
          == "block") or (message.parameter[0] == "unblock") and (len(
              message.parameter) == 2):
        group = message.parameter[1]
        group_info = await bot.get_chat(chat_id=group)
        if not group_info:
            return await message.edit(f"❌ **目标群组不存在或参数有误**")
        group_id = group_info.id
        group_name = group_info.title

        if (message.parameter[0] == "block"):
            hasBlocked = sqlite.get(f"AutoSendReactionsBlock.{group_id}")
            if hasBlocked:
                await edit_delete(
                    message, f"❌ 已经将 __{group_name}__ 加入自动回复Emoji黑名单群组了哦~")
            else:
                sqlite[f"AutoSendReactionsBlock.{group_id}"] = 'yes'
                await edit_delete(message,
                                  f"✅ 已将 __{group_name}__ 加入至自动回复Emoji黑名单群组")
        elif (message.parameter[0] == "unblock"):
            hasBlocked = sqlite.get(f"AutoSendReactionsBlock.{group_id}")
            if hasBlocked:
                del sqlite[f"AutoSendReactionsBlock.{group_id}"]
                await edit_delete(message,
                                  f"✅ 已将 __{group_name}__ 从自动回复Emoji黑名单群组中移除")
            else:
                await edit_delete(
                    message, f"❌ 还没有将 __{group_name}__ 加入进自动回复Emoji群组黑名单哦~")

    else:
        return await message.edit(f"{lang('error_prefix')}{lang('arg_error')}"
                                  )


@listener(is_plugin=False, incoming=True, ignore_edited=True)
async def AutoSendReactions(message: Message):
    from_user = ''
    try:
        # 判断是否启用了本插件
        if not sqlite.get(f"AutoSendReactions.Enable"):
            return
        # # 判断消息类型是否为群组（仅在群组生效）
        if 'GROUP' not in str(message.chat.type):
            return
        else:
            # 判断是否在黑名单中
            if sqlite.get(f"AutoSendReactionsBlock.{message.chat.id}"):
                return
        # 判断目标用户是否在名单中
        if message.from_user:
            from_user = message.from_user
            if not sqlite.get(f"AutoSendReactions.{from_user.id}"):
                return
        else:
            # 过滤匿名管理员
            return

        # 判断群组是否启用了表情回应功能
        group_info = await bot.get_chat(chat_id=message.chat.id)
        if group_info.available_reactions:
            if not group_info.available_reactions:
                return
            # if not message.allow_custom_emoji:
            #     return
        else:
            return

        # 发送表情
        emoji = sqlite.get(f"AutoSendReactions.{from_user.id}").split('|')[0]
        user_name = from_user.first_name + ' ' + from_user.last_name if from_user.last_name else from_user.first_name
        try:
            await bot.send_reaction(message.chat.id, message.id, emoji)

        except Exception as e:
            errorMsg = f"❌ 自动回复Emoji失败（{user_name} {emoji}）> {e}"
            await log(errorMsg)
            return False

        # 打印日志
        # text = message.text.markdown
        # await log(f"AutoSendReactions 监控到来自 {user_name} 的消息：{str(text)}")

    except Exception as e:
        errorMsg = f"❌ 第{e.__traceback__.tb_lineno}行：{e}"
        await log(errorMsg)
        return False


## ⬆️ 不懂勿动 ⬆️
