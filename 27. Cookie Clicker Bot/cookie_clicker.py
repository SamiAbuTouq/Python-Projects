from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep, time

# Setup Chrome driver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

driver = webdriver.Chrome(options=chrome_options)

driver.get("https://ozh.github.io/cookieclicker/")

# Wait for page to load just in case
sleep(3)

# Handle initial popups
# print("Looking for language selection...")
# try:
#     language_button = driver.find_element(by=By.ID, value="langSelect-EN")
#     print("Found language button, clicking...")
#     language_button.click()
#     sleep(3)  # more loading
# except NoSuchElementException:
#     print("Language selection not found")
#
# # Wait for everything to settle
# sleep(2)
# Find the big cookie to click

cookie = driver.find_element(by=By.ID, value="bigCookie")


# Set timers
wait_time = 5
timeout = time() + wait_time  # Check for purchases every 5 seconds
five_min = time() + 60 * 5  # Run for 5 minutes

while True:
    cookie.click()

    # Every 5 seconds, try to buy the most expensive item we can afford
    if time() > timeout:
        try:
            # Get current cookie count
            cookies_element = driver.find_element(By.ID, "cookies")
            cookie_text = cookies_element.text
            cookie_count = int(cookie_text.split()[0].replace(",", ""))

            # Re-find all products every time to avoid stale element
            products = driver.find_elements(By.CSS_SELECTOR, "div[id^='product']")

            # Buy the most expensive item we can afford
            for product in reversed(products):
                if "enabled" in product.get_attribute("class"):
                    item_id = product.get_attribute('id')  # store id before click
                    product.click()
                    print(f"Bought item: {item_id}")
                    break

        except (NoSuchElementException, ValueError):
            print("Couldn't find cookie count or items")

        # Reset timer
        timeout = time() + wait_time

    # Stop after 5 minutes
    if time() > five_min:
        try:
            cookies_element = driver.find_element(by=By.ID, value="cookies")
            print(f"Final result: {cookies_element.text}")
        except NoSuchElementException:
            print("Couldn't get final cookie count")
        break
