import requests
from datetime import datetime

# To see the graph visit the link below:
# https://pixe.la/v1/users/sami2004/graphs/graph1.html

TOKEN = "fsdfih3223423jijw"
USERNAME = "sami2004"
GRAPH_ID = "graph1"

user_params = {
    "token": TOKEN,
    "username": USERNAME,
    "agreeTermsOfService": "yes",
    "notMinor": "yes",
}
graph_params = {
    "id": "graph1",
    "name": "Cycling Graph",
    "unit": "minute",
    "type": "int",
    "color": "sora",
}
headers = {
    "X-USER-TOKEN": TOKEN,
}
today = datetime.now().strftime("%Y%m%d")
specific_day = datetime(year=2025, month=4, day=11)

post_pixel_params = {
    "date": today,
    "quantity": input("How many minute did you code today? "),
}

pixela_endpoint = "https://pixe.la/v1/users"
# response=requests.post(url=pixela_endpoint,json=user_params)
# print(response.text)

graph_endpoint = f"{pixela_endpoint}/{USERNAME}/graphs"
# response=requests.post(url=graph_endpoint,json=graph_params,headers=headers)
# print(response.text)

post_pixel_endpoint = f"{graph_endpoint}/{GRAPH_ID}"
response = requests.post(url=post_pixel_endpoint, json=post_pixel_params, headers=headers)
print(response.text)

x = {"quantity": "9"}
specific_day2 = datetime(year=2025, month=4, day=11)
update_pixel_endpoint = f"{graph_endpoint}/{GRAPH_ID}/{specific_day2.strftime("%Y%m%d")}"
# response=requests.put(url=update_pixel_endpoint,json={"quantity":"15"},headers=headers)
# print(response.text)


# delete_pixel_endpoint=f"{graph_endpoint}/{GRAPH_ID}/{specific_day2.strftime("%Y%m%d")}"
# response=requests.delete(url=update_pixel_endpoint,headers=headers)
# print(response.text)
