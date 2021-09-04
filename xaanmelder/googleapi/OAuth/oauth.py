from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/spreadsheets']

def authenticate():
    """ Get user credentials using Google OAuth authentication so that Google API can be used.
    Requires a file 'credentials.json' in the data/oauth directory, which can be
    retrieved from the Google Console.
    """
    creds = None
    oauth_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))) + '/data/oauth/'
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(oauth_dir + 'token.json'):
        creds = Credentials.from_authorized_user_file(oauth_dir + 'token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(oauth_dir + 'credentials.json'):
                print("OAuth not setup. Please refer to README")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                oauth_dir + 'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(oauth_dir + 'token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_calendar_service():
    creds = authenticate()
    if creds is None: return None
    try:
        service = build('calendar', 'v3', credentials=creds)
    except:
        return None
    return service


def get_sheets_service():
    service = None
    creds = authenticate()
    if creds is None: return None
    try:
        service = build('sheets', 'v4', credentials=creds)
    except:
        return None
    return service


if __name__ == "__main__":
    creds = authenticate()
    if creds is not None: print("Google authentication succeeded.")
    else:
        print("Authentication failed.")