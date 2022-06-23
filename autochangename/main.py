""" Module to automate message deletion. """
import traceback
from asyncio import sleep
from datetime import datetime, timedelta, timezone
from pagermaid.utils import pip_install

pip_install("emoji")

from emoji import emojize
from pagermaid import logs, scheduler, bot
from pagermaid.listener import listener



auto_change_name_init = False
dizzy = emojize(":dizzy:", use_aliases=True)
cake = emojize(":cake:", use_aliases=True)
all_time_emoji_name = ["clock12", "clock1230", "clock1", "clock130", "clock2", "clock230", "clock3", "clock330",
                       "clock4", "clock430", "clock5", "clock530", "clock6", "clock630", "clock7", "clock730", "clock8",
                       "clock830", "clock9", "clock930", "clock10", "clock1030", "clock11", "clock1130"]
time_emoji_symb = [emojize(":%s:" % s, use_aliases=True) for s in all_time_emoji_name]


@scheduler.scheduled_job("interval", seconds=30, id="autochangename")
async def change_name_auto():
    try:
        time_cur = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(timezone(
            timedelta(hours=8))).strftime('%H:%M:%S:%p:%a')
        hour, minu, seco, p, abbwn = time_cur.split(':')
        shift = 0
        if int(minu) > 30: shift = 1
        hsym = time_emoji_symb[(int(hour) % 12) * 2 + shift]
        _last_name = f"{hour}:{minu} {p} UTC+8 {hsym}"
        await bot.update_profile(last_name=_last_name)
        me = await bot.get_me()
        if me.last_name != _last_name:
            raise Exception("修改 last_name 失败")
    except Exception as e:
        trac = "\n".join(traceback.format_exception(e))
        await logs.info(f"更新失败! \n{trac}")
