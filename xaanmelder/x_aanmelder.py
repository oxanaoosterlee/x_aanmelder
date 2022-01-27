import json
import os
import time
from datetime import datetime
from datetime import time as t

import pytz
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


from googleapi.gcalendar import add_schedule_booking_to_calendar
from googleapi.OAuth.oauth import get_calendar_service
from api_calls.https_participations import https_participations
from api_calls.https_bookable_slots import https_bookable_slots
from Attendance import Attendance

from localStorage import localStorage



class x_aanmelder():
    def __init__(self):
        self.driver = self.init_webdriver()
        self.reserved = False

        # Update info about desired attendance
        attendance = Attendance()
        attendance.update_file()
        attendance.update_calendar()

        self.requested_bookings = attendance.get_todays_requested_bookings()

    def init_webdriver(self):
        """ Initialize a webdriver. """
        # Don't show the window
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        return driver

    def enter_credentials(self):
        """
        Read the user's credentials from 'credentials.txt'.
        Use them to log in on the TU login page.
        """
        script_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        credentials_file = open(script_directory + "/data/account/credentials.txt")
        username = credentials_file.readline().replace("username:", "").strip()
        password = credentials_file.readline().replace("password:", "").strip()

        if len(username) == 0 or len(password) == 0:
            raise Exception("Invalid credentials supplied. Please add credentials to credentials.txt.")

        # Log in
        self.driver.find_element_by_id("username").send_keys(username)
        self.driver.find_element_by_id("password").send_keys(password)
        self.driver.find_element_by_id("submit_button").click()

        # Weird empty page appears after logging in, so refresh after it loads.
        WebDriverWait(self.driver, 20).until(
            ec.presence_of_element_located((By.XPATH, "//body[@class='ng-tns-0-0']")))
        self.driver.get("https://x.tudelft.nl/dashboard")

    def find_requested_booking_in_bookings(self, title, time):
        """ Check in the bookings (the schedule of all available lessons), if the requested booking is there. If not,
        throw an error.
        @param title is string with booking name
        @param time is dateTime with start time.
        """
        booking_schedule = https_bookable_slots()
        for booking in booking_schedule:
            if title.lower() in booking['booking']['description'].lower():
                if time == parser.isoparse(booking['startDate']):
                    print("Found requested booking %s at time %s" % (title, time))
                    return booking
        # If it cannot be found, something is wrong.
        print(booking_schedule)
        raise Exception("Cannot find requested class in booking 'bookings'!")

    def find_booking_in_schedule(self, title, time, schedule):
        """
        Check in the schedule (list of all available bookings) if the requested booking is there.
        Note: schedule needs to be preprocessed to only include the correct date and location.
        """
        for available_booking in schedule['bookings']:
            # Check if lesson name and starting time matches
            if title.lower() in available_booking['Description'].lower() and parser.parse(
                    available_booking['Start_date']).astimezone(
                pytz.timezone('Europe/Amsterdam')) == time:
                return available_booking

        raise Exception("Cannot find booking in 'schedule'.")

    def run_aanmelder(self):
        if len(self.requested_bookings) == 0:
            print("No bookings to make today.")
        
        self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")
        
        # Loop through all requested bookings.
        for requested_booking in self.requested_bookings:
            self.reserved = False

            # Check if requested booking is valid (can be found in the schedule calendar).
            # requested_booking_data contains info required for making the booking.
            requested_booking_data = self.find_requested_booking_in_bookings(title=requested_booking['Class'], time=requested_booking['Start'])

            # Some booking details
            start_time = requested_booking['Start']
            title = requested_booking['Class']
            print("Trying to reserve %s at time %s" % (title, start_time))

            while not self.reserved:

                # Go to website
                self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")
                time.sleep(0.5)

                # Wait until 12:59 before logging in (enrollment starts at 13:00) 
                if datetime.now().time() < t(12, 59): print("Waiting until 12:59 before logging in.")
                while datetime.now().time() < t(12, 59): time.sleep(2)

                # Click on TUDelft login button (only necessary if it is required to log in again)
                # When revisiting the page, it is possible to still be logged in.
                log_in_button = self.driver.find_elements_by_xpath("//*[contains(text(),'TUDelft')]")

                # The button can only be found when it is needed to log in again.
                if len(log_in_button) > 0:
                    log_in_button[0].click()

                    # Select TU Delft login (wait 0.5 sec for the xpath to be correct)
                    time.sleep(0.5)
                    log_in_button_2 = self.driver.find_elements_by_xpath("//*[@class='remaining'][contains(@data-keywords, 'delft')]")
                    log_in_button_2[0].click()

                    print("Logging in..")
                    self.enter_credentials()


                # Get dictionary of local storage that contains user info for making the booking
                local_storage = json.loads(localStorage(self.driver).items()['delcom_auth'])

                # Wait for 13:00
                if datetime.now().time() < t(13, 00): print("Waiting until 13:00 before attempting to make a booking.")
                while datetime.now().time() < t(13, 00): time.sleep(8)

                # Requesting the schedule can only be done from 13:00. Keep retrying until the desired schedule is returned.
                # If schedule is requested too early, the response will be an empty schedule.
                print("Trying to find requested lesson available for booking..")

                # Check if lesson is already booked.
                for participant in requested_booking_data['booking']['participations']:
                        if participant['memberId'] == local_storage['member']['id']:
                            print("Already booked!")
                            self.reserved = True
                            return

                # Make booking
                print("Requesting booking at time %s." % str(datetime.now().time()))
                success = https_participations(requested_booking_data, local_storage)
                if success:
                    print("Successfully made booking at time %s." % str(datetime.now().time()))
                    if get_calendar_service() is not None:
                        add_schedule_booking_to_calendar(requested_booking_data, booked=True)
                    self.reserved = True
                    continue
                else:
                    print("Failed to make booking.")



                # Retrying to make a booking. Need to refresh the page in case token expires and
                # we need to log in again
                time.sleep(1)


if __name__ == "__main__":
    aanmelder = x_aanmelder()
    aanmelder.run_aanmelder()
