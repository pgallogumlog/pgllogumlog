"""
Run this script once to authorize Google Sheets access.
A browser will open - sign in with agentforgeworkflows@gmail.com and approve.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "config/google_sheets_credentials.json"
TOKEN_FILE = "config/sheets_token.pickle"

def authorize():
    print("Opening browser for Google Sheets authorization...")
    print("Sign in with: agentforgeworkflows@gmail.com")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "wb") as token:
        pickle.dump(creds, token)

    print()
    print("Authorization successful! Token saved to:", TOKEN_FILE)
    print("You can now run: python run_test.py")

if __name__ == "__main__":
    authorize()