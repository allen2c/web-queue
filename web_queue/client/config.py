import functools
import pathlib
import typing

import cachetic
import openai
import pydantic as pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    OPENAI_MODEL: str = pydantic.Field(default="gpt-4.1-nano")
    OPENAI_API_KEY: pydantic.SecretStr = pydantic.SecretStr("")

    # Cache
    WEB_CACHE_PATH: typing.Text = pydantic.Field(default="./.cache/web.cache")
    WEB_CACHE_EXPIRE_SECONDS: int = pydantic.Field(default=60 * 60 * 24)  # 1 day
    COMPRESSED_BASE64_CACHE_PATH: typing.Text = pydantic.Field(
        default="./.cache/compressed_base64.cache"
    )
    COMPRESSED_BASE64_CACHE_EXPIRE_SECONDS: int = pydantic.Field(
        default=60 * 60 * 24
    )  # 1 day

    @functools.cached_property
    def openai_client(self) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=self.OPENAI_API_KEY.get_secret_value())

    @functools.cached_property
    def web_cache(self) -> "cachetic.Cachetic[typing.Text]":
        import cachetic

        return cachetic.Cachetic(
            object_type=pydantic.TypeAdapter(typing.Text),
            cache_url=pathlib.Path(self.WEB_CACHE_PATH),
            default_ttl=self.WEB_CACHE_EXPIRE_SECONDS,
        )

    @functools.cached_property
    def compressed_base64_cache(self) -> "cachetic.Cachetic[typing.Text]":
        import cachetic

        return cachetic.Cachetic(
            object_type=pydantic.TypeAdapter(typing.Text),
            cache_url=pathlib.Path(self.COMPRESSED_BASE64_CACHE_PATH),
            default_ttl=self.COMPRESSED_BASE64_CACHE_EXPIRE_SECONDS,
        )
