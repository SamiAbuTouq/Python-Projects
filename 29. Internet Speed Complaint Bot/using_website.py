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

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"


class InternetSpeedTwitterBot:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True)
        options.binary_location = BRAVE_PATH  # tell Selenium to use Brave instead of Chrome
        self.driver = webdriver.Chrome(options=options)

        self.up = 0
        self.down = 0
        self.wait = WebDriverWait(driver=self.driver, timeout=60, poll_frequency=0.5)

    def get_internet_speed(self):
        self.driver.get("https://www.speedtest.net/")
        go_btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "start-text")))
        print("Started speed test...")
        go_btn.click()

        download_speed = self.wait.until(lambda d: d.find_element(By.CLASS_NAME, "download-speed"))
        self.wait.until(lambda _: download_speed.text and download_speed.text != "—")

        # Wait until upload speed becomes a number (not "—")
        upload_speed = self.wait.until(lambda d: d.find_element(By.CLASS_NAME, "upload-speed"))
        self.wait.until(lambda _: upload_speed.text and upload_speed.text != "—")

        self.down = float(download_speed.text)
        self.up = float(upload_speed.text)

        print("Download:", download_speed.text)
        print("Upload:", upload_speed.text)

    def tweet_at_provider(self):
        self.driver.get("https://twitter.com/i/flow/login")

        email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "text")))
        email_input.send_keys(TWITTER_EMAIL)
        email_input.send_keys(Keys.RETURN)  # same as Keys.ENTER
        sleep(2)  #

        try:
            username_input = self.driver.find_element(By.NAME, "text")
            username_input.send_keys(TWITTER_USERNAME)
            username_input.send_keys(Keys.RETURN)
            sleep(2)
        except:
            pass

        password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(TWITTER_PASSWORD)
        password_input.send_keys(Keys.RETURN)
        sleep(5)  # wait for login to finish

        # Tweet text box
        tweet_box = self.driver.find_element(By.XPATH, '//div[@data-testid="tweetTextarea_0"]')
        tweet_content = f"Hey Internet Provider, my download speed is {self.down} Mbps and upload speed is {self.up} Mbps. Why is this below the promised {PROMISED_DOWN} down / {PROMISED_UP} up?"
        tweet_box.send_keys(tweet_content)

        tweet_button = self.driver.find_element(
            By.XPATH,
            '//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div/button')
        tweet_button.click()
        sleep(10)

        self.driver.close()

        print("Tweet posted successfully!🎉🎉")


bot = InternetSpeedTwitterBot()
bot.get_internet_speed()
bot.tweet_at_provider()
