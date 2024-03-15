""" PagerMaid Plugin Coin by Pentacene """
#   ______          _
#   | ___ \        | |
#   | |_/ /__ _ __ | |_ __ _  ___ ___ _ __   ___
#   |  __/ _ \ '_ \| __/ _` |/ __/ _ \ '_ \ / _ \
#   | | |  __/ | | | || (_| | (_|  __/ | | |  __/
#   \_|  \___|_| |_|\__\__,_|\___\___|_| |_|\___|
#

from datetime import datetime
from sys import executable
import urllib.request
from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, pip_install

pip_install("binance-connector", alias="binance")
pip_install("xmltodict")

from binance.spot import Spot
import xmltodict

API = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"

def init() -> list:
    """ INIT """
    with urllib.request.urlopen(API) as response:
        result = response.read()
        currencies = []
        data = {}
        rate_data = xmltodict.parse(result)
        rate_data = rate_data['gesmes:Envelope']['Cube']['Cube']['Cube']
        for i in rate_data:
            currencies.append(i['@currency'])
            data[i['@currency']] = float(i['@rate'])
        currencies.sort()
    return [currencies, data]

@listener(command="bc", description="coins", parameters="[num] [coin1] [coin2]")
async def coin(_: Client, message: Message) -> None:
    """coin change"""
    currencies, data = init()
    binanceclient = Spot()
    nowtimestamp = binanceclient.time()
    nowtime = datetime.fromtimestamp(float(nowtimestamp['serverTime'])/1000)
    if len(context.parameter) == 0:
        btc_usdt_data = binanceclient.klines("BTCUSDT", "1m")[:1][0]
        eth_usdt_data = binanceclient.klines("ETHUSDT", "1m")[:1][0]
        await context.edit((
            f'{nowtime.strftime("%Y-%m-%d %H:%M:%S")} UTC\n'
            f'**1 BTC** = {btc_usdt_data[1]} USDT '
            f'\n'
            f'**1 ETH** = {eth_usdt_data[1]} USDT '))
        return
    if len(context.parameter) < 3:
        await context.edit('输入错误.\nbc 数量 币种1 币种2')
        return
    try:
        number = float(context.parameter[0])
    except ValueError:
        await context.edit('输入错误.\nbc 数量 币种1 币种2')
        return
    _from = context.parameter[1].upper().strip()
    _to = context.parameter[2].upper().strip()

    # both are real currency
    if (currencies.count(_from) != 0) and (currencies.count(_to) != 0):
        await context.edit((
            f'{context.parameter[0]} {context.parameter[1].upper().strip()} ='
            f'{number * data[_to] / data[_from]:.2f} '
            f'{context.parameter[2].upper().strip()}'))
        return
    
    # from real currency to crypto
    if currencies.count(_from) != 0:
        usd_number = number * data["USD"] / data[_from]
        try:
            x_usdt_data = binanceclient.klines(f"{_to}USDT", "1m")[:1][0]
        except ClientError:
            await context.edit(f'Cannot find coinpair {_to}USDT')
            return
        await context.edit((
            f'{context.parameter[0]} **{_from}** = '
            f'{1 / float(x_usdt_data[1]) * usd_number:.8f} **{_to}**\n'
            f'{context.parameter[0]} **{_from}** = '
            f'{usd_number:.2f} **USD**'))
        return
    
    # from crypto to real currency
    if currencies.count(_to) != 0:
        usd_number = number * data[_to] / data["USD"]
        try:
            x_usdt_data = binanceclient.klines(f"{_from}USDT", "1m")[:1][0]
        except ClientError:
            await context.edit(f'Cannot find coinpair {_from}USDT')
            return
        await context.edit((
            f'{context.parameter[0]} **{_from}** = '
            f'{float(x_usdt_data[1]) * usd_number:.2f} **{_to}**\n'
            f'{context.parameter[0]} **{_from}** = '
            f'{float(x_usdt_data[1]):.2f} **USD**'))
        return

    # both crypto
    try:
        from_to_data = binanceclient.klines(f"{_from}{_to}", "1m")[:1][0]
    except ClientError:
        await context.edit(f'Cannot find coinpair {_from}{_to}')
        return
    await context.edit((
            f'{context.parameter[0]} **{_from}** = '
            f'{float(from_to_data[1]) * number} **{_to}**\n'))
