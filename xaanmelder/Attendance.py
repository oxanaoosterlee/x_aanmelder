from googleapi.gcalendar import *
from googleapi.gsheets import *
from api_calls.https_bookable_slots import https_bookable_slots
import pytz
import os
own_tz = pytz.timezone('Europe/Amsterdam')


class Attendance:
    """
    - Keeps a file 'attendance.csv' with all classes for the next 7 days.
    - User can put an 'x' in the column 'attend' for classes they want to attend.
    - The user's Google Calendar will by synced with the attendance file.
    """

    def __init__(self):
        self.attendance_file = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/data/attendance.csv"
        self.attendance_df = self.read_from_csv(self.attendance_file)

        # Enable using Google Sheets for marking attendance. If False, an offline csv file is used located in the
        # /data directory.
        self.use_gsheets = True

        # Check if google sheets is correctly setup
        if self.use_gsheets and not gsheets_available():
            self.use_gsheets = False

    def update_file(self):
        """
        Update attendance file to only include bookings on the schedule from the current time until
        the next seven days.
        """
        new_attendance = pd.DataFrame(columns=['Day', 'Date', 'Start', 'End', 'Class', 'Trainer', 'Location', 'Attend'])

        # Get all available 'bookings' (classes) for the next week. NOTE: returned in UTC time.
        # Store the bookings in a dataframe.
        next_week_bookings = https_bookable_slots(days=7)
        for booking in next_week_bookings:
            # Keep start and end 'datetime' for easier handling.
            # 'Day' and 'Date' are made human-readible immediately.
            # 'Start' and 'End' will be changed to human-readible times when storing as .csv.
            start = parser.isoparse(booking['startDate']).astimezone(own_tz)
            end = parser.isoparse(booking['endDate']).astimezone(own_tz)

            # Skip classes without description, these are things such as 'masseur' and 'physiotherapist'
            if booking['booking']['description'] is None:
                continue

            supervisors = booking['booking']['supervisors']
            new_attendance = new_attendance.append(
                {'Day': start.strftime("%a"),
                 'Date': start.strftime("%d-%m"),
                 'Start': start,
                 'End': end,
                 'Class': booking['booking']['description'],
                 'Trainer': supervisors[0]['firstName'] + " " + supervisors[0]['lastName'] if len(supervisors) > 0 else "",
                 'Location': booking['booking']['product']['description'],
                 'Attend': '',
                 },
                ignore_index=True
            )

        # Sort by start date/time
        new_attendance = new_attendance.sort_values(by=['Start'], ignore_index=True)

        # Set 'start' column dtype correctly to avoid issues with merging
        new_attendance['Start'] = pd.to_datetime(new_attendance['Start'])

        # Merge attendance information from old file into the new dataframe
        # Only merge old attendance information when it actually exists.
        old_attendance = get_sheet_data() if self.use_gsheets else self.read_from_csv(self.attendance_file)

        if not old_attendance.empty:
            new_attendance = pd.merge(new_attendance, old_attendance[['Start', 'Class', 'Attend']],
                                      how='left', on=['Start', 'Class'])
            new_attendance['Attend'] = new_attendance['Attend_y'].fillna(new_attendance['Attend_x'])
            new_attendance = new_attendance.drop(['Attend_x', 'Attend_y'], axis=1)

        # Store the newly merged dataframe
        self.attendance_df = new_attendance
        write_sheet_data(new_attendance) if self.use_gsheets else self.write_to_csv(new_attendance)
        print("Updated 'attendance file'")

    def get_todays_requested_bookings(self):
        """
        Return booking(s) that the user wants to attend and that are bookable today.
        These are bookings for the evening of the same day, as well as bookings for the next morning (<13:00)
        Return as a dictionary.
        """

        # Relevant bookings adhere three conditions:
        # 1. Start time between NOW and next day 13:00.
        # 2. 'Attend' is marked with an 'x'.

        # Find bookings marked 'attend'.
        subset = self.attendance_df.loc[self.attendance_df['Attend'].str.strip() == 'x']

        # Get requested bookings with a start time between now and tomorrow 13:00
        from_dt = datetime.now(own_tz)
        until_dt = datetime.now(own_tz).replace(hour=23, minute=0, second=0, microsecond=0)
        until_dt += timedelta(days=1)
        subset = subset.loc[(subset['Start'] >= from_dt) & (subset['Start'] < until_dt)]

        # Convert to dictionary for iterating easier.
        todays_requested_bookings = subset.to_dict("records")

        return todays_requested_bookings

    def update_calendar(self):
        """ Update googleapi calendar with all desired bookings.
        Also remove bookings that are in calendar but are not marked with 'x' anymore.
        """
        if get_calendar_service() is None:
            print("Calendar is not available")
            return

        # Add items marked with 'x' in attendance_df to the googleapi calendar.
        attending_events = self.attendance_df.loc[self.attendance_df['Attend'].str.strip() == 'x']
        for i, event in attending_events.iterrows():
            add_calendar_event(
                title=event['Class'],
                start=event['Start'],
                end=event['End'],
                location=event['Location'],
                trainer=event['Trainer'],
                booked=False
            )

        # Check googleapi calendar events made by this script.
        # 1. Remove calendar events that are not in 'attending_events'.
        # 2. Update the location of the event in case it is incorrect
        calendar_events = get_all_x_aanmelder_events()
        for event in calendar_events:
            event_title = event['summary']
            event_start = parser.parse(event['start']['dateTime'])

            # Check if calendar event is in attending_events
            matches = attending_events.loc[(attending_events["Start"] == event_start) & (
                        attending_events['Class'] == event_title.replace(" (booked)", ""))]

            # If it is not, delete from the calendar.
            # Only delete events that have not been booked yet.
            if matches.empty:
                if 'booked' not in event_title: remove_event(event['id'])
                continue

            # Check if the location of the calendar event is still correct.
            # If not, update it.
            if matches['Location'].iloc[0] != event['location']:
                update_event_location(event, matches['Location'].iloc[0])

        print("Updated calendar.")

    def read_from_csv(self, csv_file):
        """ Read the (old) attendance dataframe from a csv. """
        # If file does not exist yet, return an empty dataframe.
        if not os.path.exists(csv_file):
            return pd.DataFrame()
        df = pd.read_csv(csv_file)
        # Change 'Start' and 'End' columns to DateTime formats for easier handling.
        df['Start'] = df.apply(lambda x: parser.parse(x.Date + " " + x.Start, dayfirst=True).astimezone(own_tz), axis=1)
        df['End'] = df.apply(lambda x: parser.parse(x.Date + " " + x.End, dayfirst=True).astimezone(own_tz), axis=1)
        return df

    def write_to_csv(self, df):
        """ Store the new attendance dataframe to a csv."""
        # Need to make copy otherwise the column operations are applied to the original dataframe.
        copy = df.copy()
        # Change 'Start' and 'End' columns to something more readable.
        copy['Start'] = df.apply(lambda x: x.Start.strftime("%H:%M"), axis=1)
        copy['End'] = df.apply(lambda x: x.End.strftime("%H:%M"), axis=1)
        copy.to_csv(self.attendance_file, index=False)


if __name__ == "__main__":
    att = Attendance()
    att.update_file()
    att.update_calendar()
