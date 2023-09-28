"""
Re-usable types.
"""

import typing
from dataclasses import dataclass, field

from requests import Response
from yayarl import URL

AnyDict = dict[str, typing.Any]


class BaseDriveInException(Exception):
    """
    Every exception in this library should inherit from this one.
    """


@dataclass
class UploadError(BaseDriveInException):
    """
    Raised when something goes wrong while uploading to Drive.
    """

    status_code: int
    message: str


@dataclass
class DownloadError(BaseDriveInException):
    """
    Raised when something goes wrong while uploading to Drive.
    """

    status_code: int
    message: str


@dataclass
class Result:
    """
    Container for API request responses.
    """

    success: bool
    data: AnyDict
    _response: Response = field(repr=False)
    _url: URL | None = field(repr=False)


T = typing.TypeVar("T", str, bytes)
