import requests
import json
from dateutil import parser
from datetime import datetime, timedelta
import pytz

own_tz = pytz.timezone('Europe/Amsterdam')
booking_tz = pytz.utc


def https_bookable_slots(days=7):
    """ 
    Returns the schedule / all bookable classes for the next x days
    """

    # Get today's date at 13:00 (local time) in UTC time.
    start = datetime.now(own_tz).replace(hour=13, minute=0, second=0, microsecond=0).astimezone(booking_tz)

    # Validaty of the https request (required for the request)
    available_from = datetime.now(booking_tz)
    available_till = available_from + timedelta(days=2)

    # If days = 1, get tomorrow's date at 14:00 (local time) in UTC time.
    # Else, get the date x days ahead at 23:00 (local time) in UTC time. 
    # Because in this case, we want to get ALL bookings of the day, not just the morning ones.
    if days == 1:
        end = datetime.now(own_tz).replace(hour=14, minute=0, second=0, microsecond=0).astimezone(booking_tz)
    else:
        end = datetime.now(own_tz).replace(hour=23, minute=0, second=0, microsecond=0).astimezone(booking_tz)

    end += timedelta(days=days)

    # Convert to required format
    start = start.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'
    end = end.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'
    available_from = available_from.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'
    available_till = available_till.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'

    # dit is een json
    parameters = {
        "s": '{"startDate":"%s","endDate":"%s","tagIds":{"$in":[1,12]},"availableFromDate":{"$gt":"%s"},"availableTillDate":{"$gte":"%s"}}' % (start, end, available_from, available_till)  
    }
    url = "https://backbone-web-api.production.delft.delcom.nl/bookable-slots"
    p = requests.get(url, params=parameters)


    if p.status_code != 200:
        raise Exception("Failed to request bookable slots. Error: %s" % p.text)
    data = json.loads(p.content)
    schedule = data['data']

    # Schedule is returned using AMS timezone!!
    return schedule


if __name__ == "__main__":
    data = https_bookable_slots(days=2)
    print(data)


    