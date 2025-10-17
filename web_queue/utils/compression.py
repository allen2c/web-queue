import base64
import typing

import fastapi
import zstandard


def compress(
    data: str, *, level: int = 9, format: typing.Literal["zstd"] = "zstd"
) -> str:
    if format == "zstd":
        return base64.b64encode(
            zstandard.compress(data.encode("utf-8"), level=level)
        ).decode("utf-8")
    else:
        raise fastapi.exceptions.HTTPException(
            status_code=400, detail=f"Invalid format: {format}"
        )


def decompress(data: str, *, format: typing.Literal["zstd"] = "zstd") -> str:
    if format == "zstd":
        return zstandard.decompress(base64.b64decode(data.encode("utf-8"))).decode(
            "utf-8"
        )
    else:
        raise fastapi.exceptions.HTTPException(
            status_code=400, detail=f"Invalid format: {format}"
        )
