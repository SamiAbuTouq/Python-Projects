from pprint import pprint

import requests
from dotenv import load_dotenv
import os
from  requests.auth import HTTPBasicAuth

load_dotenv()

class DataManager:
    #This class is responsible for talking to the Google Sheet.
    def __init__(self):
        self._user = os.environ["SHEETY_USERNAME"]
        self._password = os.environ["SHEETY_PASSWORD"]
        self.users_endpoint = os.environ["SHEETY_USERS_ENDPOINT"]
        self.prices_endpoint = os.environ["SHEETY_PRICES_ENDPOINT"]
        self._authorization=HTTPBasicAuth(self._user,self._password)
        self.destination_data = {}
        self.customer_data = {}


    def get_destination_data(self):
        response = requests.get(url=self.prices_endpoint,auth=self._authorization)
        response.raise_for_status()
        data = response.json()
        self.destination_data = data["prices"]
        # pprint(data)
        return self.destination_data


    def update_destination_codes(self):
        for city in self.destination_data:
            new_data={
                "price":{
                    "iataCode": city["iataCode"]
                }
            }
            response = requests.put(url=f"{self.prices_endpoint}/{city['id']}",json=new_data,auth=self._authorization)
           # print(response.text)

    # HTTPBasicAuth(USERNAME, PASSWORD):
    # automatically encodes your username and password into a Base64 string.

    def get_customer_emails(self):
        response = requests.get(url=self.users_endpoint,auth=self._authorization)
        data = response.json()
        # See how Sheet data is formatted so that you use the correct column name!
        #pprint(data)
        # Name of spreadsheet 'tab' with the customer emails should be "users".
        self.customer_data = data["users"]
        return self.customer_data