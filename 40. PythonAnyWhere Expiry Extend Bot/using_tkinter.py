from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox

# ------------------- Load environment variables -------------------
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
    login_link = wait_for_element(driver, By.LINK_TEXT, "Log in")
    login_link.click()
    username_input = wait_for_element(driver, By.NAME, "auth-username")
    username_input.send_keys(username)
    password_input = driver.find_element(By.NAME, "auth-password")
    password_input.send_keys(password)
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
        return True
    except TimeoutException:
        return False

# ------------------- Logout -------------------
def logout(driver):
    try:
        logout_btn = driver.find_element(By.XPATH, "/html/body/div[1]/nav[1]/div/ul/li[6]/form/button")
        logout_btn.click()
    except NoSuchElementException:
        pass

# ------------------- Tkinter Message -------------------
def show_message(title, message):
    root = tk.Tk()
    root.withdraw()  # Hide the main window completely
    root.attributes("-topmost", True)  # Make sure the messagebox appears on top
    messagebox.showinfo(title, message)
    root.destroy() # Start the Tk event loop

# ------------------- Main Script -------------------
def main():
    try:
        driver = setup_driver(headless=True)
        login(driver, USERNAME, PASSWORD)
        go_to_tasks(driver)
        success = extend_expiry(driver)
        logout(driver)
        driver.quit()

        if success:
            show_message("Success ✅", "Expiry extended successfully!")
        else:
            show_message("Notice ⚠️", "No extend button found or task already extended.")
    except WebDriverException as e:
        show_message("Error ❌", f"WebDriver failed: {str(e)}")
    except Exception as e:
        show_message("Error ❌", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
