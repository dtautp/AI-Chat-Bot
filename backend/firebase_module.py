import pyrebase
import os

config = {
    'apiKey': os.environ.get('FIREBASE_API_KEY'),
    'authDomain': os.environ.get("FIREBASE_AUTH_DOMAIN"),
    'projectId': os.environ.get("FIREBASE_PROJECT_ID"),
    'storageBucket': os.environ.get("FIREBASE_STORAGE_BUCKET"),
    'messagingSenderId': os.environ.get("FIREBASE_MESSAGINGSENDER_ID"),
    'appId': os.environ.get("FIREBASE_APP_ID"),
    'databaseURL': os.environ.get("FIREBASE_DATABASE_URL")
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

def select_system_prompt_by_id(system_prompt_id):
    system_prompt = dict(db.child('system_prompt').child(system_prompt_id).get().val())
    return system_prompt

def insert_request(request):
    db.child('requests').push(request)
    return True