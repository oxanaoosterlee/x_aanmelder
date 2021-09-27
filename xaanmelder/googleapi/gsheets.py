import numpy as np
import pandas as pd
import pytz
from dateutil import parser

from .OAuth.oauth import get_sheets_service

own_tz = pytz.timezone('Europe/Amsterdam')

SPREADSHEET_ID = '1m1WMCQzaLLQEHYvcS-P3ytFGeBO3s4okUDvt8nID5FE'
RANGE_NAME = 'Sheet1!A1:H'


def get_sheet_data():
    """ Read the (old) attendance dataframe from googleapi sheets. """
    service = get_sheets_service()
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    # If sheet is empty, return empty dataframe.
    if len(values) == 0:
        return pd.DataFrame([],[])

    # Make sure each row has the required number of elements (equal to the number of column headers).
    for row in values[1:]:
        if len(row) < len(values[0]):
            row.append(None)

    df = pd.DataFrame(values[1:], columns=values[0])

    # Change 'Start' and 'End' columns to DateTime formats for easier handling.
    # Only necessary when dataframe is not empty
    if not df.empty:
        df['Start'] = df.apply(lambda x: parser.parse(x.Date + " " + x.Start, dayfirst=True).astimezone(own_tz), axis=1)
        df['End'] = df.apply(lambda x: parser.parse(x.Date + " " + x.End, dayfirst=True).astimezone(own_tz), axis=1)


    # Convert None to NaN
    df = df.fillna(value=np.nan)
    print("Got sheet data: " + str(df))

    return df


def write_sheet_data(attendance_df):
    """ Write new attendance data to Google sheet."""
    print("Writing data to google sheet.")
    # Convert time back to readible format
    # Need to make copy otherwise the column operations are applied to the original dataframe.
    copy = attendance_df.copy()
    # Change 'Start' and 'End' columns to something more readable.
    copy['Start'] = copy.apply(lambda x: x.Start.strftime("%H:%M"), axis=1)
    copy['End'] = copy.apply(lambda x: x.End.strftime("%H:%M"), axis=1)

    service = get_sheets_service()
    sheet = service.spreadsheets()

    response_date = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        valueInputOption='RAW',
        range=RANGE_NAME,
        body=dict(
            majorDimension='ROWS',
            values=copy.T.reset_index().T.values.tolist())
    ).execute()

def gsheets_available():
    service = get_sheets_service()
    if service is None:
        print("Google sheet not available. Please refer to README.")
        return False

    sheet = service.spreadsheets()
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    except:
        print("Google sheet not available. Please refer to README.")
        return False
    return True

if __name__ == "__main__":
    data = get_sheet_data()
    print(data)
