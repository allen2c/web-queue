import functools

import openai
import pydantic as pydantic
import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    OPENAI_MODEL: str = pydantic.Field(default="gpt-4.1-nano")
    OPENAI_API_KEY: pydantic.SecretStr = pydantic.SecretStr("")

    @functools.cached_property
    def openai_client(self) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=self.OPENAI_API_KEY.get_secret_value())
