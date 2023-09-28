import io
import os

from configuraptor.helpers import as_binaryio

from src.drive_in import Drive
from uuid import uuid4

from src.drive_in.helpers import extract_google_id
from src.drive_in.types import BaseDriveInException


def main():
    folder = '1zQoUrPpKQ7eTr4e3obwubrx1pSKun__t'

    drive = Drive(
        # client_id=custom_clientid,
        # redirect_uri=custom_url,
    )

    file_url = drive.upload(io.BytesIO(b"Test"), filename="some_example.txt", folder=folder)
    file_id = extract_google_id(file_url)

    for file in drive.get("files").data['files']:
        if file['id'] == file_id:
            tempfile = io.StringIO()
            drive.download(file_id, tempfile)
            drive.download(file_id)

            exists = os.path.exists("some_example.txt")
            assert exists
            if exists:
                os.unlink("some_example.txt")

            with as_binaryio(tempfile):
                assert tempfile.read() == "Test"

            endpoint = drive.endpoint("files") / file_id
            result = drive.delete(endpoint)

            assert result.success
            assert result._response.status_code == 204  # no content, is fine
            break


if __name__ == '__main__':
    main()
