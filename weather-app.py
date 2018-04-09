import requests
import json
response = requests.get(
    'https://api.openweathermap.org/data/2.5/weather?units=imperial&id=4699066&APPID=1e1e9213cbe1601262c8d3628ed8fc3c'
).json()
print(response)