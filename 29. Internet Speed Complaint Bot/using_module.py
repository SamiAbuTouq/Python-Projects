import speedtest  # Using speedtest-cli
import os
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

load_dotenv()

PROMISED_DOWN = 150
PROMISED_UP = 10
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")

UP = 0
DOWN = 0


def get_internet_speed():
    global UP, DOWN
    try:
        st = speedtest.Speedtest()

        print("Finding best server...")
        st.get_best_server()  # Optional: find the closest server for better accuracy

        print("Performing download test...")
        download_speed = st.download()
        download_mbps = download_speed / 1_000_000

        print("Performing upload test...")
        upload_speed = st.upload()
        upload_mbps = upload_speed / 1_000_000

        ping = st.results.ping

        UP = round(upload_mbps, 2)
        DOWN = round(download_mbps, 2)

        print(f"\nPing: {ping:.2f} ms")
        print(f"Download Speed: {download_mbps:.2f} Mbps")
        print(f"Upload Speed: {upload_mbps:.2f} Mbps")

    except Exception as e:
        print(f"An error occurred: {e}")


def tweet_at_provider():
    BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach', True)
    options.binary_location = BRAVE_PATH  # tell Selenium to use Brave instead of Chrome
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver=driver, timeout=20, poll_frequency=0.5)

    driver.get("https://twitter.com/i/flow/login")

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "text")))
    email_input.send_keys(TWITTER_EMAIL)
    email_input.send_keys(Keys.RETURN)  # same as Keys.ENTER
    sleep(2)  #

    try:
        username_input = driver.find_element(By.NAME, "text")
        username_input.send_keys(TWITTER_USERNAME)
        username_input.send_keys(Keys.RETURN)
        sleep(2)
    except:
        pass

    password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
    password_input.send_keys(TWITTER_PASSWORD)
    password_input.send_keys(Keys.RETURN)
    sleep(5)  # wait for login to finish

    # Tweet text box
    tweet_box = driver.find_element(By.XPATH, '//div[@data-testid="tweetTextarea_0"]')
    tweet_content = f"Hey Internet Provider, my download speed is {DOWN} Mbps and upload speed is {UP} Mbps. Why is this below the promised {PROMISED_DOWN} down / {PROMISED_UP} up?"
    tweet_box.send_keys(tweet_content)

    tweet_button = driver.find_element(By.XPATH,
                                       '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div/button')
    tweet_button.click()
    sleep(10)

    driver.close()

    print("Tweet posted successfully!🎉🎉")


get_internet_speed()
tweet_at_provider()
