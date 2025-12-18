from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
USERNAME = os.getenv("PYTHON_ANY_WHERE_USERNAME")
PASSWORD = os.getenv("PYTHON_ANY_WHERE_PASSWORD")


# ------------------- Setup Chrome -------------------
def setup_driver(headless=True):
    """Initialize the Chrome WebDriver with optional headless mode"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    if headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=chrome_options)
    return driver


# ------------------- Wait Helper -------------------
def wait_for_element(driver, by, locator, timeout=3):
    """Wait until an element is present and return it"""
    wait = WebDriverWait(driver, timeout, poll_frequency=0.5)
    return wait.until(EC.presence_of_element_located((by, locator)))


# ------------------- Login -------------------
def login(driver, username, password):
    driver.get("https://www.pythonanywhere.com/")

    # Go to login page
    login_link = wait_for_element(driver, By.LINK_TEXT, "Log in")
    login_link.click()

    # Fill credentials
    username_input = wait_for_element(driver, By.NAME, "auth-username")
    username_input.send_keys(username)
    password_input = driver.find_element(By.NAME, "auth-password")
    password_input.send_keys(password)

    # Click login button
    login_btn = driver.find_element(By.ID, "id_next")
    login_btn.click()


# ------------------- Navigate to Tasks -------------------
def go_to_tasks(driver):
    tasks_link = wait_for_element(driver, By.ID, "id_tasks_link")
    tasks_link.click()


# ------------------- Extend Expiry -------------------
def extend_expiry(driver):
    try:
        extend_btn = wait_for_element(driver, By.CSS_SELECTOR, "button.extend_scheduled_task", timeout=4)
        extend_btn.click()
        print("✅ Extend button clicked successfully")
    except TimeoutException:
        print("⚠️ No extend button found (maybe already extended)")


# ------------------- Logout -------------------
def logout(driver):
    try:
        logout_btn = driver.find_element(By.XPATH, "/html/body/div[1]/nav[1]/div/ul/li[6]/form/button")
        logout_btn.click()
    except NoSuchElementException:
        print("⚠️ Logout button not found")


# ------------------- Main Script -------------------
if __name__ == "__main__":
    driver = setup_driver(headless=False)
    try:
        login(driver, USERNAME, PASSWORD)
        go_to_tasks(driver)
        extend_expiry(driver)
    finally:
        logout(driver)
        driver.quit()




