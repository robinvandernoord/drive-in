# drive_in

Minimalistic Google Drive Library for Python.

[![PyPI - Version](https://img.shields.io/pypi/v/drive-in.svg)](https://pypi.org/project/drive-in)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/drive-in.svg)](https://pypi.org/project/drive-in)

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

- **File Download**: Download files from Google Drive, although this part is a work in progress and requires further
  development.

- **API Interaction**: Interact with the Google Drive API through a simplified interface, making it effortless to
  perform operations like creating, updating, and deleting files or folders.

- **Error Handling**: Drive-In includes error handling to help you handle unexpected situations, such as failed API
  requests.

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
    print("Authentication is successful.")
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
```

### Accessing other Drive API Endpoints

```python
...
```

## License

`drive-in` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

*Disclaimer: This library is not officially affiliated with Google Drive or Google LLC. It is an open-source project
created to simplify interactions with Google Drive's API.*