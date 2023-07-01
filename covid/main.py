""" https://github.com/Zeta-qixi/nonebot-plugin-covid19-news """

import json

from typing import Dict

from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import client

POLICY_ID = {}


class Area:
    def __init__(self, data):
        self.name = data["name"]
        self.today = data["today"]
        self.total = data["total"]
        self.grade = data["total"].get("grade", "风险未确认")
        self.children = data.get("children", None)

    @property
    async def policy(self):
        return await get_policy(POLICY_ID.get(self.name))

    @property
    def main_info(self):
        return (
            f"**{self.name} 新冠肺炎疫情情况**  ({self.grade})\n\n"
            f"`😔新增确诊：{self.today['confirm']}`\n"
            f"`☢️现存确诊：{self.total['nowConfirm']}`"
        )


class AreaList(Dict):
    def add(self, data):
        self[data.name] = data


class NewsData:
    def __init__(self):
        self.data = {}
        self.time = ""

    async def update_data(self):
        url = "https://api.inews.qq.com/newsqa/v1/query/inner/publish/modules/list?modules=statisGradeCityDetail,diseaseh5Shelf"
        res = await client.get(url)
        if res.status_code != 200:
            return
        data = res.json()["data"]["diseaseh5Shelf"]

        if data["lastUpdateTime"] != self.time:
            self.time = data["lastUpdateTime"]
            self.data = AreaList()

            def get_data(data_):
                if isinstance(data_, list):
                    for i in data_:
                        get_data(i)

                if isinstance(data_, dict):
                    if area_ := data_.get("children"):
                        get_data(area_)

                    self.data.add(Area(data_))  # noqa

            get_data(data["areaTree"][0])
            return


async def set_pid():
    url_city_list = "https://r.inews.qq.com/api/trackmap/citylist?"
    resp = await client.get(url_city_list)
    res = resp.json()

    for province in res["result"]:
        if cities := province.get("list"):
            for city in cities:
                cid = city["id"]
                name = city["name"]
                POLICY_ID[name] = cid


async def get_policy(uid):
    url_get_policy = f"https://r.inews.qq.com/api/trackmap/citypolicy?&city_id={uid}"
    resp = await client.get(url_get_policy)
    res_ = resp.json()
    if res_["message"] != "success":
        return "数据获取失败！"
    try:
        data = res_["result"]["data"][0]
    except IndexError:
        return "暂无政策信息"
    return f"出行({data['leave_policy_date']})\n{data['leave_policy']}\n\
------\n\
进入({data['back_policy_date']})\n{data['back_policy']}"


NewsBot = NewsData()


@listener(command="covid", description="获取新冠疫情信息。", parameters="[地区]")
async def covid_info(message: Message):
    global POLICY_ID, NewsBot
    if not POLICY_ID:
        await set_pid()
    await NewsBot.update_data()

    city = message.arguments
    if not city:
        return await message.edit("[covid] 无法获取城市名！")
    zc = False
    if city.find("政策") != -1:
        zc = True
        city = city.replace("政策", "")
    if city := NewsBot.data.get(city):
        policy = await city.policy if zc else "Tips: 查询出行政策可加上 `政策`"
        await message.edit(f"{city.main_info}\n\n{policy}")
    else:
        await message.edit("[covid] 只限查询国内城市或你地理没学好。")
