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

inputs = tf.placeholder(tf.float32, [None, 416, 416, 3])
model = nets.YOLOv3COCO(inputs, nets.Darknet19)
classes={'0':'person','1':'bicycle','2':'car','3':'bike','5':'bus','7':'truck'}
list_of_classes=[0,1,2,3,5,7]

device_id = mi.getbackyardcameraname()

with tf.Session() as sess:
    sess.run(model.pretrained())
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
            while vcap.isOpened():
                ret, frame = vcap.read()

                img = cv2.resize(frame, (416, 416))
                imge = np.array(img).reshape(-1, 416, 416, 3)
                preds = sess.run(model.preds, {inputs: model.preprocess(imge)})

                boxes = model.get_boxes(preds, imge.shape[1:3])
                cv2.namedWindow('image', cv2.WINDOW_NORMAL)
                cv2.resizeWindow('image', 640, 480)

                boxes1 = np.array(boxes)
                for j in list_of_classes:  # iterate over classes
                    count = 0
                    if str(j) in classes:
                        lab = classes[str(j)]
                    if len(boxes1) != 0:
                        # iterate over detected vehicles
                        for i in range(len(boxes1[j])):
                            box = boxes1[j][i]
                            # setting confidence threshold as 40%
                            if boxes1[j][i][4] >= .40:
                                count += 1

                                cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 3)
                                cv2.putText(img, lab, (box[0], box[1]), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255),
                                            lineType=cv2.LINE_AA)
                    print(lab, ": ", count)

                # Display the output
                cv2.imshow("image", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break





                cv2.imshow('VIDEO', frame)
                cv2.waitKey(1)
                refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(seconds=30)
                if refresh_cutoff_utc > expire_time:
                    break

        except Exception as e:
            time.sleep(60)
            print(e)