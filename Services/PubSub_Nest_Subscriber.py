from dotenv import load_dotenv
from pathlib import Path
import json, os, subprocess, datetime
from pymongo import MongoClient
from google.oauth2 import service_account
from google.cloud import pubsub_v1
import logging
import logging.handlers
import sys

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
if os.name != 'nt':
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    my_logger.addHandler(handler)

my_logger.info('Initializing .env')

target_env_path = '/home/pi/HomeAutomation-DNN'  # default linux
if os.name == 'nt':
    target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation' # Windows
else:
    sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path

env_path = Path(target_env_path) / '.env'
load_dotenv(dotenv_path=env_path)

my_logger.info('Connecting to MongoDB')
my_client = MongoClient('mongodb://susmanserver:27017',
                        username=os.getenv("Google_Nest_Username"),
                        password=os.getenv("Google_Nest_Password"),
                        authSource='Google_Nest',
                        authMechanism='SCRAM-SHA-256')
my_db = my_client["Google_Nest"]
my_col = my_db["PubSub_Events"]


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
    try:
        my_logger.debug(message.data.decode('UTF-8'))
    except Exception as e:
        my_logger.critical(e)
    my_logger.debug('Starting Callback')
    try:
        payload = message.data.decode('UTF-8')
        json_payload = json.loads(payload)
        scrubbed_json_payload = scrubpayload(json_payload)
        insert_id = my_col.insert_one(scrubbed_json_payload).inserted_id
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
