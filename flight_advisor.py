from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db


def firebase_db_connect():
    cred = credentials.Certificate("firebaseServiceAccountKey.json")
    default_app = firebase_admin.initialize_app(cred, {'databaseURL':'https://mymillieassistant-default-rtdb.firebaseio.com/'})
    ref = db.reference("users")
    return ref 


app = Flask(__name__)
@app.route('/bot', methods=['POST'])
def bot():
    message = request.values.get('Body', '')
    from_number = request.values.get('From')

    resp = MessagingResponse()
    msg = resp.message()

    ref = firebase_db_connect()
    ref = db.reference("users")
    

    if "MyMillie, I want to find out if I'm going to be late!".lower() in message:
        msg.body('What is your flight number and airline?')
    else:
        msg.body('.test...')
    ref.set({str(from_number):message})
    return str(resp)
if __name__ == '__main__':
    app.run()
