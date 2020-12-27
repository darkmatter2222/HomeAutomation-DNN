import json
import os
import time
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging
import logging.handlers

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
if os.name != 'nt':
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    my_logger.addHandler(handler)
else:
    my_logger.addHandler(logging.StreamHandler())

my_logger.info('Initializing .env')

target_env_path = '/home/pi/secure'  # default linux
if os.name == 'nt':
    target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation' # Windows
else:
    sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path
    sys.path.append('/home/pi/secure')  # add this to the path

env_path = Path(target_env_path) / '.env'
load_dotenv(dotenv_path=env_path)

my_logger.info('Connecting to MongoDB')

db_name = 'OAuth2_Manager'
collection_name = 'Active_OAuth2'
my_client = MongoClient('mongodb://susmanserver:27017',
                        username=os.getenv("OAuth2_Manager_Username"),
                        password=os.getenv("OAuth2_Manager_Password"),
                        authSource=db_name,
                        authMechanism='SCRAM-SHA-256')
my_db = my_client[db_name]
my_col = my_db[collection_name]

my_logger.info('Beginning Refresh Loop...')

while True:
    time.sleep(60)
    try:
        refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(minutes=5)
        refresh_cutoff_utc_epoch = refresh_cutoff_utc.timestamp()
        connections_needing_refresh = my_col.find({'expires_at': {"$lt": refresh_cutoff_utc_epoch}})

        for connection in connections_needing_refresh:
            my_logger.info(f'Refreshing {str(connection["_id"])}...')
            try:
                payload = {'client_id': connection['client_id'], 'client_secret': connection['client_secret'],
                           'refresh_token': connection['refresh_token'], 'grant_type': 'refresh_token'}
                response = requests.post(connection['token_uri'], params=payload)

                refresh_response = json.loads((response.text))

                new_experation = (datetime.now(timezone.utc) + timedelta(seconds=refresh_response['expires_in'])).timestamp()

                my_query = {'_id': connection['_id']}
                new_values = {
                    "$set": {"access_token": refresh_response['access_token'], 'expires_in': refresh_response['expires_in'],
                             'expires_at': new_experation}}

                my_col.update_one(my_query, new_values)
                my_logger.info(f'Refresh {str(connection["_id"])} complete')
            except Exception as e:
                my_logger.critical(e)
    except Exception as e:
        my_logger.critical(e)
