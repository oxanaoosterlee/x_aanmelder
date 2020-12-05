# x_aanmelder

For people that are too lazy to manually enroll for a sports class.

### Credentials

Before using, put in your credentials in credentials.txt like this:

```
username: jsmith
password: 123abc
```

### Automatic job

Add execute permissions to script (while in the main project directory)

```
chmod u+x python_script.py
```

Then, in terminal run:

```
crontab -e
```

Add the following line at the end:

```
50 12 * * * export DISPLAY=:0 && /home/oxana/Documents/x_aanmelder/job.sh
```

This starts a terminal at 12:55 every day running the script. Remove `DISPLAY=:0 &&` to run in the background.

### Attendance

The file `attendance.csv` shows all available bookings for the next week. (Note: if the file is not there yet,
run `./Attendance.py`). Select which you would like to attend by putting an `x` in the last column. The script will then
make the booking for you. This file is also synced with Google Calendar (if it has been set-up, see next section).
Syncing happens automatically when x_aanmelder runs. If you want to update your Calendar directly after making
changes to `attendance.csv`, run `./Attendance.py`.

Note: when removing an `x`, it will also remove the class from your calendar. However, when removing a class that
has already been booked, the booking will not be made undone. This has to be done manually through the website.


### Google Calendar

To automatically enable the script to put reserved bookings in google calendar, take the following steps:

1. Enable the google calendar API (https://developers.google.com/calendar/quickstart/python).
3. After enabling using the website above, store the acquired file 'credentials.json' in the `/gcalendar` directory.
   Alternatively, acquire OAuth 2.0 credentials using the google cloud console, just make sure the .json file is
   called `credentials.json`.
4. Install the google client
   library `pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`
5. In the `/gcalendar` directory, run `python3 init_calendar.py` once to finish the authentication process.

### Notes

- If you want to add extra locations, you can add these in `https_bookings` (the `locations` list). You can find the
  location id by investigating the response to the 'bookings' request on the timetable page.

