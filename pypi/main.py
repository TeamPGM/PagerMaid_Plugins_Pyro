import html
import re

from pyrogram.enums import ParseMode

from pagermaid.enums import Message, AsyncClient
from pagermaid.listener import listener


def clean_html(raw_html):
    return re.sub(re.compile(r"<.*?>"), "", raw_html)


def escape_definition(definition):
    for key, value in definition.items():
        if isinstance(value, str):
            definition[key] = html.escape(clean_html(value))
    return definition


@listener(
    command="pypi", description="Search PyPI packages", parameters="The query string"
)
async def pypi(message: Message, httpx: AsyncClient):
    if not message.arguments:
        return await message.edit("Please provide a query string")
    r = await httpx.get(
        f"https://pypi.org/pypi/{message.arguments}/json", follow_redirects=True
    )
    if r.status_code != 200:
        return await message.edit("Could not find the package")
    json = r.json()
    pypi_info = escape_definition(json["info"])
    text = """
<b><a href="{package_link}">{package_name}</a></b> by <i>{author_name} {author_email}</i>
平台：<b>{platform}</b>
版本：<b>{version}</b>
许可协议：<b>{license}</b>
摘要：<b>{summary}</b>""".format(
        package_link=f"https://pypi.org/pypi/{message.arguments}",
        package_name=pypi_info["name"],
        author_name=pypi_info["author"],
        author_email=f"&lt;{pypi_info['author_email']}&gt;"
        if pypi_info["author_email"]
        else "",
        platform=pypi_info["platform"] or "未指定",
        version=pypi_info["version"],
        license=pypi_info["license"] or "未指定",
        summary=pypi_info["summary"],
    )
    await message.edit(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
