import io

from configuraptor.helpers import as_binaryio

from src.drive_in import Drive
from uuid import uuid4

from src.drive_in.helpers import extract_google_id


def main():
    folder = '1zQoUrPpKQ7eTr4e3obwubrx1pSKun__t'

    custom_clientid = "327892950221-uaah9475qfsfp64s6nqa3o15a9eh3p67.apps.googleusercontent.com"
    custom_url = "https://oauth.trialandsuccess.nl/callback"

    drive = Drive(
        client_id=custom_clientid,
        redirect_uri=custom_url,
    )

    # url = drive.upload("kaggle.vst", folder="1zQoUrPpKQ7eTr4e3obwubrx1pSKun__t")
    url = "https://drive.google.com/file/d/1CzVnMH-3IfCagwKaWtWBiHFVa9SJuA3g/view"
    drive.download(url)

    return


    # with open("somefile", "wb") as f:
    #     drive.download(
    #         "https://drive.google.com/file/d/1P1EAjn_CYvsLpkOe0YoAMPZvQ7OVYoPj/view?usp=drive_link",
    #         "somefile",
    #     )

    # with open("somefile", "w") as f:
    #     drive.download(
    #         "https://drive.google.com/file/d/1P1EAjn_CYvsLpkOe0YoAMPZvQ7OVYoPj/view?usp=drive_link",
    #         f
    #     )

    # output = io.StringIO()
    # print(
    #     drive.download("https://drive.google.com/file/d/1P1EAjn_CYvsLpkOe0YoAMPZvQ7OVYoPj/view?usp=drive_link",
    #                    output
    #                    )
    # )
    #
    # print(
    #     output.read()
    # )

    file_url = drive.upload(io.BytesIO(b"Test"), filename="some_example.txt", folder=folder)
    file_id = extract_google_id(file_url)

    for file in drive.get("files").data['files']:
        if file['id'] == file_id:
            tempfile = io.StringIO()
            drive.download(file_id, tempfile)

            with as_binaryio(tempfile):
                assert tempfile.read() == "Test"

            endpoint = drive.endpoint("files") / file_id
            result = drive.delete(endpoint)

            assert result.success
            assert result._response.status_code == 204  # no content, is fine
            break


if __name__ == '__main__':
    main()
