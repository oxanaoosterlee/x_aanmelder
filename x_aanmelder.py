#!/usr/bin/python3
import os
import time
from datetime import time as t

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from Attendance import Attendance
from gcalendar.gcalendar import *
from https_addBooking import https_addBooking
from https_bookings import https_bookings
from https_schedule import https_schedule


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
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def enter_credentials(self):
        """
        Read the user's credentials from 'credentials.txt'.
        Use them to log in on the TU login page.
        """
        script_directory = os.path.dirname(os.path.realpath(__file__))
        credentials_file = open(script_directory + "/credentials.txt")
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
            ec.presence_of_element_located((By.XPATH, "//div[@class='dialog__content']")))
        self.driver.get("https://x.tudelft.nl/nl/members/dashboard")

    def find_requested_booking_in_bookings(self, title, time):
        """ Check in the bookings (the schedule of all available lessons), if the requested booking is there. If not,
        throw an error.
        @param title is string with booking name
        @param time is dateTime with start time.
        """
        booking_schedule = https_bookings()
        for booking in booking_schedule:
            if title.lower() in booking['description'].lower():
                if time == parser.isoparse(booking['start']):
                    print("Booking id in 'booking' is: %d" % booking['booking_id'])
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
        self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")

        # Loop through all requested bookings.
        for requested_booking in self.requested_bookings:
            self.reserved = False

            # Check if requested booking is valid (can be found in the schedule calendar).
            self.find_requested_booking_in_bookings(title=requested_booking['Class'], time=requested_booking['Start'])

            # Some booking details
            location_name = requested_booking['Location']
            start_time = requested_booking['Start']
            title = requested_booking['Class']
            print("Trying to reserve %s at time %s" % (title, start_time))

            while not self.reserved:
                # Go to website
                self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")

                # Wait until 12:59 before logging in (enrollment starts at 13:00)
                if datetime.now().time() < t(12, 59): print("Waiting until 12:59 before logging in.")
                while datetime.now().time() < t(12, 59): time.sleep(2)

                # Click on the TU logo thingy (only necessary if it is required to log in again)
                # When revisiting the page, it is possible to still be logged in.
                log_in_button = self.driver.find_elements(By.LINK_TEXT, 'tudelft')

                # The button can only be found when it is needed to log in again.
                if len(log_in_button) > 0:
                    log_in_button[0].click()
                    print("Logging in..")
                    self.enter_credentials()

                # Get session token (can be find in the url that leads to the reservation. token is regenerated after each login).
                print("Getting token...")
                WebDriverWait(self.driver, 20).until(
                    ec.presence_of_element_located((By.XPATH, "//a[text()[contains(.,'Reserveren')]]")))
                reserveren_btn = self.driver.find_element(By.XPATH, "//a[text()[contains(.,'Reserveren')]]")
                reserveren_href = reserveren_btn.get_attribute('href')
                token_start, token_end = reserveren_href.find("token") + 6, reserveren_href.find("&redirect")
                token = reserveren_href[token_start:token_end]
                print("Got token")

                # Wait for 13:00
                if datetime.now().time() < t(13, 00): print("Waiting until 13:00 before attempting to make a booking.")
                while datetime.now().time() < t(13, 00): time.sleep(2)

                # Requesting the schedule can only be done from 13:00. Keep retrying until the desired schedule is returned.
                # If schedule is requested too early, the response will be an empty schedule.
                print("Trying to find requested lesson available for booking..")
                i = 0
                while (True):
                    # Returns the schedule (available bookings) for a specific location.
                    # (Usually for today's evening and tomorrow's morning)
                    schedule_i = https_schedule(location_name, token)

                    # Only keep the schedule for the requested date
                    schedule = [x for x in schedule_i if
                                parser.parse(x['day'], dayfirst=True).date() == start_time.date()]

                    if len(schedule) != 1:
                        # Desired schedule is not available yet (len(schedule) == 1 if correct day can found).
                        # Retry.
                        time.sleep(0.5)
                        i += 1
                        print("\rRetrying.. i = %d" % (i), end="")
                    else:
                        print("\n")
                        break

                scheduled_booking = self.find_booking_in_schedule(title=title, time=start_time, schedule=schedule[0])
                print("Found the requested lesson!")

                # Check if lesson is already booked.
                if scheduled_booking['Booked']:
                    print("Already booked!")
                    self.reserved = True
                    return

                # Get booking id of the lesson and make a booking.
                booking_id = scheduled_booking['Booking_id']
                print("The retrieved booking id is %s" % booking_id)
                # Make booking
                if int(scheduled_booking['Bezetting']) < int(scheduled_booking['Max_participants']):
                    print("Requesting booking at time %s." % str(datetime.now().time()))
                    success = https_addBooking(booking_id, token)
                    if success:
                        print("Successfully made booking at time %s." % str(datetime.now().time()))
                        if is_calendar_available():
                            add_schedule_booking_to_calendar(scheduled_booking, booked=True)
                        self.reserved = True
                        continue
                    else:
                        print("Failed to make booking.")
                else:
                    print("Lesson full")


                # Retrying to make a booking. Need to refresh the page in case token expires and
                # we need to log in again
                time.sleep(1)


if __name__ == "__main__":
    aanmelder = x_aanmelder()
    aanmelder.run_aanmelder()
