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
