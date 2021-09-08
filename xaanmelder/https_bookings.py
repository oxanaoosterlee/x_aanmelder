import requests
import json
from dateutil import parser
from datetime import datetime, timedelta
import pytz
from https_locations import https_locations

own_tz = pytz.timezone('Europe/Amsterdam')
booking_tz = pytz.utc


def https_bookings(days=1):
    """ Returns all scheduled classes between a specified start and end time/date.
    Note that for this request, all times in the request/respond are in UTC time.
    """

    url = "https://services.sc.tudelft.nl/api/v1/bookings"
    # Get bookings for today 13:00 - next day 14:00.

    # Get today's date at 13:00 (local time) in UTC time.
    start = datetime.now(own_tz).replace(hour=13, minute=0, second=0, microsecond=0).astimezone(booking_tz)
    # Get the current time in UTC time
    #start = datetime.now(booking_tz)

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

    # Locations that we want to go to
    location_names = ["Aerobics", "FTO Aerobics", "FTO Body & Mind", "Body & Mind", "FTO Combat", "Combat"]

    # Convert location strings to location IDs
    locations = [https_locations(loc) for loc in location_names]
    locations = '["' + '", \"'.join(locations) + '"]'

    data = '{"start":"' + start + '", "end":"' + end + '","locations":' + locations + '}'
    headers = {
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://services.sc.tudelft.nl',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Referer': 'https://services.sc.tudelft.nl/?lang=en',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    p = requests.post(url, headers=headers, data=data.encode())
    if p.status_code != 200:
        raise Exception("Failed to request bookings. Error: %s" % p.text)

    data = json.loads(p.content)

    # Remove bookings that are not bookable classes.
    data = [x for x in data if not x['max_participants'] == 1]

    # Bookings are returned using UTC timezone!!!!

    return data

    # Location ids

if __name__ == "__main__":
    data = https_bookings()
    print(data)


    