from dotenv import load_dotenv
from pathlib import Path
import json, os, subprocess, datetime
import uuid
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
from google.oauth2 import service_account
from google.cloud import pubsub_v1
from bson.objectid import ObjectId
import logging
import requests
import logging.handlers
import PIL.Image as Image
import sys, io

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
if os.name != 'nt':
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    my_logger.addHandler(handler)

my_logger.info('Initializing .env')
target_image_root = '/home/pi/neural/HomeAutomation-DNN/images'
target_env_path = '/home/pi/secure'  # default linux
if os.name == 'nt':
    target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation' # Windows
    target_image_root = '../../testing'
else:
    sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path
    sys.path.append('/home/pi/secure')  # add this to the path

env_path = Path(target_env_path) / '.env'
load_dotenv(dotenv_path=env_path)

nest_metadata = {'devices': {}}
nest_metadata_expiration_seconds = 3600
nest_metadata_last_refresh = datetime.now(timezone.utc) - timedelta(minutes=60)

my_logger.info('Connecting to MongoDB')
my_client = MongoClient('mongodb://susmanserver:27017',
                        username=os.getenv("Google_Nest_Username"),
                        password=os.getenv("Google_Nest_Password"),
                        authSource='Google_Nest',
                        authMechanism='SCRAM-SHA-256')
my_db = my_client["Google_Nest"]
my_col = my_db["PubSub_Events"]

def getaccesstoken():
    db_name = 'OAuth2_Manager'
    collection_name = 'Active_OAuth2'
    my_client = MongoClient('mongodb://susmanserver:27017',
                            username=os.getenv("OAuth2_Manager_Username"),
                            password=os.getenv("OAuth2_Manager_Password"),
                            authSource=db_name,
                            authMechanism='SCRAM-SHA-256')
    my_db = my_client[db_name]
    my_col = my_db[collection_name]
    token = my_col.find({'_id': ObjectId('5fd61e859532201850007cdf')})[0]['access_token']
    return token

def pullimage(device_id, event_id, access_token, payload):
    url = f'https://smartdevicemanagement.googleapis.com/v1/{device_id}:executeCommand'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
    data = {"command": "sdm.devices.commands.CameraEventImage.GenerateImage", "params": {"eventId": event_id}}
    response = requests.post(url=url, headers=headers, data=json.dumps(data))
    result = response.content.decode('ascii')
    json_result = json.loads(result)
    url = json_result['results']['url']
    headers = {'Content-Type': 'application/json', 'Authorization': f'{json_result["results"]["token"]}'}
    response = requests.get(url=url, headers=headers)
    image = Image.open(io.BytesIO(response.content))
    unique_id = str(uuid.uuid1())

    this_image_target = \
        f"{target_image_root}/{payload['resourceUpdate']['displayName']}/{payload['resourceUpdate']['type']}"

    if not os.path.exists(this_image_target):
        os.makedirs(this_image_target)

    image.save(f"{this_image_target}/{unique_id}.jpeg")
    my_logger.info(f'Image Saved')
    return unique_id

def pullimages(payload):
    try:
        if 'events' in payload['resourceUpdate']:
            for key in payload['resourceUpdate']['events'].keys():
                if 'Camera' in key:
                    access_token = getaccesstoken()
                    image_uid = pullimage(device_id=payload['resourceUpdate']['name'],
                              event_id=payload['resourceUpdate']['events'][key]['eventId'],
                              access_token=access_token,
                              payload=payload)
                    payload['resourceUpdate']['events'][key]['image_uid'] = image_uid

    except Exception as e:
        my_logger.critical(e)

    return payload

def pullmetainfo(last_refresh):
    perform_refresh = False
    if last_refresh < datetime.now(timezone.utc):
        last_refresh = datetime.now(timezone.utc) + timedelta(minutes=nest_metadata_expiration_seconds)
        perform_refresh = True
    if perform_refresh:
        try:
            my_logger.info('Connecting to MongoDB, pulling auth')
            db_name = 'OAuth2_Manager'
            collection_name = 'Active_OAuth2'
            my_client = MongoClient('mongodb://susmanserver:27017',
                                    username=os.getenv("OAuth2_Manager_Username"),
                                    password=os.getenv("OAuth2_Manager_Password"),
                                    authSource=db_name,
                                    authMechanism='SCRAM-SHA-256')
            my_db = my_client[db_name]
            my_col = my_db[collection_name]
            token = my_col.find({'_id': ObjectId('5fd61e859532201850007cdf')})[0]
            my_logger.info('Retrieving Devices')
            url = f'https://smartdevicemanagement.googleapis.com/v1/enterprises/{os.getenv("Google_Nest_Prodect_ID")}/devices'
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token["access_token"]}'}
            response = requests.get(url=url, headers=headers)
            response_json = json.loads(response.text)
            for device in response_json['devices']:
                nest_metadata['devices'][device['name']] = \
                    {
                        'type': device['type'].replace('.', '_'),
                        'displayName': device['parentRelations'][0]['displayName']
                    }

            my_logger.info(f'Meta Downloaded')
        except Exception as e:
            my_logger.critical(e)
    return last_refresh

def applymetadata(payload):
    try:
        payload['resourceUpdate']['type'] = nest_metadata['devices'][payload['resourceUpdate']['name']]['type']
        payload['resourceUpdate']['displayName'] = \
            nest_metadata['devices'][payload['resourceUpdate']['name']]['displayName']
    except Exception as e:
        my_logger.critical(e)
    return payload

def scrubpayload(payload):
    try:
        if 'events' in payload['resourceUpdate']:
            my_logger.info('An "event" event has occurred')
            list = []
            for key in payload['resourceUpdate']['events'].keys():
                list.append(key)
            for this_key in list:
                payload['resourceUpdate']['events'][this_key.replace('.', '_')] = \
                    payload['resourceUpdate']['events'].pop(this_key)
    except Exception as e:
        my_logger.critical(e)

    try:
        if 'traits' in payload['resourceUpdate']:
            my_logger.info('A "trait" event has occurred')
            list = []
            for key in payload['resourceUpdate']['traits'].keys():
                list.append(key)
            for this_key in list:
                payload['resourceUpdate']['traits'][this_key.replace('.', '_')] = \
                    payload['resourceUpdate']['traits'].pop(this_key)
    except Exception as e:
        my_logger.critical(e)

    return payload


def callback(message):
    global nest_metadata_last_refresh
    try:
        my_logger.debug(message.data.decode('UTF-8'))
    except Exception as e:
        my_logger.critical(e)
    my_logger.debug('Starting Callback')
    try:
        payload = message.data.decode('UTF-8')
        json_payload_1 = json.loads(payload)
        json_payload_2 = scrubpayload(json_payload_1)
        nest_metadata_last_refresh = pullmetainfo(nest_metadata_last_refresh)
        json_payload_3 = applymetadata(json_payload_2)
        json_payload_4 = pullimages(json_payload_3)
        insert_id = my_col.insert_one(json_payload_4).inserted_id
        my_logger.debug(insert_id)
    except Exception as e:
        my_logger.critical(e)

    my_logger.debug('Starting ack')
    try:
        message.ack()
    except Exception as e:
        my_logger.critical(e)


my_logger.info('Setting Creds')

cred_location = os.getenv('Google_PubSub_Client_Creds_Linux_Location')
if os.name == 'nt':
    cred_location = os.getenv('Google_PubSub_Client_Creds_Windows_Location')
credentials = service_account.Credentials.from_service_account_file(cred_location)

my_logger.info('Creating Sub Client')
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
# subscription_name = projects/<Project Name>/subscriptions/<Something you Chose>
subscription_name = os.getenv('Google_PubSub_Subscription_Name')

my_logger.info('Subscribing...')
future = subscriber.subscribe(subscription_name, callback)

my_logger.info('Listening...')
try:
    future.result()
except KeyboardInterrupt:
    my_logger.critical('KeyboardInterrupt')
    future.cancel()
except Exception as e:
    my_logger.critical(e)
    future.cancel()

my_logger.debug('Exiting')
