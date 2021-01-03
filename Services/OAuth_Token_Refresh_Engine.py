import sys
sys.path.append('/home/pi/HomeAutomation-DNN')
import Initialize_Project as ip
logger = ip.initialize()

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
from Helpers.Exception_Handling import Exception_Handling as eh
from Helpers.Mongo_Interface import Mongo_Interface as mi

mi.initializedb()

logger.info('Beginning Refresh Loop...')

while True:
    time.sleep(60)
    try:
        refresh_cutoff_utc = datetime.now(timezone.utc) + timedelta(minutes=5)
        refresh_cutoff_utc_epoch = refresh_cutoff_utc.timestamp()
        connections_needing_refresh = mi.getauthrecordsneedingrefresh(refresh_cutoff_utc_epoch)

        for connection in connections_needing_refresh:
            logger.info(f'Refreshing {str(connection["_id"])}...')
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

                mi.updateauthrecord(my_query, new_values)
                logger.info(f'Refresh {str(connection["_id"])} complete')
            except Exception as e:
                message = eh.formatexception(e)
                logger.critical(message)
    except Exception as e:
        message = eh.formatexception(e)
        logger.critical(message)
