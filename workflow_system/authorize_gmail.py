"""
Gmail OAuth Authorization Script.

Run this once to authorize Gmail access and create the token file.
The token will be saved to config/gmail_token.pickle and reused for future requests.

Usage:
    python authorize_gmail.py
"""

import os
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

CREDENTIALS_FILE = "config/google_credentials.json"
TOKEN_FILE = "config/gmail_token.pickle"


def authorize_gmail():
    """Run Gmail OAuth flow and save credentials."""
    print("=" * 60)
    print("Gmail OAuth Authorization")
    print("=" * 60)

    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"\nERROR: {CREDENTIALS_FILE} not found!")
        print("Please download OAuth credentials from Google Cloud Console")
        print("and save them to config/google_credentials.json")
        return False

    creds = None

    # Check for existing token
    if os.path.exists(TOKEN_FILE):
        print(f"\nFound existing token: {TOKEN_FILE}")
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("\nRefreshing expired token...")
            creds.refresh(Request())
        else:
            print("\nStarting OAuth flow...")
            print("   A browser window will open")
            print("   Please sign in and authorize Gmail access")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials
        print(f"\nSaving credentials to {TOKEN_FILE}")
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    else:
        print("\nToken is valid")

    # Test the connection
    print("\nTesting Gmail API connection...")
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        print(f"\nSUCCESS! Connected to Gmail")
        print(f"   Email: {profile.get('emailAddress')}")
        print(f"   Messages: {profile.get('messagesTotal')}")
    except Exception as e:
        print(f"\nERROR testing connection: {e}")
        return False

    print("\n" + "=" * 60)
    print("Gmail authorization complete!")
    print("=" * 60)
    print(f"\nToken saved to: {TOKEN_FILE}")
    print("You can now send emails using the workflow system.")
    print("\nTo test email sending:")
    print("  python run_test.py --send-emails --tier standard --count 1")
    print("=" * 60)

    return True


if __name__ == "__main__":
    authorize_gmail()
