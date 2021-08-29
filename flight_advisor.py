from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse


import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

#firebase needs to be initialized every instance
def firebase_initialize():
    try:
        default_app = firebase_admin.initialize_app(credentials.Certificate("firebaseServiceAccountKey.json"), {'databaseURL':'https://mymillieassistant-default-rtdb.firebaseio.com/'})
    except:
        pass 
    
def firebase_responses_upload():
    messages_ref = db.reference("responses")
    messages_ref.set(
        {
            100:{
                'id':100,
                'content':"Welcome to Flight Advisor! What's your airline and flight number?"
            },
            101:{
                'id':101,
                'content':"Thanks! Last question: What's your current address?"
            },
            102:{
                'id':102,
                'content':"You should leave at {LEAVE_TIME}. Based on our math: {DRIVE_TIME} min drive, {TRANSIT_TIME} min transit from parking lot, {SECURITY_TIME} min security line"
            },
            103:{
                'id':103,
                'content':"uh oh - I don't know how to respond..."
            }
        }
    )
    
def firebase_response_get(response_id):
    #{'100': {'content': "Welcome to Flight Advisor! What's your airline and flight number?", 'id': 100}, '101': {'content': "Thanks! Last question: What's your current address?", 'id': 101}}
    return db.reference("responses").child(str(response_id)).get()

def firebase_customer_data_get(phone_number):
    return db.reference("customers").child(str(phone_number)).get()

def firebase_conversation_save(phone_number,message,message_phone_number=None):
    db.reference("conversations").child(str(phone_number)).push(
        {
            "message":message,
            "phone_number":phone_number if not message_phone_number else message_phone_number
        }
    )
    
def firebase_customer_update(phone_number,data):
    db.reference("customers").child(phone_number).update(data)

    
def customer_data_generate(phone_number,customer_message,response_id):
    if response_id == 100:
        return {
            'phone_number':phone_number,
            'response_id':response_id
        }
    elif response_id == 101:
        return {
            'flight_number':customer_message,
            'response_id':response_id
        }
    elif response_id == 102:
        return {
            'location':customer_message,
            'response_id':response_id
        }
    else:
        return {
            'response_id':response_id
        }

def firebase_customer_data_update(phone_number,customer_message,response_id):
    customer_updated_data = customer_data_generate(phone_number,customer_message,response_id)
    firebase_customer_update(phone_number,customer_updated_data)

    
def response_id_determine(customer_data):
    if customer_data == None:
        return 100
    elif customer_data['response_id'] == 100:
        return 101
    elif customer_data['response_id'] == 101:
        return 102
    else:
        return 103
    
def respond(phone_number):
    customer_data = firebase_customer_data_get(phone_number)    
    response_id = response_id_determine(customer_data)
    response = firebase_response_get(response_id)['content']
    return response_id,response
    
def respond_save(phone_number,customer_message):
    firebase_initialize()
    firebase_conversation_save(phone_number,customer_message)
    
    response_id,response = respond(phone_number)
    
    firebase_customer_data_update(phone_number,customer_message,response_id)    
    firebase_conversation_save(phone_number,response,message_phone_number='4069645543')
    return response


app = Flask(__name__)
@app.route('/bot', methods=['POST'])
def bot():
    customer_message = request.values.get('Body', '')
    phone_number = request.values.get('From').replace("+","")

    resp = MessagingResponse()
    msg = resp.message()

    response = respond_save(phone_number,customer_message)
    msg.body(response)
    return str(resp)
if __name__ == '__main__':
    app.run()



