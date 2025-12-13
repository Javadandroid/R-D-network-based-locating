import requests
import json
API_KEY = "AIzaSyD8dwT6cn8Et-JTVWvjDH-e0mIktGmydwA" 
base_url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={API_KEY}"

request_json = {
  "considerIp": "false",
  "cellTowers": [
    {
      "cellId": 43693383,
      "locationAreaCode": 22822,
      "mobileCountryCode": 432,
      "mobileNetworkCode": 35,
      "signalStrength": -69
    }
  ]
}

response = requests.post(base_url, json=request_json)
response.raise_for_status()
response_data = response.json()
print(response_data)