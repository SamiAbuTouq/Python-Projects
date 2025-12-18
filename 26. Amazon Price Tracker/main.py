import os
import smtplib
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
EMAIL_PROVIDER_SMTP_ADDRESS = os.environ["EMAIL_PROVIDER_SMTP_ADDRESS"]
MY_EMAIL = os.environ["MY_EMAIL"]
MY_EMAIL_PASSWORD = os.environ["MY_EMAIL_PASSWORD"]




# Practice
# url = "https://appbrewery.github.io/instant_pot/"
# Live Site
url = "https://www.amazon.com/dp/B075CYMYK6?psc=1&ref_=cm_sw_r_cp_ud_ct_FM9M699VKHTT47YD50Q6"
header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
}

response = requests.get(url, headers=header)

soup = BeautifulSoup(response.content, "html.parser")
# print(soup.prettify())


# Find the HTML element that contains the price
price = soup.find(class_="a-offscreen").get_text()

# Remove the dollar sign using split
price_without_currency = price.split("$")[1]
# Convert to floating point number
price_as_float = float(price_without_currency)
print(price_as_float)

# ====================== Send an Email ===========================

# Get the product title
title = soup.find(id="productTitle").get_text().strip()
print(title)

# Set the price below which you would like to get a notification
BUY_PRICE = 95

if price_as_float < BUY_PRICE:
    message = f"{title} is on sale for {price}!"

    # ====================== Use environment variables ===========================

    with smtplib.SMTP(EMAIL_PROVIDER_SMTP_ADDRESS) as connection:
        connection.starttls()
        result = connection.login(MY_EMAIL, MY_EMAIL_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=MY_EMAIL,
            msg=f"Subject:Amazon Price Alert!\n\n{message}\n{url}".encode("utf-8")
        )

