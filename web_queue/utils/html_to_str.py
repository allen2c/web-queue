import typing

import bs4
import html_to_markdown


def html_to_str(html: bs4.BeautifulSoup | bs4.Tag | str) -> str:
    html = bs4.BeautifulSoup(html, "html.parser") if isinstance(html, str) else html
    content = html_to_markdown.convert(str(html)).strip()
    return "\n".join(line.rstrip() for line in content.splitlines())


def htmls_to_str(
    htmls: typing.List[bs4.BeautifulSoup | bs4.Tag | str] | bs4.ResultSet[bs4.Tag],
) -> str:
    return "\n\n".join(html_to_str(h) for h in htmls)
