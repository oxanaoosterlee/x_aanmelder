from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from plyer import notification
import time
from datetime import datetime
from datetime import time as t


class x_aanmelder():
	def __init__(self):
		self.driver = self.init_webdriver()
		self.reserved = False

		#Todo: Read from .csv
		self.available_lessons = ["Body"]
		self.start_times = ["09:15"]


	def init_webdriver(self):
		""" Initialize a webdriver. """
		# Don't show the window
		chrome_options = webdriver.ChromeOptions()
		chrome_options.add_argument('--disable-notifications')
		#chrome_options.add_argument("--headless")
		driver = webdriver.Chrome(options=chrome_options)
		return driver

	def enrolling_available(self):
		""" Check if classes are available for enrolling on the current page.
		(if not, the page shows "There are no bookings on this day").
		When classes do not show up yet, refresh every 2 seconds.
		"""
		try:
			WebDriverWait(self.driver, 2).until(ec.presence_of_element_located((By.XPATH, "//h3[@class='headline mb-0']")))
			print("TRUE")
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

		# Weird empty page appears after logging in, so refresh.
		self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")


	def get_correct_lesson_card(self, lesson_name, lesson_start_time):
		""" Return the lesson card for the requested lesson on the 'enrol' page.
			Lesson cards are the 'blocks' where each lesson is represented in with their info.
		"""

		# Get the correct lesson. There can be more of the same class at different times
		# Pick the one with the right time.
		# todo: make case insensitive
		lessons = self.driver.find_elements(By.XPATH, "//h3[@class='headline mb-0' and contains(text(), '%s')]" %
											self.available_lessons[0])
		for lesson in lessons:
			lesson_card = lesson.find_element_by_xpath(".//ancestor::div[contains(@class, 'card')]")

			# Get time
			time_txt = lesson_card.find_element_by_xpath(".//b[text()[contains(.,'Time')]]").find_element_by_xpath(
				".//ancestor::p").text
			time_txt = time_txt.replace("Time:", "").strip().split("\n")[0].split(" - ")
			start_time, end_time = time_txt[0], time_txt[1]

			print("Found lesson %s at start time %s" % (lesson_name, lesson_start_time))
			if start_time != lesson_start_time:
				print("Not the correct one. Skipping.")
				continue
			else:
				return lesson_card

		raise Exception("Could not find lesson %s at time %s" % (lesson_name, lesson_start_time))

	def run_aanmelder(self):
		while not self.reserved:
			# Go to website
			self.driver.get("https://x.tudelft.nl/nl/home?return_url=null")

			# Wait until 12:59 before logging in (enrollment starts at 13:00)
			while datetime.now().time() < t(12, 59): time.sleep(2)

			# Click on the TU logo thingy (only necessary if it is required to log in again)
			# When revisiting the page, it is possible to still be logged in.
			log_in_button = self.driver.find_elements(By.LINK_TEXT, 'tudelft')

			# The button can only be found when it is needed to log in again.
			if len(log_in_button) > 0:
				log_in_button[0].click()
				self.enter_credentials()

			# Navigate to correct menu
			reserveren_btn = WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.LINK_TEXT, "Reserveren")))
			reserveren_btn.click()

			# Click on the class location at 13:00, when enrollment starts.
			location = "Aerobics" #todo: check if full name is needed or part is also fine
			location_btn = WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, '//div[text()="%s"]' % location)))
			while datetime.now().time() < t(13,00): time.sleep(1)
			location_btn.click()

			# Check if enrollment is available, if not, refresh the page and keep checking until it becomes available.
			while True:
				if self.enrolling_available():
					break
				else:
					self.driver.refresh()


			lesson_card = self.get_correct_lesson_card(self.available_lessons[0], self.start_times[0])

			# Get occupancy of the lesson
			occupancy_txt = lesson_card.find_element_by_xpath(".//span").text
			occupancy_txt = occupancy_txt.replace("Occupation", "").replace(":", "").strip().split('/')
			occupancy, capacity = int(occupancy_txt[0]), int(occupancy_txt[1])
			print("Occupancy: %d/%d" % (occupancy, capacity))

			# Check if already enrolled
			button = lesson_card.find_element_by_xpath(".//button")
			if button.text == "CANCEL":
				print("Already enrolled!")
				self.reserved=True
				return

			# Enroll if there is space.
			if occupancy < capacity:
				print("Space available!")

				# Send out a notification
				notification.notify(
					title="SPACE AVAILABLE",
					message="SPACE AVAILABLE FOR %s at %s" % (self.available_lessons[0], self.start_times[0])
				)

				# Click on 'add' (subscribe for lesson)
				add_button = lesson_card.find_element_by_xpath(".//button")
				add_button.click()
				time.sleep(10)

				# Need to get lesson card again (the page takes some time to reload after clicking the enroll button),
				lesson_card = self.get_correct_lesson_card(self.available_lessons[0], self.start_times[0])
				WebDriverWait(self.driver, 10).until(ec.presence_of_element_located((By.XPATH, ".//button")))
				button = lesson_card.find_element_by_xpath(".//button")
				if button.text == "CANCEL":
					print("Reservation succesfull.")
					self.reserved = True
				else:
					print("Reservation failed")

			else:
				now = datetime.now()
				current_time = now.strftime("%H:%M:%S")
				print("(%s) No space available.." % current_time)

				# If still just after 13:00, retry immediately. Else, retry every 3 minutes or so.
				if datetime.now().time() < t(13, 5): continue
				else: time.sleep(3 * 60)




if __name__ == "__main__":
	aanmelder = x_aanmelder()
	aanmelder.run_aanmelder()


