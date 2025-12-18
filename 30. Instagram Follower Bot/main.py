from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
import time
from dotenv import load_dotenv
import os


load_dotenv()


SIMILAR_ACCOUNT = "chefsteps"
USERNAME = os.getenv("INSTA_USERNAME_1")
USERNAME = os.getenv("INSTA_USERNAME_2")
PASSWORD = os.getenv("INSTA_PASSWORD")

class InstaFollower:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 3)

    def login(self):
        url = "https://www.instagram.com/accounts/login/"
        self.driver.get(url)

        # Wait for page to load and handle cookie consent if present
        try:
            cookie_decline = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Decline') or contains(text(), 'Not Now')]")))
            cookie_decline.click()
        except TimeoutException:
            pass  # No cookie consent dialog found

        # Wait for login form to load
        username_field = self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
        password_field = self.driver.find_element(By.NAME, "password")

        username_field.send_keys(USERNAME)
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.ENTER)

        # Handle "Save Login Info" prompt
        try:
            not_now_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Not now')]")))
            not_now_btn.click()
        except TimeoutException:
            pass

        # Handle notifications prompt
        try:
            not_now_notifications = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Not Now')]")))
            not_now_notifications.click()
        except TimeoutException:
            pass

        time.sleep(3)

    def find_followers(self):
        self.driver.get(f"https://www.instagram.com/{SIMILAR_ACCOUNT}/")
        time.sleep(1)

        # Click on followers
        try:
            followers_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]")))
            followers_link.click()
        except TimeoutException:
            print("Could not find followers link")
            return

        time.sleep(1)

        # Wait for the followers modal to appear
        try:
            # modal = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div")))
            modal = self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div//div[1]")))

        except TimeoutException:
            print("Could not find followers modal")
            return

        last_height = 0
        scroll_attempts = 0
        max_scroll_attempts = 10

        while scroll_attempts < max_scroll_attempts:
            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)
            self.driver.execute_script("arguments[0].scrollBy(0, 200)", modal)

            time.sleep(2)

            new_height = self.driver.execute_script("return arguments[0].scrollTop", modal)

            if new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1

    def follow(self):
        # Find all follow buttons in the modal
        all_buttons = self.driver.find_elements(By.XPATH,"//div[@role='dialog']//button//div[contains(text(), 'Follow')]/..")

        for button in all_buttons:
            try:
                if button.text == "Follow":
                    button.click()
                    time.sleep(1.5)  # Wait between follows to avoid being flagged
            except ElementClickInterceptedException:
                try:
                    cancel_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Cancel')]")
                    cancel_button.click()
                except NoSuchElementException:
                    pass
                continue
        self.driver.close()


# Run the bot
bot = InstaFollower()
bot.login()
bot.find_followers()
bot.follow()