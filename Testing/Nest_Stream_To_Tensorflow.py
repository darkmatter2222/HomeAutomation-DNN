import sys
sys.path.append('/home/pi/HomeAutomation-DNN')
import Initialize_Project as ip
logger = ip.initialize()

import requests, json
import cv2
from Helpers.Exception_Handling import Exception_Handling as eh
from Helpers.Mongo_Interface import Mongo_Interface as mi

token = mi.getnestapiaccesstoken()

device_id = ''

url = f'https://smartdevicemanagement.googleapis.com/v1/{device_id}:executeCommand'
headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
data = {"command": "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params": {}}
response = requests.post(url=url, headers=headers, data=json.dumps(data))
result = response.content.decode('ascii')
json_result = json.loads(result)

print(json_result)

vcap = cv2.VideoCapture(json_result['results']['streamUrls']['rtspUrl'])
while(1):
    ret, frame = vcap.read()
    cv2.imshow('VIDEO', frame)
    cv2.waitKey(1)