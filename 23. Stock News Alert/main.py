import requests
import os
from dotenv import load_dotenv

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

load_dotenv()
STOCK_ENDPOINT =os.getenv("STOCK_ENDPOINT")
NEWS_ENDPOINT = os.getenv("NEWS_ENDPOINT")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
Twilio_SID = os.getenv("Twilio_SID")
Twilio_AUTH_TOKEN = os.getenv("Twilio_AUTH_TOKEN")

## STEP 1: Use https://www.alphavantage.co
# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday then print("Get News").
stock_api_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": STOCK_API_KEY,
}

r = requests.get(STOCK_ENDPOINT, params=stock_api_parameters)
r.raise_for_status()
stock_data = r.json()
data_list = list(stock_data["Time Series (Daily)"].keys())
print(data_list)

yesterday = data_list[0]
day_before_yesterday = data_list[1]

yesterday_close = float(stock_data["Time Series (Daily)"][yesterday]["4. close"])
day_before_yesterday_close = float(stock_data["Time Series (Daily)"][day_before_yesterday]["4. close"])
difference = abs(yesterday_close - day_before_yesterday_close)
percentage_change = (difference / day_before_yesterday_close) * 100
if percentage_change >= 5:  # You can change this value of percentage change If you want to test the code.
    news_api_parameters = {
        "qInTitle": "tesla",
        "from": "2025-07-23",
        # "sortBy":"publishedAt",
        "apiKey": NEWS_API_KEY,
    }

    r = requests.get(NEWS_ENDPOINT, params=news_api_parameters)
    r.raise_for_status()
    data = r.json()

    three_articles = data["articles"][:3]

    # print(three_articles)

    ## STEP 3: Use https://www.twilio.com
    # Send a seperate message with the percentage change and each article's title and description to your phone number.
    from twilio.rest import Client

    percentage_change = 5
    client = Client(Twilio_SID, Twilio_AUTH_TOKEN)
    for article in three_articles:
        headline = article['title']
        brief = article['description']
        # Format the message
        message_body = f"{STOCK}: {'🔺' if percentage_change > 0 else '🔻'}{percentage_change:.2f}%\nHeadline: {headline}\nBrief: {brief}"

        # Send the message
        message = client.messages.create(
            from_='whatsapp:+14155238886',
            body=message_body,
            to='whatsapp:+962796115278'
        )
        print(message.sid)

