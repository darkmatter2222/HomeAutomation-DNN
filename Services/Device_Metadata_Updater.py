from dotenv import load_dotenv
from pathlib import Path
import requests
import time
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
import json, os, subprocess, sys
import logging
import logging.handlers

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
if os.name != 'nt':
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    my_logger.addHandler(handler)

my_logger.info('Initializing .env')

target_env_path = '/home/pi/secure'  # default linux
if os.name == 'nt':
    target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation' # Windows
else:
    sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path
    sys.path.append('/home/pi/secure')  # add this to the path

env_path = Path(target_env_path) / '.env'
load_dotenv(dotenv_path=env_path)

my_logger.info('Cycle Started')

while True:
    time.sleep(3600)
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

        name_type_dict = {}
        response_json = json.loads(response.text)
        for device in response_json['devices']:
            name_type_dict[device['name']] = device['type'].replace('.', '_')
        my_logger.info('Connecting to MongoDB, pulling records to update')
        my_client = MongoClient('mongodb://susmanserver:27017',
                                username=os.getenv("Google_Nest_Username"),
                                password=os.getenv("Google_Nest_Password"),
                                authSource='Google_Nest',
                                authMechanism='SCRAM-SHA-256')
        my_db = my_client["Google_Nest"]
        my_col = my_db["PubSub_Events"]

        missing_type_records = my_col.find({"resourceUpdate.type": {'$exists': False}})
        my_logger.info('Updating Records...')
        count = 0
        for record in missing_type_records:
            my_query = {'_id': record['_id']}
            new_values = {"$set": {"resourceUpdate.type": name_type_dict[record['resourceUpdate']['name']]}}
            my_col.update_one(my_query, new_values)
            count += 1

        my_logger.info(f'{count} records updated')
    except Exception as e:
        my_logger.critical(e)

