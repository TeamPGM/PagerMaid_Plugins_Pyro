# -*- coding: utf-8 -*-

from typing import Optional, List, Dict, Tuple
from functools import reduce

from pyrogram.enums import MessageEntityType, ParseMode
from pyrogram.raw.functions.messages import SendReaction
from pyrogram.raw.types import ReactionEmoji, ReactionCustomEmoji, User
from pyrogram.types import MessageEntity

from pagermaid.listener import listener
from pagermaid.enums import Client, Message
from pagermaid.utils import sleep, pip_install
from pagermaid.single_utils import sqlite

pip_install("emoji")
import emoji

NATIVE_EMOJI = b'\xf0\x9f\x91\x8d\xf0\x9f\x91\x8e\xe2\x9d\xa4\xef\xb8\x8f\xf0\x9f\x94\xa5\xf0\x9f\xa5\xb0\xf0\x9f\x91\x8f\xf0\x9f\x98\x81\xf0\x9f\xa4\x94\xf0\x9f\xa4\xaf\xf0\x9f\x98\xb1\xf0\x9f\xa4\xac\xf0\x9f\x98\xa2\xf0\x9f\x8e\x89\xf0\x9f\xa4\xa9\xf0\x9f\xa4\xae\xf0\x9f\x92\xa9\xf0\x9f\x99\x8f\xf0\x9f\x91\x8c\xf0\x9f\x95\x8a\xf0\x9f\xa4\xa1\xf0\x9f\xa5\xb1\xf0\x9f\xa5\xb4\xf0\x9f\x98\x8d\xf0\x9f\x90\xb3\xe2\x9d\xa4\xef\xb8\x8f\xe2\x80\x8d\xf0\x9f\x94\xa5\xf0\x9f\x8c\x9a\xf0\x9f\x8c\xad\xf0\x9f\x92\xaf\xf0\x9f\xa4\xa3\xe2\x9a\xa1\xef\xb8\x8f\xf0\x9f\x8d\x8c\xf0\x9f\x8f\x86\xf0\x9f\x92\x94\xf0\x9f\xa4\xa8\xf0\x9f\x98\x90\xf0\x9f\x8d\x93\xf0\x9f\x8d\xbe\xf0\x9f\x92\x8b\xf0\x9f\x96\x95\xf0\x9f\x98\x88\xf0\x9f\x98\x82\xf0\x9f\x98\xad'.decode()
SPECIAL_EMOJI = "❤⬅↔➡⬆↕⬇" # TO BE ADDED
USAGE = f"""```Usage:
  Reply to a message:
    Trace      : .trace 👍👎🥰
    Untrace    : .trace
  Trace keyword: .trace kw add 👍👎🥰
  Del keyword  : .trace kw del

  List all   : .trace status
  Untrace all: .trace clean
  Keep log   : .trace log [true|false]
```
**Available native emojis:** {NATIVE_EMOJI}
"""

keep_log = True
cached_sqlite = {
    key: value for key, value in sqlite.items() if key.startswith("trace.")
}

async def edit_and_delete(message: Message, text: str, entities: List[MessageEntity]=[], seconds=5, parse_mode:ParseMode=ParseMode.DEFAULT):
    global keep_log
    await message.edit(text, entities=entities, parse_mode=parse_mode)
    if seconds == -1 or keep_log:
        return
    await sleep(seconds)
    return await message.delete()

async def print_usage(message: Message):
    return await edit_and_delete(message, USAGE, [], 15, ParseMode.MARKDOWN)

async def get_users_by_userids(client: Client, uids: List[int]) -> List[User]:
    return await client.get_users(uids)

async def get_all_traced(client: Client) -> Dict:
    uid_reactions = {
        int(key.split("trace.user_id.")[1]): {"reactions": value}
        for key, value in cached_sqlite.items()
        if key.startswith("trace.user_id.")
    }

    user_info = await get_users_by_userids(client, uid_reactions.keys())
    for user in user_info:
        uid_reactions[user.id]["user"] = user
    return uid_reactions

def count_offset(text: str) -> int:
    return sum(
        1
        if c in SPECIAL_EMOJI
        or c not in SPECIAL_EMOJI
        and not emoji.is_emoji(c)
        else 2
        for c in text
    )

def append_emoji_to_text(text: str, reaction_list: List[ReactionEmoji | ReactionCustomEmoji], entities: List[MessageEntity]):
    text += "["
    for reaction in reaction_list:
        if type(reaction) is ReactionEmoji:
            text += f"{reaction.emoticon}, "
        elif type(reaction) is ReactionCustomEmoji:
            entities.append(MessageEntity(
                type=MessageEntityType.CUSTOM_EMOJI,
                offset=count_offset(text),
                length=2,
                custom_emoji_id=reaction.document_id
            ))
            text += "👋, "
        else:  # Would it reach here?
            text += str(reaction)
    text = text[:-2] + "]\n"
    return text, entities

def get_keyword_emojis_from_message(message) -> Tuple[str, List[str|int]]:
    return (
        (message.parameter[0], get_emojis_from_message(message))
        if message
        else None
    )

def get_emojis_from_message(message: Message) -> List[str|int]:
    if not message:
        return None

    emoji_list = []
    index = 0
    entity_i = 0
    # Parse input to preserve order.
    # TODO: Can be more elegant
    for c in message.text:
        if len(emoji_list) == 3:
            break
        if emoji.is_emoji(c):
            if message.entities \
            and len(message.entities) - 1 >= entity_i \
            and message.entities[entity_i].type == MessageEntityType.CUSTOM_EMOJI \
            and message.entities[entity_i].offset == index:
                emoji_list.append(message.entities[entity_i].custom_emoji_id)
                entity_i += 1
            else:
                emoji_list.append(c)
            index += 2
            if c in SPECIAL_EMOJI:
                index -= 1
        else:
            index += 1
    return emoji_list

def get_name_and_username_from_message(message: Message):
    other_name = ""
    if message.reply_to_message.from_user.first_name:
        other_name += message.reply_to_message.from_user.first_name
    if message.reply_to_message.from_user.last_name:
        other_name += message.reply_to_message.from_user.last_name
    other_username = message.reply_to_message.from_user.username
    return other_name, other_username

def append_username_to_text(text: str, other_name:str , other_username: str, entities: List[MessageEntity], message: Message, user: Optional[User]=None):
    if other_username:
        entities.append(MessageEntity(
            type=MessageEntityType.MENTION,
            offset=count_offset(text) + 2,
            length=count_offset(other_username),
        ))
        text += f"  @{other_username}"
    elif other_name:
        if user:
            entities.append(MessageEntity(
                type=MessageEntityType.TEXT_MENTION,
                offset=count_offset(text) + 2,
                length=count_offset(other_name),
                user=user
            ))
        else:
            entities.append(MessageEntity(
                type=MessageEntityType.TEXT_MENTION,
                offset=count_offset(text) + 2,
                length=count_offset(other_name),
                user=message.reply_to_message.from_user
            ))
        text += f"  {other_name}"
    else:
        text += "Some unknown ghost"
    text += ": "
    return text, entities

def new_bold_string_entities(text: str) -> Tuple[str, List[MessageEntity]]:
    return append_bold_string("", text, [])

def append_bold_string(text: str, append_text: str, entities: List[MessageEntity]) -> Tuple[str, List[MessageEntity]]:
    entities.append(MessageEntity(
                        type=MessageEntityType.BOLD,
                        offset=count_offset(text),
                        length=count_offset(append_text)
                    ))
    text += append_text
    return text, entities

async def gen_reaction_list(emojis: List[str|int], bot: Client):
    me = bot.me or await bot.get_me()
    reaction_list = []
    if not me.is_premium:  # Remove custom emojis if not premium (will it happen?)
        emojis = [x for x in emojis if type(x) is not int]
    emojis = reduce(lambda x,y:x if y in x else x + [y],[[],]+emojis)  # Remove replicated
    for emoji in emojis:
        if type(emoji) is int:
            reaction_list.append(ReactionCustomEmoji(document_id=emoji))
        elif type(emoji) is str and emoji in NATIVE_EMOJI:
            reaction_list.append(ReactionEmoji(emoticon=emoji))
    return reaction_list

def append_log_status(text: str, entities: List[MessageEntity]) -> Tuple[str, List[MessageEntity]]:
    entities.append(
        MessageEntity(
            type=MessageEntityType.BOLD,
            offset=count_offset(text),
            length=len(f"\nKeep log: \n  {keep_log}")
        )
    )
    text += f"\nKeep log: \n  {keep_log}"
    return text, entities

@listener(command="trace",
          is_plugin=True,
          need_admin=True,
          description=USAGE)
async def trace(bot: Client, message: Message):
    global keep_log
    '''
    # For debug use
    if len(message.parameter) and message.parameter[0] == "magicword":
        return await message.edit(str(message))
    '''
    if len(message.parameter) == 0:  # Either untrace someone or throw error
        if message.reply_to_message is None or message.reply_to_message.from_user is None:
            return await print_usage(message)
        other_id = message.reply_to_message.from_user.id
        if not cached_sqlite.get(f"trace.user_id.{other_id}", None):
            return await edit_and_delete(message, "This user is not in the traced list.")
        prev_emojis = cached_sqlite.get(f"trace.user_id.{other_id}", None)

        del sqlite[f"trace.user_id.{other_id}"]
        del cached_sqlite[f"trace.user_id.{other_id}"]

        text, entities = new_bold_string_entities("Sucessfully untraced: \n")
        other_name, other_username = get_name_and_username_from_message(message)
        text, entities = append_username_to_text(text, other_name, other_username, entities, message)
        text, entities = append_emoji_to_text(text, prev_emojis, entities)
        return await edit_and_delete(message, text, entities=entities, seconds=5, parse_mode=ParseMode.MARKDOWN)
    elif len(message.parameter) == 1:
        if message.parameter[0] in ["status", "clean"]:  # Get all traced info
            traced_uids = await get_all_traced(bot)
            text, entities = (
                new_bold_string_entities("Traced userlist:\n")
                if message.parameter[0] == "status"
                else new_bold_string_entities("Sucessfully untraced: \n")
            )

            for traced_uid in traced_uids.keys():
                if message.parameter[0] == "clean":  # Delete all trace
                    del sqlite[f"trace.user_id.{traced_uid}"]
                    del cached_sqlite[f"trace.user_id.{traced_uid}"]
                other_name = ""
                if traced_uids[traced_uid]["user"].first_name:
                    other_name += traced_uids[traced_uid]["user"].first_name
                if traced_uids[traced_uid]["user"].last_name:
                    other_name += traced_uids[traced_uid]["user"].last_name
                other_username = traced_uids[traced_uid]["user"].username

                text, entities = append_username_to_text(text, other_name, other_username, entities, message, traced_uids[traced_uid]["user"])
                text, entities = append_emoji_to_text(text, traced_uids[traced_uid]["reactions"], entities)

            text, entities = append_bold_string(text, "\nTraced keywords: \n", entities)
            if traced_keywords := cached_sqlite.get("trace.keywordlist", None):
                for keyword in traced_keywords:
                    reaction_list = cached_sqlite.get(f"trace.keyword.{keyword.encode().hex()}", None)
                    if message.parameter[0] == "clean":
                        del sqlite[f"trace.keyword.{keyword.encode().hex()}"]
                        del cached_sqlite[f"trace.keyword.{keyword.encode().hex()}"]
                    text += f"  {keyword}: "
                    text, entities = append_emoji_to_text(text, reaction_list, entities)
                if message.parameter[0] == "clean":
                    del sqlite["trace.keywordlist"]
                    del cached_sqlite["trace.keywordlist"]
            if message.parameter[0] == "status":
                text, entities = append_log_status(text, entities)
            return await edit_and_delete(message, text, entities=entities, seconds=5, parse_mode=ParseMode.MARKDOWN)
        else:
            if emojis := get_emojis_from_message(message):
                reaction_list = await gen_reaction_list(emojis, bot)
                if reaction_list:
                    sqlite[f"trace.user_id.{message.reply_to_message.from_user.id}"] = reaction_list
                    cached_sqlite[f"trace.user_id.{message.reply_to_message.from_user.id}"] = reaction_list
                    await bot.invoke(
                        SendReaction(
                            peer=await bot.resolve_peer(int(message.chat.id)), 
                            msg_id=message.reply_to_message_id,
                            reaction=reaction_list,
                            big=True
                        )
                    )
                    text = "Successfully traced: \n"
                    # TODO: Add username
                    text, entities = append_emoji_to_text(text, reaction_list, [])
                    return await edit_and_delete(message, text, entities=entities, seconds=5, parse_mode=ParseMode.MARKDOWN)
                return await edit_and_delete(message, "No valid emojis found!")
            return await print_usage(message)
    elif len(message.parameter) == 2:  # log t|f; kw del
        if message.parameter[0] == "log":
            if message.parameter[1] == "true":
                keep_log = True
            elif message.parameter[1] == "false":
                keep_log = False
            else:
                return await print_usage(message)
            return await message.edit(str(f"**Keep log: \n  {keep_log}**"))
        elif message.parameter[1] == "del":
            keyword = message.parameter[0]
            keyword_encoded_hex = keyword.encode().hex()
            if not cached_sqlite.get(f"trace.keyword.{keyword_encoded_hex}"):
                return await edit_and_delete(message, f"Keyword \"{keyword}\" is not traced.")
            prev_emojis = cached_sqlite.get(f"trace.keyword.{keyword_encoded_hex}")

            del sqlite[f"trace.keyword.{keyword_encoded_hex}"]
            del cached_sqlite[f"trace.keyword.{keyword_encoded_hex}"]

            sqlite["trace.keywordlist"].remove(keyword)
            cached_sqlite["trace.keywordlist"].remove(keyword)

            text, entities = new_bold_string_entities("Sucessfully untraced keyword: \n")
            text += f"  {keyword}: "
            text, entities = append_emoji_to_text(text, prev_emojis, entities)
            return await edit_and_delete(message, text, entities=entities, seconds=5, parse_mode=ParseMode.MARKDOWN)
        else:
            return await print_usage(message)
    elif len(message.parameter) == 3:
        keyword, emojis = get_keyword_emojis_from_message(message)
        keyword_encoded_hex = keyword.encode().hex()
        if keyword and len(emojis) != 0:
            reaction_list = await gen_reaction_list(emojis, bot)
            if reaction_list:
                sqlite[f"trace.keyword.{keyword_encoded_hex}"] = reaction_list
                cached_sqlite[f"trace.keyword.{keyword_encoded_hex}"] = reaction_list

                if cached_sqlite.get("trace.keywordlist", None) is None:
                    sqlite["trace.keywordlist"] = [keyword]
                    cached_sqlite["trace.keywordlist"] = [keyword]
                elif keyword not in cached_sqlite["trace.keywordlist"]:
                    cached_sqlite["trace.keywordlist"].append(keyword)
                    sqlite["trace.keywordlist"] = cached_sqlite["trace.keywordlist"]

                text, entities = new_bold_string_entities("Successfully traced keyword: \n")
                text += f"  {keyword}: "
                text, entities = append_emoji_to_text(text, reaction_list, entities)
                return await edit_and_delete(message, text, entities=entities, seconds=5, parse_mode=ParseMode.MARKDOWN)
            return await edit_and_delete(message, "No valid emojis found!")
    else:
        return await print_usage(message)
    
@listener(is_plugin=False, incoming=True, outgoing=False, ignore_edited=True)
async def trace_user(client: Client, message: Message):
    if message.from_user is None:
        return
    if reaction_list := cached_sqlite.get(
        f"trace.user_id.{message.from_user.id}", None
    ):
        await client.invoke(
            SendReaction(
                peer=await client.resolve_peer(int(message.chat.id)), 
                msg_id=message.id,
                reaction=reaction_list,
                big=True
            )
        )

@listener(is_plugin=False, incoming=False, outgoing=False, ignore_edited=True)
async def trace_keyword(client: Client, message: Message):
    if message.from_user is None:
        return
    if message.text:
        if keyword_list := cached_sqlite.get("trace.keywordlist", None):
            for keyword in keyword_list:
                if keyword in message.text:
                    if reaction_list := cached_sqlite.get(
                        f"trace.keyword.{keyword.encode().hex()}", None
                    ):
                        await client.invoke(
                            SendReaction(
                                peer=await client.resolve_peer(int(message.chat.id)), 
                                msg_id=message.id,
                                reaction=reaction_list,
                                big=True
                            )
                        )