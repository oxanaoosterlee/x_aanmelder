import requests
import json

"""
Make a booking! 
"""
def https_participations(booking, local_storage):
    """ 
    Https-request to make the requested booking
    @param booking is a single item from the list that 'https_bookable_slots' returns
    @local_storage contains the user auth info from local storage in a dict
    """

    url = "https://backbone-web-api.production.delft.delcom.nl/participations"

    data = {
        "organizationId": None,
        "memberId": local_storage['member']['id'],
        "bookingId": booking['bookingId'], # 
        "primaryPurchaseMessage": None,
        "secondaryPurchaseMessage": None,
        "params": {
            "startDate": booking['startDate'],
            "endDate": booking['endDate'],
            "bookableProductId": booking['bookableProductId'], #
            "bookableLinkedProductId": booking['linkedProductId'], #
            "bookingId": booking['bookingId'], #
            "invitedMemberEmails": [],
            "invitedGuests": [],
            "invitedOthers": [],
            "primaryPurchaseMessage": None,
            "secondaryPurchaseMessage": None
        },
        "dateOfRegistration": None
    }

    data = json.dumps(data)

    headers = {
        'authority': 'backbone-web-api.production.delft.delcom.nl',
        'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="97", "Chromium";v="97"',
        "accept": "application/json, text/plain, */*",
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://x.tudelft.nl',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://x.tudelft.nl/',
        'accept-language': 'nl,en-US;q=0.9,en;q=0.8,ja;q=0.7,en-GB;q=0.6,fr;q=0.5,de;q=0.4s',
        'authorization': local_storage['tokenResponse']['tokenType'] + " " + local_storage['tokenResponse']['accessToken']
    }

    p = requests.post(url, headers=headers, data=data.encode())

    if "Created" in p.reason:
        return True
    elif p.status_code == 401:
        raise Exception("Booking not correct")
    else:
        print("Error: %s" % p.text)
        return False
