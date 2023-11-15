"""
Simple API to simplify working with Google Drive.
"""
from __future__ import annotations

import json
import os
import typing
import uuid
import warnings
from pathlib import Path

import requests
import tqdm
from configuraptor import Singleton
from configuraptor.helpers import as_binaryio
from yayarl import URL

from ._constants import AUTH_TOKEN_FILE, CLIENT_ID, REDIRECT_URI, SCOPE
from .helpers import OutputManager, extract_google_id, get_size
from .types import AnyDict, DownloadError, Result, T, UploadError

try:
    from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError
except ImportError:

    class RequestsJSONDecodeError(json.JSONDecodeError):  # type: ignore
        """
        Fallback for older versions of `requests`.
        """


class Drive:  # pragma: no cover
    """
    Simplified class that allows authenticate and uploading (multi part).
    """

    version = "v3"

    token: str

    auth_url = URL("https://accounts.google.com/o/oauth2/v2/auth")
    base_url = URL("https://www.googleapis.com/drive") / version
    upload_url = URL("https://www.googleapis.com/upload/drive/") / version

    def __init__(self, token: str = None, **kw: typing.Any) -> None:
        """
        Provide an existing access_token or be prompted to create one.
        """
        self.token = token or self.authenticate(**kw)
        self.ping()

    def generate_headers(self) -> dict[str, str]:
        """
        After .authenticate(), create default auth header.
        """
        return {
            "Authorization": f"Bearer {self.token}",  # Replace with your access token
            "Content-Type": "application/json; charset=UTF-8",
        }

    def endpoint(self, resource: str) -> URL:
        """
        Return an URL object to a specific resource.
        """
        # https://developers.google.com/drive/api/reference/rest/v3
        return self.base_url / resource

    def _handle_resp(self, resp: requests.Response, url: URL | None = None) -> Result:
        if resp.status_code > 399:
            warnings.warn(f"Response to {url} failed with status code {resp.status_code}")

        try:
            data = resp.json()
            data = typing.cast(AnyDict, data)
        except (json.JSONDecodeError, RequestsJSONDecodeError):
            data = {}

        return Result(
            success=resp.status_code < 400,
            data=data or {},
            _url=url,
            _response=resp,
        )

    def _build_url(self, resource: str | URL, session: requests.Session | None) -> URL:
        url = self.endpoint(resource) if isinstance(resource, str) else resource

        if session:
            url &= session

        return url

    def get(
        self, resource: str | URL, data: AnyDict = None, session: requests.Session = None, **kwargs: typing.Any
    ) -> Result:
        """
        GET a resource.

        Supports everything from `requests.get`.
        """
        url = self._build_url(resource, session)
        url %= data or {}

        headers = self.generate_headers() | kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 5)

        resp = url.get(headers=headers, timeout=timeout, **kwargs)

        return self._handle_resp(resp, url)

    def post(
        self, resource: str | URL, data: AnyDict = None, session: requests.Session = None, **kwargs: typing.Any
    ) -> Result:
        """
        POST a resource.

        Supports everything from `requests.post`.
        """
        url = self._build_url(resource, session)

        headers = self.generate_headers() | kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 5)

        resp = url.post(headers=headers, json=data, timeout=timeout, **kwargs)

        return self._handle_resp(resp, url)

    def patch(
        self, resource: str | URL, data: AnyDict = None, session: requests.Session = None, **kwargs: typing.Any
    ) -> Result:
        """
        PATCH a resource.

        Supports everything from `requests.patch`.
        """
        url = self._build_url(resource, session)

        headers = self.generate_headers() | kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 5)

        resp = url.patch(headers=headers, json=data, timeout=timeout, **kwargs)

        return self._handle_resp(resp, url)

    def delete(
        self, resource: str | URL, data: AnyDict = None, session: requests.Session = None, **kwargs: typing.Any
    ) -> Result:
        """
        DELETE a resource.

        Supports everything from `requests.delete`.
        """
        url = self._build_url(resource, session)
        url %= data or {}

        headers = self.generate_headers() | kwargs.pop("headers", {})
        timeout = kwargs.pop("timeout", 5)

        resp = url.delete(headers=headers, timeout=timeout, **kwargs)

        return self._handle_resp(resp, url)

    def ping(self, session: requests.Session = None) -> bool:
        """
        Make sure the authentication token works and the API responds normally.
        """
        result = self.get("about", {"fields": "kind"}, session=session)

        return result.success and result.data.get("kind") == "drive#about"

    def _load_token(self) -> str:
        with open(AUTH_TOKEN_FILE, "r") as f:
            return f.read()

    def _store_token(self, token: str) -> None:
        with open(AUTH_TOKEN_FILE, "w") as f:
            f.write(token)

    def _remove_token(self) -> None:
        if os.path.exists(AUTH_TOKEN_FILE):
            os.unlink(AUTH_TOKEN_FILE)

    def authenticate_cached(self) -> str | None:
        """
        Load a previous token from a file on disk.

        If the file fails, remove it.
        """
        try:
            self.token = self._load_token()
            if self.ping():  # could crash if invalid auth, should do normal authenticate() in that case.
                return self.token
            else:
                raise ValueError("ping failed")
        except Exception:
            self._remove_token()
            return None

    def authenticate(
        self, scope: str = SCOPE, redirect_uri: str = REDIRECT_URI, client_id: str = CLIENT_ID, cache: bool = True
    ) -> str:
        """
        CLI-authenticate: print the URL and prompt for access token.

        Uses oauth.trialandsuccess.nl since a callback URL is required.
         Other methods that do not require a callback, expect a private key or secure config which is not
         feasible for an open source library.
        """
        if cache and (token := self.authenticate_cached()):
            return token

        # Construct the URL
        print(
            self.auth_url
            % {
                "scope": scope,
                "include_granted_scopes": "true",
                "response_type": "token",
                "state": str(uuid.uuid4()),
                "redirect_uri": redirect_uri,
                "client_id": client_id,
            }
        )

        token = input("Please paste your token here: ")

        if cache:
            self._store_token(token)

        return token

    def download(
        self,
        file_id: str,
        to_file: str | Path | typing.IO[T] | None = None,
        chunks_size_mb: int = 25,
        overwrite: bool = True,
    ) -> typing.IO[T]:
        """
        Download a file in multiple chunks.

        The downloaded file can be written to a file by name, open object or Path. If no file is passed,
        the name from the metadata will be used.

        file_id can be an ID or a full URL to the file.

        Examples:
             drive.download("<some id>", "output.txt")

             with open('myfile, 'wb') as f:
                drive.download("<some id>", f)


             with open('myfile, 'w') as f:
                drive.download("<some id>", f)

            drive.download("<some id>", io.BytesIO())

            drive.download("<some id>", io.StringIO())

            drive.download("<some id>")

        """
        file_id = extract_google_id(file_id)
        url = self.base_url / "files" / file_id

        with requests.Session() as session:
            # bytesio, stringio
            # bytesio, bytesio
            # bufferedwriter, bufferedwriter
            # bytesio, textiowrapper
            url &= session
            metadata = self.get(url)

            if not metadata.success:
                raise DownloadError(
                    status_code=metadata._response.status_code,
                    message=metadata._response.text,
                )

            if to_file is None:
                filepath = Path(metadata.data["name"])
                if filepath.exists() and not overwrite:
                    raise ValueError(
                        f"File {filepath} already exists. "
                        f"Either remove it, choose a custom filename or set overwrite to True."
                    )

                to_file = filepath

            with OutputManager(to_file) as (temp_file, output):
                self._download_chunks(url % {"alt": "media"}, chunks_size_mb, temp_file)
                return output

    def _download_chunks(
        self,
        url: URL,
        chunks_size_mb: int,
        tempfile: typing.BinaryIO,
        total_content_length: int = None,
    ) -> None:
        chunk_size = chunks_size_mb * 1024 * 1024
        start = 0
        current_content_length = 0
        with tqdm.tqdm(total=total_content_length or 0, unit="B", unit_scale=True, unit_divisor=1024) as progress:
            while True:
                end = start + chunk_size - 1

                result = self.get(url, headers={"Range": f"bytes={start}-{end}"})
                byterange: str = result._response.headers["Content-Range"].split("-")[-1]

                len_info = byterange.split("/")
                start = int(len_info[0]) + 1

                if not total_content_length:
                    total_content_length = int(len_info[1])
                    progress.reset(total_content_length)

                content = result._response.content
                tempfile.write(content)

                current_content_length += len(content)
                progress.update(len(content))

                if current_content_length < total_content_length:
                    continue
                else:
                    break

    def upload(
        self,
        file_path: str | Path | typing.BinaryIO,
        filename: str = None,
        folder: str = None,
        chunks_size_mb: int = 25,
    ) -> str:
        """
        Upload a file in multiple chunks.

        file_path can be either a path to a file, or an in-memory file-like object (bytesio).

        Returns the new file url.
        """
        if isinstance(file_path, Path):
            file_path = str(file_path.resolve())

        if not filename and isinstance(file_path, str):
            filename = os.path.basename(file_path)

        with requests.Session() as session, as_binaryio(file_path) as file_obj:
            location = self._initialize_upload(filename, folder, session)

            total_size = os.path.getsize(file_path) if isinstance(file_path, str) else get_size(file_obj)
            self._upload_chunks(file_obj, total_size, location, session, chunks_size_mb)

            metadata = self._finalize_upload(location, session)

        return f"https://drive.google.com/file/d/{metadata['id']}/view"

    def _initialize_upload(self, filename: str | None, folder: str | None, session: requests.Session) -> str:
        metadata: dict[str, str | list[str]] = {
            "name": filename or "model.vst",
        }
        if folder:
            metadata["parents"] = [folder]
        resp = session.post(
            str(
                self.upload_url
                / "files"
                % {
                    "uploadType": "resumable",
                }
            ),
            headers=self.generate_headers(),
            json=metadata,
            timeout=10,
        )
        return resp.headers["Location"]

    def _upload_chunks(
        self, file: typing.BinaryIO, total_size: int, location: str, session: requests.Session, chunks_size_mb: int
    ) -> None:
        chunk_size = chunks_size_mb * 1024 * 1024  # 50MB chunk size (you can adjust this)
        with tqdm.tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024) as progress:
            start_byte = 0
            while start_byte < total_size:
                end_byte = start_byte + chunk_size - 1
                if end_byte >= total_size:
                    end_byte = total_size - 1

                headers = {
                    "Content-Length": str(end_byte - start_byte + 1),
                    "Content-Range": f"bytes {start_byte}-{end_byte}/{total_size}",
                }

                response = session.put(location, headers=headers, data=file.read(chunk_size), timeout=60)

                if response.status_code > 399:
                    raise UploadError(response.status_code, response.text)

                progress.update(end_byte - start_byte + 1)
                start_byte = end_byte + 1

    def _finalize_upload(self, location: str, session: requests.Session) -> dict[str, str]:
        # Step 3: Finalize the upload with a 200 status code
        headers = {"Content-Length": "0"}
        response = session.put(location, headers=headers, timeout=5)
        if response.status_code != 200:
            raise UploadError(response.status_code, response.text)
        metadata = response.json()
        return typing.cast(dict[str, str], metadata)


class DriveSingleton(Drive, Singleton):
    """
    Make sure authentication only happens once, even if trying to create multiple instances.

    (e.g. calling to_drive() multiple times will try to create new Drive objects, but we want to keep the auth info.)
    """
