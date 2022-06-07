import datetime
from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, client

icons = {
    "01d": "🌞",
    "01n": "🌚",
    "02d": "⛅️",
    "02n": "⛅️",
    "03d": "☁️",
    "03n": "☁️",
    "04d": "☁️",
    "04n": "☁️",
    "09d": "🌧",
    "09n": "🌧",
    "10d": "🌦",
    "10n": "🌦",
    "11d": "🌩",
    "11n": "🌩",
    "13d": "🌨",
    "13n": "🌨",
    "50d": "🌫",
    "50n": "🌫",
}


def timestamp_to_time(timestamp, timeZoneShift):
    timeArray = datetime.datetime.utcfromtimestamp(timestamp) + datetime.timedelta(seconds=timeZoneShift)
    return timeArray.strftime("%H:%M")


def calcWindDirection(windDirection):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(windDirection / (360. / len(dirs)))
    return dirs[ix % len(dirs)]


@listener(command="weather",
          description="查询天气",
          parameters="<城市>")
async def weather(_: Client, message: Message):
    of not message.arguments:
        return await message.edit("出错了呜呜呜 ~ 无效的参数。")
    try:
        req = await client.get(
            "http://api.openweathermap.org/data/2.5/weather?appid=973e8a21e358ee9d30b47528b43a8746&units=metric&lang"
            "=zh_cn&q=" + message.arguments)
        if req.status_code == 200:
            data = req.json()
            cityName = "{}, {}".format(data["name"], data["sys"]["country"])
            timeZoneShift = data["timezone"]
            temp_Max = round(data["main"]["temp_max"], 2)
            temp_Min = round(data["main"]["temp_min"], 2)
            pressure = data["main"]["pressure"]
            humidity = data["main"]["humidity"]
            windSpeed = data["wind"]["speed"]
            windDirection = calcWindDirection(data["wind"]["deg"])
            sunriseTimeunix = data["sys"]["sunrise"]
            sunriseTime = timestamp_to_time(sunriseTimeunix, timeZoneShift)
            sunsetTimeunix = data["sys"]["sunset"]
            sunsetTime = timestamp_to_time(sunsetTimeunix, timeZoneShift)
            fellsTemp = data["main"]["feels_like"]
            tempInC = round(data["main"]["temp"], 2)
            tempInF = round((1.8 * tempInC) + 32, 2)
            icon = data["weather"][0]["icon"]
            desc = data["weather"][0]["description"]
            res = "{} {}{} 💨{} {}m/s\n大气🌡 {}℃ ({}℉) 💦 {}% \n体感🌡 {}℃\n气压 {}hpa\n🌅{} 🌇{} ".format(
                cityName, icons[icon], desc, windDirection, windSpeed, tempInC, tempInF, humidity, fellsTemp, pressure,
                sunriseTime, sunsetTime
            )
            await message.edit(res)
        if req.status_code == 404:
            await message.edit("出错了呜呜呜 ~ 无效的城市名，请使用拼音输入 ~ ")
            return
    except Exception:
        await message.edit("出错了呜呜呜 ~ 无法访问到 openweathermap.org 。")
