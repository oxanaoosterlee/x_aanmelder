from selenium import webdriver
import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from plyer import notification
import time
from datetime import datetime
from datetime import time as t



def check_if_reservations_available(driver, lesson):
	try:
		lesson = WebDriverWait(driver,2).until(ec.presence_of_element_located((By.XPATH, "//*[text()[contains(.,'%s')]]" % lesson)))
		return True
	except:
		return False

credentials = open("credentials.txt")

username_input = credentials.readline().replace("username:","").strip()
password_input = credentials.readline().replace("password:","").strip()

available_lessons = ["Banaan"]
start_times = ["20:30"]
reserved = False

noon_rush = True


# Don't show the window
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-notifications')
#chrome_options.add_argument("--headless")

# Instantiate webdriver and waiting thingy
driver = webdriver.Chrome(options=chrome_options) #sudo apt install chromium-chromedriver
wait = WebDriverWait(driver,10)


while not reserved:
	# Go to website
	driver.get("https://x.tudelft.nl/nl/home?return_url=null")

	# Load at 12:59 am exactly
	if noon_rush: 
		while datetime.now().time() < t(19,46): continue

	# Click on the TU delft logo thingy (only necessary if it is required to log in again)
	log_in_button = driver.find_elements(By.LINK_TEXT, 'tudelft')


	# If required to log in
	if len (log_in_button) > 0:
		log_in_button[0].click()
		# Log in
		username = driver.find_element_by_id("username")
		username.send_keys(username_input)
		password = driver.find_element_by_id("password").send_keys(password_input)
		driver.find_element_by_id("submit_button").click()

		# Weird menu, need to navigate away
		back_btn = wait.until(ec.presence_of_element_located((By.CLASS_NAME, "btn__content")))
		back_btn.click()



	# Navigate to correct menu
	reserveren_btn = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "Reserveren")))
	reserveren_btn.click()

	location_btn = wait.until(ec.presence_of_element_located((By.XPATH, '//div[text()="Aerobics"]'))) # Click on 'Aerobics'

	# Load at 13:00 exactly
	if noon_rush: 
		while datetime.now().time() < t(22,6): continue

	location_btn.click()

	# Refresh the page every 2 seconds until the lesson appears on the page.
	if noon_rush:
		while True:
			is_available = check_if_reservations_available(driver, available_lessons[0])
			if is_available:
				break
			else:
				driver.refresh()

	else:
		# Find the specific class
		lesson = wait.until(ec.presence_of_element_located((By.XPATH, "//*[text()[contains(.,'%s')]]" % available_lessons[0])))

	# There can be more of the class. Pick the one with the right time.
	lessons = driver.find_elements(By.XPATH, "//*[text()[contains(.,'%s')]]" % available_lessons[0])

	for lesson in lessons:
		lesson_card = lesson.find_element_by_xpath(".//ancestor::div[contains(@class, 'card')]")


		# Get time 
		time_txt = lesson_card.find_element_by_xpath(".//b[text()[contains(.,'Time')]]").find_element_by_xpath(".//ancestor::p").text
		time_txt = time_txt.replace("Time:", "").strip().split("\n")[0].split(" - ")
		start_time, end_time = time_txt[0], time_txt[1]

		print("Found lesson %s at start time %s" % (available_lessons[0], start_time))
		if start_time != start_times[0]:
			print("Not the correct one. Skipping.")
			continue

		# Get occupancy
		occupancy_txt = lesson_card.find_element_by_xpath(".//span").text
		occupancy_txt = occupancy_txt.replace("Occupation","").replace(":","").strip().split('/')
		occupancy, capacity = int(occupancy_txt[0]), int(occupancy_txt[1])

		print("Occupancy: %d/%d" % (occupancy, capacity))
		# Subsribe if there is space.
		if occupancy < capacity:
			print("Space available!")
			notification.notify(
				title = "SPACE AVAILABLE",
				message = "SPACE AVAILABLE FOR %s at %s" % (available_lessons[0], start_time)
				)
			# Click on 'add' (subscribe for lesson)
			add_button = lesson_card.find_element_by_xpath(".//button")
			#add_button.click()
			reserved = True
		else:
			now = datetime.now()
			current_time = now.strftime("%H:%M:%S")
			print("(%s) No space available.." % current_time)

	# Wait a minute or three
	time.sleep(3 * 60)


