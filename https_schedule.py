import requests
import json


def request_schedule(location, token):
    """ Returns the classes currently available for booking.
    So after 13:00, returns all classes for that evening + the next morning.
    """

    url = "https://0072.api.dmssolutions.eu/bookings/schedule"

    data = '{"license":"z7Cp8owQQJEcGlm44EPQ","customer_id":"31090041","token":"' + token + '","trainer":"","onlinegroup":"' + location + '","cmsid":"","amount_of_days":365,"site":"0"}'

    headers = {
        'authority': '0072.api.dmssolutions.eu',
        'sec-ch-ua': '"Chromium";v="86", "\"Not\\A;Brand";v="99", "Google Chrome";v="86"',
        "accept": "application/json, text/plain, */*",
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://x.tudelft.nl',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://x.tudelft.nl/',
        'accept-language': 'en-US,en;q=0.9',
    }

    p = requests.post(url, headers=headers, data=data.encode())
    if p.status_code != 200:
        raise Exception("Failed to request schedule. Error: %s" % p.text)
    data = json.loads(p.content)

    # Schedule is returned using AMS timezone!!

    return data
