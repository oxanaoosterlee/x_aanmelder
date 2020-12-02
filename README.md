# x_aanmelder


# Credentials
Before using, put in your credentials in credentials.txt like this:
```
username: jsmith
password: 123abc
```

# Automatic job

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

This starts a terminal at 12:50 every day running the script.

# Google Calendar
To automatically enable the script to put reserved bookings in google calendar, take the following steps:
1. Enable the google calendar API (https://developers.google.com/calendar/quickstart/python).
3. After enabling using the website above, store the acquired file 'credentials.json' in the `/gcalendar` directory.
    Alternatively, acquire OAuth 2.0 credentials using the google cloud console, just make sure the .json file is called `credentials.json`.
4. Install the google client library `pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib`
5. In the `/gcalendar` directory, run `python3 init_calendar.py` once to finish the authentication process.