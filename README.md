A Python script to batch upload videos to YouTube with automatic Shorts detection and customizable metadata.

⚠️ Important Security Notice ⚠️
NEED TO CHANGE VARIABLES WITH CHANGE >>>>>>>
USE YOUR OWN API CREDENTIALS
The script doesn't contain the OAuth credentials needed. You must:

Create your own Google Cloud project

Enable YouTube Data API v3

Generate your own OAuth 2.0 credentials

Replace the credentials in the script

going here:
https://console.cloud.google.com/apis/credentials

Follow this if for exact instructions:
https://developers.google.com/youtube/registering_an_application

Quick Start
Install requirements:

bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
Set your video folder path in the script:

python
VIDEO_FOLDER = "path/to/your/videos"

and edit this according to your own credentials:
CREDENTIALS_DATA = {
    "installed": {
        "client_id": "CHANGE >>>>>>> YOUR CLIENT ID",
        "project_id": "CHANGE >>>>>>> PROJECT ID",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": " CHANGE >>>>>>> CLIENT SECRET",
        "redirect_uris": [
            "http://localhost"
        ]
    }
}
Run the script:

bash
python youtube_upload.py
Features
Batch upload from any folder

Automatic YouTube Shorts detection (files starting with "shorts")

Custom titles/descriptions/tags

Privacy status control (public/unlisted/private)

Progress logging
