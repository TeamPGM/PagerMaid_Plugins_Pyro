import contextlib

from PIL import Image

from os.path import exists

from httpx import ReadTimeout

from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove
from pagermaid.utils import lang, pip_install

pip_install("speedtest-cli", alias="speedtest")

from speedtest import Speedtest, ShareResultsConnectFailure, ShareResultsSubmitFailure, NoMatchedServers, \
    SpeedtestBestServerFailure, SpeedtestHTTPError


def unit_convert(byte):
    """ Converts byte into readable formats. """
    power = 1000
    zero = 0
    units = {
        0: '',
        1: 'Kb/s',
        2: 'Mb/s',
        3: 'Gb/s',
        4: 'Tb/s'}
    while byte > power:
        byte /= power
        zero += 1
    return f"{round(byte, 2)} {units[zero]}"


async def run_speedtest(message: Message):
    test = Speedtest()
    server = [int(message.arguments)] if len(message.parameter) == 1 else []
    if server:
        test.get_servers(servers=server)
    else:
        test.get_best_server(servers=test.servers)
    test.download()
    test.upload()
    with contextlib.suppress(ShareResultsConnectFailure):
        test.results.share()
    result = test.results.dict()
    des = (
        f"**Speedtest** \n"
        f"Server: `{result['server']['name']} - "
        f"{result['server']['cc']}` \n"
        f"Sponsor: `{result['server']['sponsor']}` \n"
        f"Upload: `{unit_convert(result['upload'])}` \n"
        f"Download: `{unit_convert(result['download'])}` \n"
        f"Latency: `{result['ping']}` \n"
        f"Timestamp: `{result['timestamp']}`"
    )
    if result["share"]:
        data = await message.request.get(result["share"].replace("http:", "https:"), follow_redirects=True)
        with open("speedtest.png", mode="wb") as f:
            f.write(data.content)
        with contextlib.suppress(Exception):
            img = Image.open("speedtest.png")
            c = img.crop((17, 11, 727, 389))
            c.save("speedtest.png")
    return des, "speedtest.png" if exists("speedtest.png") else None


@listener(command="speedtest",
          description=lang('speedtest_des'),
          parameters="(Server ID)")
async def speedtest(message: Message):
    """ Tests internet speed using speedtest. """
    msg = await message.edit(lang('speedtest_processing'))
    try:
        des, photo = await run_speedtest(message)
    except SpeedtestHTTPError:
        return await msg.edit(lang('speedtest_ConnectFailure'))
    except ValueError:
        return await msg.edit(lang('arg_error'))
    except (SpeedtestBestServerFailure, NoMatchedServers):
        return await msg.edit(lang('speedtest_ServerFailure'))
    except (ShareResultsSubmitFailure, RuntimeError, ReadTimeout):
        return await msg.edit(lang('speedtest_ConnectFailure'))
    if not photo:
        return await msg.edit(des)
    try:
        await message.bot.send_photo(message.chat.id, photo, caption=des)
    except Exception:
        return await msg.edit(des)
    safe_remove(photo)
