from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import time

# ----------------  Step 1 - Setup, Chrome Profile and Basic Navigation ----------------
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

ACCOUNT_EMAIL = "sami@test.com"
ACCOUNT_PASSWORD = "sami10534114"
GYM_URL = "https://appbrewery.github.io/gym/"

driver = webdriver.Chrome(options=chrome_options)
driver.get(url=GYM_URL)
# I Can change the Condition polling interval using the poll_frequency parameter
wait = WebDriverWait(driver=driver, timeout=2, poll_frequency=0.5)


# driver.implicitly_wait(2)
# The Previous Line tells Selenium:
# Whenever I use find_element, don’t fail immediately if the element isn’t there.
# Instead, keep checking for up to 2 seconds before giving up.


def retry(func, retries=7, description=None):
    for i in range(retries):
        print(f"Trying {description}. Attempt: {i + 1}")
        try:
            return func()
        except TimeoutException:
            if i == retries - 1:
                raise  # The raise statement in this context will re-raise the same exception that was caught, without changing its type.
                # raise TimeoutException --> Creates a new TimeoutException object and raises it
                # Message: If you don’t pass the original exception message using just (raise),
                # the new exception may have no message (TimeoutException()),
                # so you lose information about what went wrong.
            time.sleep(1)


# ----------------  Step 2 - Automated Login ----------------
def login():
    login_button = wait.until(ec.element_to_be_clickable((By.ID, 'login-button')))
    login_button.click()

    email = wait.until(ec.presence_of_element_located((By.NAME, "email")))
    email.clear()
    email.send_keys(ACCOUNT_EMAIL)

    password = driver.find_element(By.NAME, 'password')
    password.clear()
    password.send_keys(ACCOUNT_PASSWORD)

    submit_button = driver.find_element(By.ID, 'submit-button')
    submit_button.click()

    # Checks if the element exists in the DOM (Document Object Model).
    # It does NOT care if the element is visible on the page.
    # The element could be hidden with display: none
    wait.until(ec.presence_of_element_located((By.ID, "schedule-page")))

    # Checks if the element is visible to the user.
    # Not hidden (display:none), not transparent, and within the viewport.
    schedule_page = driver.find_element(By.ID, "schedule-page")
    wait.until(lambda _: schedule_page.is_displayed())


retry(login, description="login")
# ----------------  Step 3 - Class Booking: Book Upcoming Tuesday Class  ----------------

# Find all class cards
class_cards = driver.find_elements(By.CSS_SELECTOR, "div[id^='class-card-']")

# Counters for booked classes for the booking summary
booked_count = 0
waitlist_count = 0
already_booked_count = 0
processed_classes = []

for card in class_cards:
    # Get the day title from the parent day group
    day_group = card.find_element(By.XPATH, "./ancestor::div[contains(@id, 'day-group-')]")
    day_title = day_group.find_element(By.TAG_NAME, "h2").text
    # Check if this is a Tuesday
    if "Tue" in day_title or "Thu" in day_title:  # Check if this is a 6pm class
        time_text = card.find_element(By.CSS_SELECTOR, "p[id^='class-time-']").text
        if "6:00 PM" in time_text:
            class_name = card.find_element(By.CSS_SELECTOR, "h3[id^='class-name-']").text  # Get the class name
            button = card.find_element(By.CSS_SELECTOR, "button[id^='book-button-']")  # Find and click the book button

            # Track the class details
            class_info = f"{class_name} on {day_title}"

            # ----------------  Step 4 - Class Booking: Checking if a class is already booked ----------------

            # Check if already booked
            # Increment the counter(s)
            if button.text == "Booked":
                print(f"✓ Already booked: {class_info}")
                already_booked_count += 1
                # Add detailed class info
                processed_classes.append(f"[Booked] {class_info}")
            elif button.text == "Waitlisted":
                print(f"✓ Already on waitlist: {class_info}")
                already_booked_count += 1
                # Add detailed class info
                processed_classes.append(f"[Waitlisted] {class_info}")
            elif button.text == "Book Class":
                button.click()
                print(f"✓ Successfully booked: {class_info}")
                booked_count += 1
                # Add detailed class info
                processed_classes.append(f"[New Booking] {class_info}")
                time.sleep(0.5)
            elif button.text == "Join Waitlist":
                button.click()
                print(f"✓ Joined waitlist for: {class_info}")
                waitlist_count += 1
                # Add detailed class info
                processed_classes.append(f"[New Waitlist] {class_info}")
                time.sleep(0.5)

print("\n--- BOOKING SUMMARY ---")
print(f"New bookings: {booked_count}")
print(f"New waitlist entries: {waitlist_count}")
print(f"Already booked/waitlisted: {already_booked_count}")
print(f"Total Tuesday & Thursday 6pm classes: {booked_count + waitlist_count + already_booked_count}")

print("\n--- DETAILED CLASS LIST ---")
for class_detail in processed_classes:
    print(f"  • {class_detail}")

# ----------------  Step 5: Verify Class Bookings on My Bookings Page ----------------

total_booked = already_booked_count + booked_count + waitlist_count
print(f"\n--- Total Tuesday/Thursday 6pm classes: {total_booked} ---")
print("\n--- VERIFYING ON MY BOOKINGS PAGE ---")

# Navigate to My Bookings page
my_bookings_link = driver.find_element(By.ID, "my-bookings-link")
my_bookings_link.click()

# Wait for My Bookings page to load
wait.until(ec.presence_of_element_located((By.ID, "my-bookings-page")))

# Count all Tuesday/Thursday 6pm bookings
verified_count = 0

# Find ALL booking cards (both confirmed and waitlist)
all_cards = driver.find_elements(By.CSS_SELECTOR, "div[id*='card-']")

for card in all_cards:
    try:
        when_paragraph = card.find_element(By.XPATH, ".//p[strong[text()='When:']]")
        when_text = when_paragraph.text
        # Check if it's a Tuesday or Thursday 6pm class
        if ("Tue" in when_text or "Thu" in when_text) and "6:00 PM" in when_text:
            class_name = card.find_element(By.TAG_NAME, "h3").text
            print(f"  ✓ Verified: {class_name}")
            verified_count += 1
    except NoSuchElementException:
        # Skip if no "When:" text found (not a booking card)
        pass

# Simple comparison
print(f"\n--- VERIFICATION RESULT ---")
print(f"Expected: {total_booked} bookings")
print(f"Found: {verified_count} bookings")

if total_booked == verified_count:
    print("✅ SUCCESS: All bookings verified!")
else:
    print(f"❌ MISMATCH: Missing {total_booked - verified_count} bookings")
