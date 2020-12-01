from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from https_bookings import https_bookings
from https_schedule import request_schedule
from dateutil import parser
import pytz
from https_addBooking import https_addBooking
import time
from datetime import datetime
from datetime import time as t

class x_aanmelder():
	def __init__(self):
		self.driver = self.init_webdriver()
		self.reserved = False

		#Todo: Read from .csv
		self.lesson = "Yogalates" # HiiT, LBT
		self.start_date_time = parser.parse("01-12-2020 19:15").astimezone(pytz.timezone('Europe/Amsterdam'))

		self.locations = ["Body & Mind", "Ballet Studio", "Aerobics"]

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

	def enrolling_available(self):
		""" Check if classes are available for enrolling on the current page.
		(if not, the page shows "There are no bookings on this day").
		When classes do not show up yet, refresh every 2 seconds.
		"""
		try:
			WebDriverWait(self.driver, 5).until(ec.presence_of_element_located((By.XPATH, "//h3[@class='headline mb-0']")))
			return True
		except:
			return False

	def enter_credentials(self):
		"""
		Read the user's credentials from 'credentials.txt'.
		Use them to log in on the TU login page.
		"""
		credentials_file = open("credentials.txt")
		username = credentials_file.readline().replace("username:", "").strip()
		password = credentials_file.readline().replace("password:", "").strip()

		if len(username) == 0 or len(password) == 0:
			raise Exception("Invalid credentials supplied. Please add credentials to credentials.txt.")

		# Log in
		self.driver.find_element_by_id("username").send_keys(username)
		self.driver.find_element_by_id("password").send_keys(password)
		self.driver.find_element_by_id("submit_button").click()

		# Weird empty page appears after logging in, so refresh after it loads.
		WebDriverWait(self.driver, 20).until(ec.presence_of_element_located((By.XPATH, "//div[@class='dialog__content']")))
		self.driver.get("https://x.tudelft.nl/nl/members/dashboard")

	def find_requested_booking_in_bookings(self):
		""" Check in the bookings (the schedule of all available lessons), if the requested booking is there. If not,
		throw an error.
		"""
		found = False
		booking_schedule = https_bookings()
		#print(booking_schedule)
		for item in booking_schedule:
			if self.lesson in item['description']:
				if self.start_date_time == parser.isoparse(item['start']):
					print("Booking id in 'booking' is: %d" % item['booking_id'])
					break


	def run_aanmelder(self):
		print("Trying to reserve %s at time %s" % (self.lesson, self.start_date_time))
		self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")

		# Get bookings (schedule with all the times and classes)
		booking_schedule = https_bookings()
		#print(booking_schedule)
		for item in booking_schedule:
			if self.lesson in item['description']:
				if self.start_date_time == parser.isoparse(item['start']):
					print("Booking id in 'booking' is: %d" % item['booking_id'])
					break

		while not self.reserved:
			# Go to website
			self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")

			# Wait until 12:59 before logging in (enrollment starts at 13:00)
			if datetime.now().time() < t(12,59): print("Waiting until 12:59 before logging in.")
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
			print("Getting token")
			WebDriverWait(self.driver, 20).until(ec.presence_of_element_located((By.XPATH, "//a[text()[contains(.,'Reserveren')]]")))
			reserveren_btn = self.driver.find_element(By.XPATH, "//a[text()[contains(.,'Reserveren')]]")
			reserveren_href = reserveren_btn.get_attribute('href')
			token_start, token_end = reserveren_href.find("token") + 6, reserveren_href.find("&redirect")
			token = reserveren_href[token_start:token_end]
			print("Got token")

			# Wait for 13:00
			if datetime.now().time() < t(13,00): print("Waiting until 13:00 before attempting to make a booking.")
			while datetime.now().time() < t(13, 00): time.sleep(2)

			# Get schedule for each location (available bookings for a certain location)
			# and find the requested lesson.
			print("Trying to find requested lesson available for booking..")
			lesson = None
			i = 0
			while lesson is None:
				for location in self.locations:
					sched = request_schedule(location, token)
					if len(sched['schedule']) == 0: continue # No available bookings for this location.
					available_lessons = sched['schedule'][0]['bookings']
					for available_lesson in available_lessons:
						print("Found lesson %s with booking_id %s at time %s" % (available_lesson['Description'], available_lesson['Booking_id'], available_lesson['Start_date']))
						# Check if correct lesson
						if self.lesson in available_lesson['Description']:
							# Check time
							starting_time = parser.parse(available_lesson['Start_date']).astimezone(pytz.timezone('Europe/Amsterdam'))
							if starting_time == self.start_date_time:
								print("Found correct lesson")
								lesson = available_lesson
								break
				i += 1
				print("\rRetrying. i = %d" % i, end='')
				time.sleep(0.5)
			print("Found it!")

			# Check if lesson is already booked.
			if lesson['Booked']:
				print("Already booked!")
				self.reserved = True
				return

			# Get booking id of the lesson and make a booking.
			booking_id = lesson['Booking_id']
			print("The retrieved booking id is %s" % booking_id)

			# Make booking
			if int(lesson['Bezetting']) < int(lesson['Max_participants']):
				success = https_addBooking(booking_id, token)
				if success:
					print("Successfully made booking.")
					self.reserved = True
					return
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


