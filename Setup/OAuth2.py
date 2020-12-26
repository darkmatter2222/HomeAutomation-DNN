import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from pymongo import MongoClient

target_env_path = '/home/pi/HomeAutomation-DNN'  # default linux
if os.name == 'nt':
    target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation' # Windows
else:
    sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path

env_path = Path(target_env_path) / '.env'
load_dotenv(dotenv_path=env_path)

db_name = 'OAuth2_Manager'
collection_name = 'Active_OAuth2'
my_client = MongoClient('mongodb://susmanserver:27017',
                        username=os.getenv("OAuth2_Manager_Username"),
                        password=os.getenv("OAuth2_Manager_Password"),
                        authSource=db_name,
                        authMechanism='SCRAM-SHA-256')
my_db = my_client[db_name]
my_col = my_db[collection_name]

flow = Flow.from_client_secrets_file(
    os.getenv('Google_Nest_Client_Secret_Windows_Location'),  # Only Windows Directory
    scopes=['https://www.googleapis.com/auth/sdm.service'],
    redirect_uri='https://www.google.com')

auth_url, _ = flow.authorization_url(prompt='consent')

print('Please go to this URL: {}'.format(auth_url))

code = input('Enter the authorization code: ')
token = flow.fetch_token(code=code)

payload = json.loads(str(token).replace('\'', '"'))

for key in flow.client_config:
    payload[key] = flow.client_config[key]

insert_id = my_col.insert_one(payload).inserted_id

print('Inserted to ID {}', insert_id)