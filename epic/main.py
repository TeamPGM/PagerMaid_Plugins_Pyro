import sys

from pytz import timezone
from datetime import datetime

from pagermaid.utils import client
from pagermaid.listener import listener
from pagermaid.single_utils import Message, safe_remove


async def get_epic_games():
    epic_url = "https://www.epicgames.com/graphql"
    headers = {
        "Referer": "https://www.epicgames.com/store/zh-CN/",
        "Content-Type": "application/json; charset=utf-8",
    }
    data = {
        "query": "query searchStoreQuery($allowCountries: String, $category: String, $count: Int, $country: String!, "
        "$keywords: String, $locale: String, $namespace: String, $sortBy: String, $sortDir: String, $start: Int, "
        "$tag: String, $withPrice: Boolean = false, $withPromotions: Boolean = false) {\n Catalog {\n "
        "searchStore(allowCountries: $allowCountries, category: $category, count: $count, country: $country, "
        "keywords: $keywords, locale: $locale, namespace: $namespace, sortBy: $sortBy, sortDir: $sortDir, "
        "start: $start, tag: $tag) {\n elements {\n title\n id\n namespace\n description\n effectiveDate\n "
        "keyImages {\n type\n url\n }\n seller {\n id\n name\n }\n productSlug\n urlSlug\n url\n items {\n id\n "
        "namespace\n }\n customAttributes {\n key\n value\n }\n categories {\n path\n }\n price(country: "
        "$country) @include(if: $withPrice) {\n totalPrice {\n discountPrice\n originalPrice\n voucherDiscount\n "
        "discount\n currencyCode\n currencyInfo {\n decimals\n }\n fmtPrice(locale: $locale) {\n originalPrice\n "
        "discountPrice\n intermediatePrice\n }\n }\n lineOffers {\n appliedRules {\n id\n endDate\n "
        "discountSetting {\n discountType\n }\n }\n }\n }\n promotions(category: $category) @include(if: "
        "$withPromotions) {\n promotionalOffers {\n promotionalOffers {\n startDate\n endDate\n discountSetting {"
        "\n discountType\n discountPercentage\n }\n }\n }\n upcomingPromotionalOffers {\n promotionalOffers {\n "
        "startDate\n endDate\n discountSetting {\n discountType\n discountPercentage\n }\n }\n }\n }\n }\n paging "
        "{\n count\n total\n }\n }\n }\n}\n",
        "variables": {
            "allowCountries": "CN",
            "category": "freegames",
            "count": 1000,
            "country": "CN",
            "locale": "zh-CN",
            "sortBy": "effectiveDate",
            "sortDir": "asc",
            "withPrice": True,
            "withPromotions": True,
        },
    }
    res = await client.post(epic_url, headers=headers, json=data, timeout=10.0)
    res_json = res.json()
    return res_json["data"]["Catalog"]["searchStore"]["elements"]


def parse_game(game):
    game_name = game["title"]
    game_corp = game["seller"]["name"]
    game_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
    game_promotions = game["promotions"]["promotionalOffers"]
    upcoming_promotions = game["promotions"]["upcomingPromotionalOffers"]
    if not game_promotions and upcoming_promotions:
        raise FileNotFoundError  # 促销即将上线，跳过
    if (
        game_promotions[0]["promotionalOffers"][0]["discountSetting"]["discountType"]
        == "PERCENTAGE"
        and game_promotions[0]["promotionalOffers"][0]["discountSetting"][
            "discountPercentage"
        ]
        != 0
    ):
        raise FileNotFoundError  # 不免费，跳过
    game_thumbnail, game_dev, game_pub = None, None, None
    for image in game["keyImages"]:
        game_thumbnail = image["url"] if image["type"] == "Thumbnail" else None
    for pair in game["customAttributes"]:
        game_dev = pair["value"] if pair["key"] == "developerName" else game_corp
        game_pub = pair["value"] if pair["key"] == "publisherName" else game_corp
    game_desp = game["description"]
    end_date_iso = game["promotions"]["promotionalOffers"][0]["promotionalOffers"][0][
        "endDate"
    ][:-1]
    end_date = (
        datetime.fromisoformat(end_date_iso)
        .replace(tzinfo=timezone("UTC"))
        .astimezone(timezone("Asia/Chongqing"))
        .strftime("%Y-%m-%d %H:%M:%S")
    )
    # API 返回不包含游戏商店 URL，此处自行拼接，可能出现少数游戏 404
    game_url = (
        f"https://www.epicgames.com/store/zh-CN/p/{game['productSlug'].replace('/home', '')}"
        if game["productSlug"]
        else "暂无链接"
    )
    msg = f"**FREE now :: {game_name} ({game_price})**\n\n{game_desp}\n\n"
    msg += (
        f"游戏由 {game_pub} 发售，"
        if game_dev == game_pub
        else f"游戏由 {game_dev} 开发、{game_pub} 出版，"
    )
    msg += f"将在 **{end_date}** 结束免费游玩，戳下面的链接领取吧~\n{game_url}"

    return msg, game_thumbnail


@listener(command="epic", description="获取 Epic 喜加一限免")
async def epic(message: Message):
    try:
        games = await get_epic_games()
    except Exception as e:
        return await message.edit(
            f"请求 Epic Store API 错误：{str(sys.exc_info()[0])}" + "\n" + str(e)
        )
    if not games:
        return await message.edit("Epic 可能又抽风啦，请稍后再试（")
    for game in games:
        try:
            msg, game_thumbnail = parse_game(game)
            if game_thumbnail:
                r = await client.get(game_thumbnail, timeout=10.0)
                with open("epic.jpg", "wb") as code:
                    code.write(r.content)
                try:
                    await message.reply_photo(
                        "epic.jpg",
                        caption=msg,
                        quote=False,
                        reply_to_message_id=message.reply_to_top_message_id,
                    )
                except Exception:
                    await message.reply(
                        msg,
                        quote=False,
                        reply_to_message_id=message.reply_to_top_message_id,
                    )
                safe_remove("epic.jpg")
            else:
                await message.reply(msg, quote=False)
        except (TypeError, IndexError):
            pass
        except FileNotFoundError:
            continue
        except Exception as e:
            return await message.edit(
                f"获取 Epic 信息错误：{str(sys.exc_info()[0])}" + "\n" + str(e)
            )
    await message.delete()
