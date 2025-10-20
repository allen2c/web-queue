import typing

StepCallbackType: typing.TypeAlias = typing.Callable[
    [
        typing.Annotated[int, "total_steps"],
        typing.Annotated[int, "completed_steps"],
        typing.Annotated[str, "message"],
    ],
    None,
]
