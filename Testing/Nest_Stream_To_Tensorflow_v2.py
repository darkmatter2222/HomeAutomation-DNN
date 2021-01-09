import sys
sys.path.append('/home/pi/HomeAutomation-DNN')
import Initialize_Project as ip
logger = ip.initialize()

import cv2, queue, threading, time
import requests, json
import cv2
import time
import numpy as np
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta
from Helpers.Exception_Handling import Exception_Handling as eh
from Helpers.Mongo_Interface import Mongo_Interface as mi
import time
import numpy as np
import cv2

target_frame_rate = 12

import multiprocessing as mp

from multiprocessing import Queue

# bufferless VideoCapture
class VideoCapture:

    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

  # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            #if not self.q.empty():
                #try:
                #    self.q.get_nowait()   # discard previous (unprocessed) frame
                #except queue.Empty:
                #    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()

    def readspead(self):
        return self.q.qsize() / target_frame_rate

    def queuesize(self):
        return self.q.qsize()

    def dumpqueue(self):
        return self.q.clear()


device_id = mi.getbackyardcameraname()
refresh = True

font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 1
fontColor = (255, 255, 255)
lineType = 2


while True:
    try:
        if refresh:
            token = mi.getnestapiaccesstoken()
            url = f'https://smartdevicemanagement.googleapis.com/v1/{device_id}:executeCommand'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            data = {"command": "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params": {}}
            response = requests.post(url=url, headers=headers, data=json.dumps(data))
            result = response.content.decode('ascii')
            json_result = json.loads(result)

            print(json_result)
            expire_time = parser.isoparse(json_result['results']['expiresAt'])
            cap = VideoCapture(json_result['results']['streamUrls']['rtspUrl'])
            #vcap = cv2.VideoCapture(json_result['results']['streamUrls']['rtspUrl'])
            refresh = False

        cap_adjuster = cap.readspead()
        read_speed = (1/target_frame_rate)
        if cap_adjuster > 100:
            cap.dumpqueue()
            print("queue dumped")
        if cap_adjuster > 1.4:
            read_speed = read_speed / 1.4
        elif cap_adjuster > 0:
            read_speed = read_speed / cap_adjuster
        time.sleep(abs(read_speed))  # simulate time between events
        frame = cap.read()
        refresh_cutoff_utc = datetime.now(timezone.utc)
        refresh_cutoff_utc_epoch = refresh_cutoff_utc.timestamp()

        cv2.putText(frame, str(f"Epoch Time: {refresh_cutoff_utc_epoch}"),
                    (10, 50),
                    font,
                    fontScale,
                    fontColor,
                    lineType)
        act_frame_rate = round(1/read_speed,2)
        act_color = (255, 0, 0)
        if act_frame_rate > target_frame_rate:
            act_color = (0, 255, 0)
        cv2.putText(frame, str(f"Frame Rate: {act_frame_rate}/{target_frame_rate}"),
                    (10, 100),
                    font,
                    fontScale,
                    act_color,
                    lineType)
        cv2.putText(frame, str(f"Queue Size: {cap.queuesize()}"),
                    (10, 150),
                    font,
                    fontScale,
                    fontColor,
                    lineType)

        cv2.imshow('VIDEO', frame)
        cv2.waitKey(1)
        refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(seconds=30)
        if refresh_cutoff_utc > expire_time:
            refresh = True

    except Exception as e:
        time.sleep(60)
        print(e)









