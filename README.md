# x_aanmelder

For people that are too lazy to manually enroll for a sports class.

### Credentials

Before using, put in your credentials in `/data/account/credentials.txt` like this:

```
username: jsmith
password: 123abc
```

### Automatic job

Add execute permissions to script (while in the `x_aanmelder/x_aanmelder` directory)

```
chmod u+x x_aanmelder.py
```

Then, in terminal run:

```
crontab -e
```

Add the following line at the end:

```
55 12 * * * export DISPLAY=:0 && /home/oxana/Documents/x_aanmelder/scripts/job.sh
```

This starts a terminal at 12:55 every day running the script. Remove `DISPLAY=:0 &&` to run in the background.

### Attendance

The file `attendance.csv` in the `data` directory shows all available bookings for the next week. (Note: if the file is
not there yet, run `python3 Attendance.py`). Select which you would like to attend by putting an `x` in the last column. The
script will then make the booking for you. This file is also synced with Google Calendar (if it has been set-up, see
next section). Syncing happens automatically when x_aanmelder runs. If you want to update your Calendar directly after
making changes to `attendance.csv`, run `python3 Attendance.py`.

Note: when removing an `x`, it will also remove the class from your calendar. However, when removing a class that has
already been booked, the booking will not be made undone. This has to be done manually through the website.

### Google Authentication

To use Google Calendar or Google Sheets, it is required to setup OAuth 2.0.
1. Install the google client library `pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`
2. Follow the instructions here (https://support.google.com/cloud/answer/6158849?hl=en) to create Desktop Application Credentials.
3. Download the credentials and store as `credentials.json` in the `/data/oauth` directory.
4. In the `/x_aanmelder/google/OAuth` directory, run `python3 oauth.py` once to finish the authentication process.


### Notes
- If you want to add extra locations, you can add these in `https_bookings` (the `location_names` list).
