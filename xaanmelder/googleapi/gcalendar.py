from __future__ import print_function

import math
from datetime import datetime, timedelta

import pytz
from dateutil import parser

from xaanmelder.googleapi.OAuth.oauth import get_calendar_service

own_tz = pytz.timezone('Europe/Amsterdam')
booking_tz = pytz.utc




def add_schedule_booking_to_calendar(booking, booked=True):
    """
    Add a booking (from https_schedule) to your calendar.
    @param booking needs to be a booking item from 'schedule'.
    @param booked is usually True because in the main loop you only call this function
    after a booking succeeds.
    """
    title = booking['Description']
    start = parser.parse(booking['Start_date']).astimezone(own_tz)
    end = parser.parse(booking['End_date']).astimezone(own_tz)
    # Sometimes no trainer information is available
    if 'First_name' and 'Last_name' in booking:
        trainer = booking['First_name'] + " " + booking["Last_name"]
    else:
        trainer = ""
    location = booking['Location']

    add_calendar_event(title, start, end, location, trainer, booked=booked)
    return True


def add_calendar_event(title, start, end, location, trainer, booked=False):
    """ Add an event to the calendar
    Parameters:
        title: string, e.g., "Body power all levels"
        start: datetime object with Europe/Amsterdam timezone
        end: datetime object with Europe/Amsterdam timezone
        location: string, e.g., "Aerobics"
        trainer: string, e.g., "Marina"
        booked: boolean whether this event has been booked succesfully.
    """

    service = get_calendar_service()
    if service is None: return False

    # Check if event is already in calendar.
    event_id = find_event(title, start)
    if event_id is not None:
        print("Event already in calendar")
        if booked: set_event_booked(event_id)
        return True

    # If event does not exist yet, make it.
    event = {
        'summary': title,
        'location': location,
        'colorId': "6",
        'description': 'Trainer: %s\nCalendar event added by xaanmelder.' % trainer,
        'start': {
            'dateTime': start.isoformat(),
            'timeZone': 'Europe/Amsterdam',
        },
        'end': {
            'dateTime': end.isoformat(),
            'timeZone': 'Europe/Amsterdam',
        }

    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    if booked: set_event_booked(event['id'])
    # print('Event created: %s' % (event.get('htmlLink')))
    print("Added event to calendar.")
    return True


def find_event(title, start):
    """ Check if event exists in calendar.
    Returns id of the event or 'None' if it doesn't exist.
    Parameters:
        title: string, e.g., "Body power all levels"
        start: datetime object with Europe/Amsterdam timezone
    """
    service = get_calendar_service()
    if service is None: return False

    # Search for the event by filtering for start time one second before 'start' en one second after 'start'
    from_t = (start - timedelta(seconds=1)).astimezone(pytz.utc).isoformat()[:-6] + 'Z'
    until_t = (start + timedelta(seconds=1)).astimezone(pytz.utc).isoformat()[:-6] + 'Z'
    events = service.events().list(calendarId='primary', timeMin=from_t, timeMax=until_t).execute()

    # Check if name of event is the same as the event we are looking for.
    for event in events['items']:
        # Check if the title matches. Use 'in' statement because there might be '(booked)' added to the summary.
        if title in event['summary']:
            return event['id']
    return None


def set_event_booked(event_id):
    """ Update an existing event with id @param event_id
    to show the user it has been booked. Two adjustments:
    1. Add (booked) to the title.
    2. Set reminder to send a reminder directly after the booking.
    """
    service = get_calendar_service()
    if service is None: return False

    event = service.events().get(calendarId='primary', eventId=event_id).execute()

    # Check if event is already set to 'booked'
    if 'booked' in event['summary']:
        print("Event is already set to 'booked'.")
        return

    event['summary'] = event['summary'] + " (booked)"

    # Minutes left until reservation (used for sending the reminder immediately after creating the event).
    # Do -1 to have some slack between creating the event and sending the reminder.
    minutes_left = math.floor(
        (parser.parse(event['start']['dateTime']) - datetime.now(tz=own_tz)).total_seconds() / 60) - 1
    event['reminders'] = {
        'useDefault': False,
        'overrides': [
            # {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 60},
            {'method': 'popup', 'minutes': minutes_left}]}

    # Update event
    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
    print("Succesfully set event to 'booked'.")
    return


def get_all_x_aanmelder_events():
    """
    Return all events in the calendar that are made by this script from now until 10 days ahead.
    """
    service = get_calendar_service()
    if service is None: return False

    x_aanmelder_events = list()

    # Search for all events in the time period now - 10 days later.
    from_t = datetime.utcnow().isoformat() + 'Z'
    until_t = (datetime.utcnow() + timedelta(days=10)).isoformat() + 'Z'
    events = service.events().list(calendarId='primary', timeMin=from_t, timeMax=until_t).execute()

    # Find the events that are made by this script by looking at the description of the event (if description exists).
    # When making an event with this script, the description contains the word 'xaanmelder'
    # This can be seen in add_calendar_event()
    for event in events['items']:
        if 'description' in event and 'xaanmelder' in event['description']:
            x_aanmelder_events.append(event)

    return x_aanmelder_events


def remove_event(event_id):
    """ Remove event with a certain id from the calendar. """
    service = get_calendar_service()
    if service is None: return False

    service.events().delete(calendarId='primary', eventId=event_id).execute()
    print("Removed event from calendar.")


def update_event_location(event, new_location):
    service = get_calendar_service()
    if service is None: return False

    event['location'] = new_location
    # Update event
    updated_event = service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()


if __name__ == '__main__':
    service = get_calendar_service()
    if service is None:
        print("Calendar not setup correctly.")
        quit()

    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
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
