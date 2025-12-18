import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime
# Exel Sheet link
# https://docs.google.com/spreadsheets/d/15cu7TRI3f-w8Zuy7x3aTPV4ixx1m4Sx7xmnEKwfLarI/edit?gid=0#gid=0

load_dotenv()

WEIGHT = 56
AGE = 21
HEIGHT = 171
GENDER = "male"

APP_ID = os.getenv("APP_ID")
API_KEY = os.getenv("API_KEY")
Sheety_Authorization = os.getenv("Sheety_Authorization")

exercise_endpoint = "https://trackapi.nutritionix.com/v2/natural/exercise"
exercise_text = input("Tell me which exercises you did: ")

headers = {
    "x-app-id": APP_ID,
    "x-app-key": API_KEY,
}
exercise_params = {
    "query": exercise_text,
    "weight_kg": WEIGHT,
    "height_cm": HEIGHT,
    "age": AGE,
    "gender": GENDER,
}

response = requests.post(exercise_endpoint, headers=headers, json=exercise_params)
response.raise_for_status()

data = response.json()
exercises = data["exercises"]
# print(json.dumps(data, indent=2))

now = datetime.now()
now_time = now.strftime("%X")  # same as %H:%M:%S
today_date = now.strftime("%d/%m/%Y")

sheety_endpoint = os.environ.get("sheety_endpoint")

sheety_headers = {"Authorization": Sheety_Authorization}

for exercise in exercises:
    sheety_params = {
        "workout": {
            "date": today_date,
            "time": now_time,
            "exercise": exercise["name"].title(),
            "duration": exercise["duration_min"],
            "calories": exercise["nf_calories"],
        }
    }
    response = requests.post(sheety_endpoint, json=sheety_params, headers=sheety_headers)
    response.raise_for_status()
    # print(response.text)

# import os
# print(os.environ.get("APP_ID")) # same as os.getenv("APP_ID")
# print((os.environ.get("num"))) # same as os.getenv("APP_ID")
# print(os.environ.get("APP_ID5", "Message")) # same as os.getenv("APP_ID3", "Message")
# print(os.environ["APP_ID5"]) # Raises a KeyError (exception)
