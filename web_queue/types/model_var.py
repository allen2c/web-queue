import typing

import pydantic

ModelVar = typing.TypeVar("ModelVar", bound=pydantic.BaseModel)
