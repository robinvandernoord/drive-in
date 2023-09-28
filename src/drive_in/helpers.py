"""
Reusable helpers.
"""

import io
import os
import re
import types
import typing
from pathlib import Path

GOOGLE_ID_RE = re.compile(r"[-\w]{25,}")


def extract_google_id(url: str) -> str:
    """
    From a Google Drive File URL, extract the unique file ID.
    """
    return next(GOOGLE_ID_RE.finditer(url)).group(0) or ""


def get_size(file_obj: io.BytesIO | io.BufferedReader | typing.BinaryIO) -> int:
    """
    Get the size of a file object or in memory file.

    File Examples:
        - io.BytesIO()
        - open("myfile", "rb")
    """
    if isinstance(file_obj, io.BytesIO):
        return file_obj.getbuffer().nbytes
    else:
        # buffered reader
        return os.fstat(file_obj.fileno()).st_size


class OutputManager:
    """
    Context manager that deals with multiple (pseudo) file objects.
    """

    output: typing.IO[typing.Any] | None

    def __init__(self, to_file: str | Path | typing.IO[typing.Any] | None) -> None:
        """
        On create.
        """
        self.to_file = to_file
        self.output = None

    def __enter__(self) -> tuple[typing.BinaryIO, typing.IO[typing.Any]]:
        """
        When starting the ctx manager.
        """
        if self.to_file is None:
            self.output = self.to_file = io.BytesIO()
        elif isinstance(self.to_file, str):
            self.output = self.to_file = Path(self.to_file).open("wb")  # noqa: SIM115
        elif isinstance(self.to_file, Path):
            self.output = self.to_file = self.to_file.open("wb")
        elif isinstance(self.to_file, (io.StringIO, io.TextIOBase)):
            self.output = self.to_file
            self.to_file = io.BytesIO()
        else:
            self.output = self.to_file

        return typing.cast(typing.BinaryIO, self.to_file), self.output

    def __exit__(
        self, exc_type: typing.Type[BaseException], exc_value: BaseException, traceback: types.TracebackType | None
    ) -> typing.Literal[False]:
        """
        Executes on success and error.
        """
        if isinstance(self.output, io.BytesIO):
            self.output.seek(0)
        elif isinstance(self.output, (io.StringIO, io.TextIOBase)):
            self.to_file.seek(0)
            content = self.to_file.read().decode()
            self.output.write(content)
            self.output.seek(0)

        if isinstance(self.output, io.TextIOWrapper):
            self.output.close()

        return False  # Propagate any exceptions
