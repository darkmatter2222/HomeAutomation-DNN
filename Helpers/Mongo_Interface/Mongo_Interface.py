from pymongo import MongoClient
from bson.objectid import ObjectId
import os

mongo_host = 'mongodb://susmanserver:27017'
mongo_authMechanism= 'SCRAM-SHA-256'

google_nest_db_name = 'Google_Nest'
pubsub_events_collection_name = 'PubSub_Events'
google_nest_db_client = MongoClient(mongo_host,
                        username=os.getenv("Google_Nest_Username"),
                        password=os.getenv("Google_Nest_Password"),
                        authSource=google_nest_db_name,
                        authMechanism=mongo_authMechanism)
google_nest_db = google_nest_db_client[google_nest_db_name]
pubsub_events_collection = google_nest_db[pubsub_events_collection_name]

oauth2_manager_db_name = 'OAuth2_Manager'
oauth2_manager_collection_name = 'Active_OAuth2'
oauth2_manager_db_client = MongoClient(mongo_host,
                        username=os.getenv("OAuth2_Manager_Username"),
                        password=os.getenv("OAuth2_Manager_Password"),
                        authSource=oauth2_manager_db_name,
                        authMechanism=mongo_authMechanism)
oauth2_manager_db = oauth2_manager_db_client[oauth2_manager_db_name]
oauth2_manager_collection = oauth2_manager_db[oauth2_manager_collection_name]


def getnestapiaccesstoken():
    token = oauth2_manager_collection.find({'_id': ObjectId('5fd61e859532201850007cdf')})[0]['access_token']
    return token

def insertnestpayload(payload):
    insert_id = pubsub_events_collection.insert_one(payload).inserted_id
    return insert_id

def getauthrecordsneedingrefresh(refresh_cutoff_utc_epoch):
    records = oauth2_manager_collection.find({'expires_at': {"$lt": refresh_cutoff_utc_epoch}})
    return records

def updateauthrecord(query, data):
    oauth2_manager_collection.update_one(query, data)

