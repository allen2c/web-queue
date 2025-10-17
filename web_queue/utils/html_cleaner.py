import re
import typing

import bs4

DEFAULT_KEEP_TAGS: typing.Tuple[typing.Text, ...] = (
    "a",
    "article",
    "body",
    "br",
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "html",
    "li",
    "main",
    "ol",
    "p",
    "section",
    "table",
    "tbody",
    "td",
    "th",
    "tr",
    "ul",
)
DEFAULT_KEEP_ATTRIBUTES: typing.Tuple[typing.Text, ...] = ("id", "class")
DEFAULT_DROP_TAGS: typing.Tuple[typing.Text, ...] = ("script", "style", "iframe")


class HTMLCleaner:
    @staticmethod
    def clean_as_main_content_html(
        html: typing.Text | bs4.BeautifulSoup,
    ) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )
        html = HTMLCleaner.clean_all_comments(html)
        html = HTMLCleaner.keep_only_tags(html)
        html = HTMLCleaner.clean_tags(html)
        html = HTMLCleaner.clean_attributes(html)
        html = HTMLCleaner.keep_first_class_name(html)
        return html

    @staticmethod
    def clean_as_main_content_html_str(
        html: typing.Text | bs4.BeautifulSoup,
    ) -> str:
        html = HTMLCleaner.clean_as_main_content_html(html)
        return re.sub(r">\s+<", "><", str(html))

    @staticmethod
    def keep_only_tags(
        html: typing.Text | bs4.BeautifulSoup,
        tags: typing.List[typing.Text] | None = None,
    ) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )
        tags = tags or list(DEFAULT_KEEP_TAGS)

        # Find all tags that are not in the keep list and decompose them
        for tag in html.find_all():
            if tag.name not in tags:
                tag.decompose()

        return html

    @staticmethod
    def keep_first_class_name(
        html: typing.Text | bs4.BeautifulSoup,
    ) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )

        # Keep only the first class name for elements with multiple classes
        for tag in html.find_all(attrs={"class": True}):
            class_attr = tag.get("class")
            if isinstance(class_attr, list) and len(class_attr) > 1:
                tag["class"] = class_attr[0]
            elif isinstance(class_attr, str):
                classes = class_attr.split()
                if len(classes) > 1:
                    tag["class"] = classes[0]

        return html

    @staticmethod
    def clean_attributes(
        html: typing.Text | bs4.BeautifulSoup,
        attributes: typing.List[typing.Text] | None = None,
    ) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )
        attributes = attributes or list(DEFAULT_KEEP_ATTRIBUTES)
        for tag in html.find_all():
            for attribute in list(tag.attrs):
                if attribute not in attributes:
                    tag.attrs.pop(attribute, None)

        return html

    @staticmethod
    def clean_all_comments(html: typing.Text | bs4.BeautifulSoup) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )
        for comment in html.find_all(text=lambda text: isinstance(text, bs4.Comment)):
            comment.decompose()
        return html

    @staticmethod
    def clean_tags(
        html: typing.Text | bs4.BeautifulSoup,
        tags: typing.List[typing.Text] | None = None,
    ) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )
        tags = tags or list(DEFAULT_DROP_TAGS)

        for tag in html.find_all(tags):
            tag.decompose()

        return html
