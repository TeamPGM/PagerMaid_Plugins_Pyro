""" Pagermaid currency exchange rates plugin. Plugin by @fruitymelon and @xtaodada"""

from json.decoder import JSONDecodeError

from pagermaid import log
from pagermaid.utils import alias_command
from pagermaid.enums import Message
from pagermaid.services import client, scheduler
from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.config import Config


class Rate:
    def __init__(self):
        if Config.LANGUAGE == "en":
            self.lang_rate = {
                "des": "Currency exchange rate plugin",
                "arg": "[from_] [to_] [NUM]",
                "help": "Currency exchange rate plugin\n\n"
                f"Usage: `,{alias_command('rate')} [from_] [to_] [NUM] where [NUM] is "
                "optional`\n\nAvailable currencies: \n",
                "nc": "is not available.\n\nAvailable currencies: \n",
                "notice": "Data are updated daily.",
                "warning": "Data are updated daily.",
            }
        else:
            self.lang_rate = {
                "des": "货币汇率插件",
                "arg": "[from_] [to_] [NUM]",
                "help": "这是货币汇率插件\n\n"
                f"使用方法: `,{alias_command('rate')} [from_] [to_] [NUM]，其中 [NUM] 是可省略的`\n\n"
                "支持货币: \n",
                "nc": "不是支持的货币. \n\n支持货币: \n",
                "notice": "数据每日八点更新",
                "warning": "数据每日八点更新",
            }
        self.host = "https://cdn.jsdelivr.net/gh/fawazahmed0/currency-api@1/latest"
        self.api = f"{self.host}/currencies.json"
        self.currencies = []
        self.data = {}

    async def get_data(self):
        try:
            req = await client.get(self.api, follow_redirects=True)
            assert req.status_code == 200
            self.data = req.json()
            for key in list(enumerate(self.data)):
                self.currencies.append(key[1].upper())
            self.currencies.sort()
        except JSONDecodeError as e:
            await log(f"Warning: plugin rate failed to refresh rates data. {e}")

    async def get_rate(self, from_: str, to_: str, nb: float):
        endpoint = f"{self.host}/currencies/{from_.lower()}/{to_.lower()}.json"
        try:
            req = await client.get(endpoint, follow_redirects=True)
            rate__data = req.json()
            return (
                f"`{from_} : {to_} = {nb} : {round(nb * rate__data[to_.lower()], 4)}`"
                f"\n\n"
                f'{self.lang_rate["warning"]}'
            )
        except Exception as e:
            return str(e)


rate_data = Rate()


@Hook.on_startup()
async def init_rate():
    await rate_data.get_data()


@scheduler.scheduled_job("cron", hour="8", id="refresher_rate")
async def refresher_rate():
    await rate_data.get_data()


@listener(
    command="rate",
    description=rate_data.lang_rate["des"],
    parameters=rate_data.lang_rate["arg"],
)
async def rate(message: Message):
    global rate_data
    if not rate_data.data:
        await rate_data.get_data()
    if not rate_data.data:
        return
    if not message.arguments:
        await message.edit(
            f"{rate_data.lang_rate['help']}`{', '.join(rate_data.currencies)}`\n\n"
            f"{rate_data.lang_rate['notice']}"
        )
        return
    nb = 1.0
    if len(message.parameter) not in [3, 2]:
        await message.edit(
            f"{rate_data.lang_rate['help']}`{', '.join(rate_data.currencies)}`"
            f"\n\n{rate_data.lang_rate['notice']}"
        )
        return
    from_ = message.parameter[0].upper().strip()
    to_ = message.parameter[1].upper().strip()
    try:
        nb = nb if len(message.parameter) == 2 else float(message.parameter[2].strip())
    except Exception:
        nb = 1.0
    if rate_data.currencies.count(from_) == 0:
        await message.edit(
            f"{from_}{rate_data.lang_rate['nc']}`{', '.join(rate_data.currencies)}`"
        )
        return
    if rate_data.currencies.count(to_) == 0:
        await message.edit(
            f"{to_}{rate_data.lang_rate['nc']}{', '.join(rate_data.currencies)}`"
        )
        return
    try:
        text = await rate_data.get_rate(from_, to_, nb)
    except Exception as e:
        text = str(e)
    await message.edit(text)
