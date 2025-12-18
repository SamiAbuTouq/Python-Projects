import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dotenv import load_dotenv

# ------------------- Configure logging -------------------
logging.basicConfig(
    filename='bot_log.txt',  # Log file will be in the same folder as the .exe
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Bot started")

# ------------------- Load environment variables -------------------
load_dotenv()
USERNAME = os.getenv("PYTHON_ANY_WHERE_USERNAME")
PASSWORD = os.getenv("PYTHON_ANY_WHERE_PASSWORD")

# ------------------- Setup Chrome -------------------
def setup_driver(headless=True):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    if headless:
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920,1080')
    return webdriver.Chrome(options=chrome_options)

# ------------------- Wait Helper -------------------
def wait_for_element(driver, by, locator, timeout=3):
    wait = WebDriverWait(driver, timeout, poll_frequency=0.5)
    return wait.until(EC.presence_of_element_located((by, locator)))

# ------------------- Login -------------------
def login(driver, username, password):
    driver.get("https://www.pythonanywhere.com/")
    login_link = wait_for_element(driver, By.LINK_TEXT, "Log in")
    login_link.click()
    username_input = wait_for_element(driver, By.NAME, "auth-username")
    username_input.send_keys(username)
    password_input = driver.find_element(By.NAME, "auth-password")
    password_input.send_keys(password)
    login_btn = driver.find_element(By.ID, "id_next")
    login_btn.click()
    logging.info("Logged in successfully")

# ------------------- Navigate to Tasks -------------------
def go_to_tasks(driver):
    tasks_link = wait_for_element(driver, By.ID, "id_tasks_link")
    tasks_link.click()
    logging.info("Navigated to tasks page")

# ------------------- Extend Expiry -------------------
def extend_expiry(driver):
    try:
        extend_btn = wait_for_element(driver, By.CSS_SELECTOR, "button.extend_scheduled_task", timeout=4)
        extend_btn.click()
        logging.info("Expiry extended successfully")
        return True
    except TimeoutException:
        logging.warning("No extend button found (maybe already extended)")
        return False

# ------------------- Logout -------------------
def logout(driver):
    try:
        logout_btn = driver.find_element(By.XPATH, "/html/body/div[1]/nav[1]/div/ul/li[6]/form/button")
        logout_btn.click()
        logging.info("Logged out successfully")
    except NoSuchElementException:
        logging.warning("Logout button not found")

# ------------------- Main Script -------------------
def main():
    try:
        driver = setup_driver(headless=True)
        login(driver, USERNAME, PASSWORD)
        go_to_tasks(driver)
        extend_expiry(driver)
        logout(driver)
        driver.quit()
    except WebDriverException as e:
        logging.error(f"WebDriver failed: {str(e)}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
    finally:
        # Add a blank line after each run for separation
        with open('bot_log.txt', 'a', encoding='utf-8') as f:
            f.write('\n')   


if __name__ == "__main__":
    main()
