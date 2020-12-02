from __future__ import print_function

import math
import os.path
import pickle
from datetime import datetime

from dateutil import parser
from googleapiclient.discovery import build


def is_calendar_available():
    """ Check if calendar is authenticated and can be used. """
    calendar_dir = os.path.dirname(os.path.realpath(__file__))
    try:
        if os.path.exists(calendar_dir + '/token.pickle'):
            with open(calendar_dir + '/token.pickle', 'rb') as token:
                creds = pickle.load(token)
                if creds and creds.valid:
                    return True
                else:
                    print("Google Calendar not available. Check README to set it up.")
                    return False
        else:
            return False
    except:
        print("Google Calendar not available. Check README to set it up.")
        return False

def get_calendar_service():
    """ Returns the calendar service that can be used for adding events to the calendar. """
    creds = None
    calendar_dir = os.path.dirname(os.path.realpath(__file__))
    if os.path.exists(calendar_dir + '/token.pickle'):
        with open(calendar_dir + '/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    service = build('calendar', 'v3', credentials=creds)
    return service

def add_booking_to_calendar(booking, booked=True):
    """
    Add a booking to your calendar.
    @param booking needs to be a booking item from 'schedule'. """
    title = booking['Description']
    if booked: title = title + " (Booked)"
    start = parser.parse(booking['Start_date'])
    end = parser.parse(booking['End_date'])
    trainer = booking['First_name'] + " " + booking["Last_name"]
    location = booking['Location']

    # Minutes left until reservation (used for sending the reminder immediately after creating the event).
    # Do -1 to have some slack between creating the event and sending the reminder.
    minutes_left = math.floor((start - datetime.utcnow()).total_seconds()/60) - 1

    service = get_calendar_service()

    event = {
        'summary': title,
        'location': location,
        'description': 'Trainer: ' + trainer,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'Europe/Amsterdam',
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'Europe/Amsterdam',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                #{'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
                {'method': 'popup', 'minutes': minutes_left}
            ],
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    #print('Event created: %s' % (event.get('htmlLink')))
    print("Added event to calendar.")
    return True

if __name__ == '__main__':
    service = create_calendar_service()
    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
