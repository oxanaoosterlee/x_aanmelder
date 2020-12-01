import requests


def https_addBooking(booking_id, token):
    url = "https://0072.api.dmssolutions.eu/bookings/addBooking"
    data = '{"license":"z7Cp8owQQJEcGlm44EPQ","customer_id":"31090041","token":"' + token + '","booking_id":"' + booking_id + '"}'

    headers = {
        'authority': '0072.api.dmssolutions.eu',
        "accept": "application/json, text/plain, */*",
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://x.tudelft.nl',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'referer': 'https://x.tudelft.nl/new/',
        'accept-language': 'en-US,en;q=0.9',
    }

    p = requests.post(url, headers=headers, data=data.encode())

    if "booking added" in p.text:
        return True
    elif p.status_code == 401:
        raise Exception("Booking not correct")
    else:
        print("Error: %s" % p.text)
        return False

#### In case of success
# '{\n    "response": 0,\n    "message": "booking added"\n}'
