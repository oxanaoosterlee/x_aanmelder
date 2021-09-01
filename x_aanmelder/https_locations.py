import requests
import json


def https_locations(location):
    """ Returns the string of the ID of a given location name.
    Location is a string. E.g., "Body & Mind" or "Aerobics".
    ID is required for http_bookings.py.
    """

    url = "https://services.sc.tudelft.nl/api/v1/location"

    headers = {
        "accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language":"nl,en-US;q=0.9,en;q=0.8,ja;q=0.7,en-GB;q=0.6,fr;q=0.5,de;q=0.4",
        "Connection":"keep-alive",
        "Host":"services.sc.tudelft.nl",
        "Referer" :"https: // services.sc.tudelft.nl /?lang = nl",
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
    }

    p = requests.get(url, headers=headers)
    if p.status_code != 200:
        raise Exception("Failed to request schedule. Error: %s" % p.text)
    data = json.loads(p.content)


    """ Find requested location ID in request return data. """
    for location_item in data:
        if location.lower() == (location_item['name_en']).lower():
            return location_item['uuid']

    raise Exception("Cannot find ID for location %s, the location name might be wrong. " % location)



if __name__ == "__main__":
    data = https_locations("Body & Mind")
    print(data)
