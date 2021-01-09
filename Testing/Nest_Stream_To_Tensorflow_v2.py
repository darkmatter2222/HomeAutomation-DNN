import sys
sys.path.append('/home/pi/HomeAutomation-DNN')
import Initialize_Project as ip
logger = ip.initialize()

import requests, json
import cv2
import time
import tensorflow as tf
import tensornets as nets
import numpy as np
import time
from dateutil import parser
from datetime import datetime, timezone, timedelta
from Helpers.Exception_Handling import Exception_Handling as eh
from Helpers.Mongo_Interface import Mongo_Interface as mi
import time
import numpy as np
import cv2

import multiprocessing as mp

from multiprocessing import Queue


def main():
    device_id = mi.getfrontdoorcameraname()

    while True:
        try:
            token = mi.getnestapiaccesstoken()
            url = f'https://smartdevicemanagement.googleapis.com/v1/{device_id}:executeCommand'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            data = {"command": "sdm.devices.commands.CameraLiveStream.GenerateRtspStream", "params": {}}
            response = requests.post(url=url, headers=headers, data=json.dumps(data))
            result = response.content.decode('ascii')
            json_result = json.loads(result)
            expire_time = parser.isoparse(json_result['results']['expiresAt'])
            cam = bufferless_camera(json_result['results']['streamUrls']['rtspUrl'], 640, 480)

            while True:
                refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(seconds=30)
                if refresh_cutoff_utc > expire_time:
                    break
                font = cv2.FONT_HERSHEY_SIMPLEX
                org = (50, 50)
                fontScale = 1
                color = (255, 0, 0)
                thickness = 2
                refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(minutes=5)
                refresh_cutoff_utc_epoch = refresh_cutoff_utc.timestamp()
                frame = cam.get_frame()
                frame = cv2.putText(frame, str(refresh_cutoff_utc_epoch), org, font,
                                    fontScale, color, thickness, cv2.LINE_AA)
                cv2.imshow('VIDEO', frame)
                cv2.waitKey(1)




        except Exception as e:
            print(e)


class bufferless_camera():

    def __init__(self, rtsp_url, width, height):
        #load pipe for data transmittion to the process
        self.parent_conn, child_conn = mp.Pipe()
        #load process
        self.p = mp.Process(target=self.grab_frames, args=(child_conn,rtsp_url))
        #start process
        self.p.daemon = True
        self.p.start()
        # frame size
        self.width = width
        self.height = height

    def end(self):
        #send closure request to process
        self.parent_conn.send(2)

    def grab_frames(self,conn,rtsp_url):
        #load cam into seperate process
        print("Cam Loading...")
        cap = cv2.VideoCapture(rtsp_url,cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print("Cam Loaded...")
        run = True

        while run:
            #grab frames from the buffer
            cap.grab()

            #receive input data
            rec_dat = conn.recv()

            #if frame requested
            if rec_dat == 1:
                #read current frame, send it to method that will return it to object detection
                ret,frame = cap.read()
                conn.send(frame)

            elif rec_dat ==2:
                #if close requested
                cap.release()
                run = False

        print("Camera Connection Closed")
        conn.close()

    def get_frame(self,resize=None):
        #send request
        self.parent_conn.send(1)
        # retrieve frame
        frame = self.parent_conn.recv()

        #reset request
        self.parent_conn.send(0)

        #return frame to object detection
        return cv2.resize(frame,(self.width, self.height))



if __name__ == "__main__":
    main()