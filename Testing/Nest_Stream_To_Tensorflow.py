import sys
sys.path.append('/home/pi/HomeAutomation-DNN')
import Initialize_Project as ip
logger = ip.initialize()

import requests, json
import cv2
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta
from Helpers.Exception_Handling import Exception_Handling as eh
from Helpers.Mongo_Interface import Mongo_Interface as mi



device_id = mi.getbackyardcameraname()

while True:
    try:
        token = mi.getnestapiaccesstoken()
        url = f'https://smartdevicemanagement.googleapis.com/v1/{device_id}:executeCommand'
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
        data = {"command": "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params": {}}
        response = requests.post(url=url, headers=headers, data=json.dumps(data))
        result = response.content.decode('ascii')
        json_result = json.loads(result)

        print(json_result)
        expire_time = parser.isoparse(json_result['results']['expiresAt'])
        vcap = cv2.VideoCapture(json_result['results']['streamUrls']['rtspUrl'])
        while True:
            ret, frame = vcap.read()
            cv2.imshow('VIDEO', frame)
            cv2.waitKey(1)
            refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(seconds=30)
            if refresh_cutoff_utc > expire_time:
                break

    except Exception as e:
        time.sleep(60)
        print(e)