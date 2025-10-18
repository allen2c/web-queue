import logging

import pydantic

logger = logging.getLogger(__name__)


class HTMLMetadataResponse(pydantic.BaseModel):
    """Structured response for HTML content metadata and element locators.

    Extracts content body CSS selector and metadata values.
    """

    title: str = pydantic.Field(
        default="",
        description=(
            "The actual title text of the content "
            "(e.g., chapter title, article title). "
            "Return empty string if not found."
        ),
    )

    author: str = pydantic.Field(
        default="",
        description=(
            "The actual author name or username. " "Return empty string if not found."
        ),
    )

    chapter_id: str = pydantic.Field(
        default="",
        description=(
            "The actual chapter ID or identifier (e.g., '12345', 'ch-001'). "
            "Return empty string if not found."
        ),
    )

    chapter_number: str = pydantic.Field(
        default="",
        description=(
            "The actual chapter number (e.g., '1', '42', 'Chapter 5'). "
            "Return empty string if not found."
        ),
    )

    content_body_css_selector: str = pydantic.Field(
        default="",
        description=(
            "CSS selector for the main content body element "
            "containing article text only. "
            "Exclude metadata like title, author, dates. "
            "Example: 'div.article-body', 'div#novel-content'. "
            "Use standard CSS syntax. Return empty string if not found."
        ),
    )

    created_date: str = pydantic.Field(
        default="",
        description=(
            "The content creation date in ISO 8601 format "
            "with Asia/Taipei timezone "
            "(e.g., '2025-10-12T14:30:00+08:00'). "
            "Parse relative dates like '2 days ago' "
            "using the current_time provided in the system prompt. "
            "Return empty string if not found."
        ),
    )

    updated_date: str = pydantic.Field(
        default="",
        description=(
            "The content last update date in ISO 8601 format "
            "with Asia/Taipei timezone "
            "(e.g., '2025-10-12T14:30:00+08:00'). "
            "Parse relative dates like '2 days ago' "
            "using the current_time provided in the system prompt. "
            "Return empty string if not found."
        ),
    )

    # Private attributes
    _html: str = pydantic.PrivateAttr(default="")
