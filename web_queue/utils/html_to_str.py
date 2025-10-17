import typing

import bs4


def html_to_str(html: bs4.BeautifulSoup | bs4.Tag | str) -> str:
    html = bs4.BeautifulSoup(html, "html.parser") if isinstance(html, str) else html

    full_text = ""
    for p in html.find_all("p"):
        content = p.get_text(separator="\n", strip=True)
        full_text += content
        full_text += "\n"

    return full_text.strip()


def htmls_to_str(
    htmls: typing.List[bs4.BeautifulSoup | bs4.Tag | str] | bs4.ResultSet[bs4.Tag],
) -> str:
    return "\n\n".join(html_to_str(h) for h in htmls)
