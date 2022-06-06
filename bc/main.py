""" PagerMaid Plugin Coin by Pentacene """
#   ______          _
#   | ___ \        | |
#   | |_/ /__ _ __ | |_ __ _  ___ ___ _ __   ___
#   |  __/ _ \ '_ \| __/ _` |/ __/ _ \ '_ \ / _ \
#   | | |  __/ | | | || (_| | (_|  __/ | | |  __/
#   \_|  \___|_| |_|\__\__,_|\___\___|_| |_|\___|
#

from asyncio import sleep
from sys import executable
import urllib.request
from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, pip_install

pip_install("python-binance", alias="binance")
pip_install("xmltodict")

from binance.client import Client
import xmltodict


API = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
CURRENCIES = []
DATA = {}
BINANCE_API_KEY = '8PDfQ2lSIyHPWdNAHNIaIoNy3MiiMuvgwYADbmtsKo867B0xnIhIGjPULsOtvMRk'
BINANCE_API_SECRET = 'tbUiyZ94l0zpYOlKs3eO1dvLNMOSbOb2T1T0eT0I1eogH9Fh8Htvli05eZ1iDvra'


def init() -> None:
    """ INIT """
    with urllib.request.urlopen(API) as response:
        result = response.read()
        try:
            global CURRENCIES, DATA
            rate_data = xmltodict.parse(result)
            rate_data = rate_data['gesmes:Envelope']['Cube']['Cube']['Cube']
            for i in rate_data:
                CURRENCIES.append(i['@currency'])
                DATA[i['@currency']] = float(i['@rate'])
            CURRENCIES.sort()
        except Exception as e:
            raise e


@listener(command="bc",
          description="coins",
          parameters="<num> <coin1> <coin2>")
async def coin(_: Client, message: Message) -> None:
    """ coin change """
    init()
    action = message.arguments.split()
    binanceclient = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
    if len(action) < 3:
        await message.edit('输入错误.\n-bc 数量 币种1 币种2')
        return
    else:
        prices = binanceclient.get_all_tickers()
        try:
            number = float(action[0])
        except ValueError:
            await message.edit('输入错误.\n-bc 数量 币种1 币种2')
            return
        _from = action[1].upper().strip()
        _to = action[2].upper().strip()
        front_text = ''
        text = ''
        rear_text = ''
        price = 0.0
        _to_USD_rate = 0.0

        if (CURRENCIES.count(_from) != 0) and (CURRENCIES.count(_to) != 0):
            # both are real currency
            text = f'{action[0]} {action[1].upper().strip()} = {float(action[0])*DATA[_to]/DATA[_from]:.2f} {action[2].upper().strip()}'

        else:
            if CURRENCIES.count(_from) != 0:
                # from virtual currency to real currency
                number = number * DATA["USD"] / DATA[_from]
                _from = 'USDT'
                front_text = f'{action[0]} {action[1]} = \n'

            if CURRENCIES.count(_to) != 0:
                # from real currency to virtual currency
                _to_USD_rate = DATA[_to] / DATA["USD"]
                _to = 'USDT'

            for _a in prices:
                if _a['symbol'] == str(f'{_from}{_to}'):
                    price = _a['price']
                    if _to == 'USDT':
                        if action[2].upper().strip() == 'USDT':
                            rear_text = f'\n= {number * float(price) * DATA["CNY"]/DATA["USD"]:.2f} CNY'
                        else:
                            rear_text = f'\n= {number * float(price) * _to_USD_rate:.2f} {action[2].upper().strip()}'
                    if float(price) < 1:
                        text = f'{number} {_from} = {number * float(price):.8f} {_to}'
                    else:
                        text = f'{number} {_from} = {number * float(price):.2f} {_to}'
                    break
                elif _a['symbol'] == str(f'{_to}{_from}'):
                    price = 1 / float(_a['price'])
                    text = f'{number} {_from} = {number * float(price):.8f} {_to}'
                    break
                else:
                    price = None

        if price is None:
            text = f'Cannot find coinpair {action[1].upper().strip()}{action[2].upper().strip()} or {action[2].upper().strip()}{action[1].upper().strip()}'

    await message.edit(f'{front_text}{text}{rear_text}')
