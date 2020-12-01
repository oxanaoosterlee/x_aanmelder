import requests
import json
from dateutil import parser
from datetime import datetime
import pytz

own_tz = pytz.timezone('Europe/Amsterdam')
booking_tz = pytz.utc


def https_bookings():
    """ Returns all scheduled classes between a specified start and end time/date. """

    url = "https://services.sc.tudelft.nl/api/v1/bookings"
    start = "2020-11-30T00:00:00.000Z"  # In UTC time. Example: 2020-11-30T00:00:00.000Z
    end = "2020-11-30T22:59:59.999Z"

    # Body&Mind: '67423d08-2113-444f-8a5e-3e97f479078f'
    # Aerobics: 'f2ae664c-f420-4609-8933-89eb8010e3f4'
    # Ballet studio: '34e4f6c5-44e3-4eae-b9c8-442dfecf01b4'
    locations = '["67423d08-2113-444f-8a5e-3e97f479078f", "f2ae664c-f420-4609-8933-89eb8010e3f4", "34e4f6c5-44e3-4eae-b9c8-442dfecf01b4"]'

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
