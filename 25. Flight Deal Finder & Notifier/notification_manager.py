import os
import requests
from twilio.rest import Client
import smtplib
from dotenv import load_dotenv
load_dotenv()

class NotificationManager:

    def __init__(self):
        self.client = Client(os.environ['TWILIO_SID'], os.environ["TWILIO_AUTH_TOKEN"])
        self.smtp_address = os.environ["EMAIL_PROVIDER_SMTP_ADDRESS"]
        self.email = os.environ["MY_EMAIL"]
        self.email_password = os.environ["MY_EMAIL_PASSWORD"]
        self.twilio_from_number = os.environ["TWILIO_WHATSAPP_FROM_NUMBER"]
        self.twilio_to_number = os.environ["TWILIO_WHATSAPP_TO_NUMBER"]

    def send_telegram(self, message_body):
        BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
        CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message_body,
            "parse_mode": "Markdown"  # or "HTML"
        }
        response = requests.post(url, data=payload)

        if response.status_code == 200:
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message:", response.text)

    def send_whatsapp(self, message_body):
        message = self.client.messages.create(
            from_=f'whatsapp:{self.twilio_from_number}',
            body=message_body,
            to=f'whatsapp:{self.twilio_to_number}'
        )
        print(message.body)

    def send_emails(self, email_list, email_body):
        with smtplib.SMTP(self.smtp_address) as connection:
            connection.starttls()
            connection.login(self.email, self.email_password)
            for email in email_list:
                connection.sendmail(
                    from_addr=self.email,
                    to_addrs=email,
                    msg=f"Subject:New Low Price Flight!\n\n{email_body}".encode('utf-8')
                )