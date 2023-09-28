# Drive-in

Minimalistic Google Drive Library for Python.

<div align="center">
    <a href="https://pypi.org/project/drive-in"><img alt="PyPI - Version" src="https://img.shields.io/pypi/v/drive-in.svg"/></a>
    <a href="https://pypi.org/project/drive-in"><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/drive-in.svg"/></a>
    <br/>
    <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"/></a>
    <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"/></a>
    <br/>
    <a href="https://github.com/robinvandernoord/drive-in/actions"><img alt="su6 checks" src="https://github.com/robinvandernoord/drive-in/actions/workflows/su6.yml/badge.svg?branch=development"/></a>
</div>

-----

**Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Features

- **Authentication**: Easily authenticate with Google Drive using OAuth 2.0, and store the access token for future use.
  Drive-In provides a CLI authentication process, guiding you through token creation.

- **File Upload**: Seamlessly upload files to your Google Drive, with support for multi-part uploads. You can specify
  the file's name and the destination folder.

- **File Download**: Download files from Google Drive, also with multipart support. *

- **API Interaction**: Interact with the Google Drive API through a simplified interface, making it effortless to
  perform operations like creating, updating, and deleting files or folders. *

- **Error Handling**: Drive-In includes error handling to help you handle unexpected situations, such as failed API
  requests.

_* Due to Authentication Limitations, you can only view and edit files that were created using this tool._

## Installation

```console
pip install drive-in
```

## Usage

First, import the library and create an instance of the `Drive` class:

```python
from drive_in import Drive

drive = Drive()
```

This will prompt the user for authentication.

### Checking Authentication Status

```python
# Check if the authentication token is valid
if drive.ping():
    print("Authentication is successful and server responds well.")
else:
    print("Authentication failed.")
```

### Uploading a File

```python
# Upload a file to Google Drive
file_path = "example.txt"
drive.upload(file_path)
```

### Downloading a File

```python
# Download a file from Google Drive 
file_id = "your_file_id_here"
downloaded_file = drive.download(file_id)
# if no output target is passed, it is saved to the same name as it has on drive. 
# A reference to the file handle is returned.
```

### Accessing other Drive API Endpoints

Other than `upload` and `download`, you can access REST resources with the HTTP verbs (GET, POST, PATCH, DELETE):

```python
drive.get("files")  # perform GET /drive/v3/files
# returns a Result object which has .success (bool) and .data (dict) properties.
# _response and _url internal properties are available if you need access to this raw info.

drive.post("files/123/comments", data=dict(content="...")) # perform POST to create a new comment.

drive.delete("files/123")  # perform DELETE /drive/v3/files/123

resource = drive.resource("files") / 123  # dynamically build up the resource string
drive.delete(resource)  # also performs DELETE /drive/v3/files/123
```

See [the Google Drive API page](https://developers.google.com/drive/api/reference/rest/v3) for information about
available resources.

## Authentication
This library works only a public OAuth Client ID. 
Since it is open source, a secret config or key can not be shared. 
This leads to some limitations with how much the app can access. 
Unfortunately, you can only access files created by this app (i.e. uploaded by it).

### OAuth Callback
Since oauth requires a callback URL, you're redirected to "https://oauth.trialandsuccess.nl/callback" after logging in.
This page simply echoes the access token from the request parameters using [oauth-echoer](https://github.com/trialandsuccess/oauth-echoer).

You can also provide you own Client ID and callback URL when initializing a Drive instance:
```python
custom_clientid = "123-abc.apps.googleusercontent.com"
custom_url = "https://yoursite.com/callback"

drive = Drive(
    client_id=custom_clientid,
    redirect_uri=custom_url,
  )
```

## License

`drive-in` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

*Disclaimer: This library is not officially affiliated with Google Drive or Google LLC. It is an open-source project
created to simplify interactions with Google Drive's API.*