from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import requests

from suds.client import Client
import googlemaps
import json
from datetime import datetime




def faware_response_get(flight_number):
    username = 'mymillieapp'
    apiKey = '0af3fd379266a7e3240ed6511692e2ec0251cd21'
    url = 'http://flightxml.flightaware.com/soap/FlightXML2/wsdl'
    response = requests.get(url)
    api = Client(url, username=username, password=apiKey)
    result = api.service.FlightInfo(flight_number)
    return result



def faware_flight_info_from_flight_number(flight_number):
    result = faware_response_get(flight_number)
    airport = result[1][0]['originName']
    departure_time = result[1][0]['filed_departuretime']
    return airport,departure_time









def gmap_directions_get(location,airport):
    gmaps = googlemaps.Client(key='AIzaSyD3ZhZmNA1az094GaNXdA14ADBAxaz5uyY')
    now = datetime.now()
    directions = gmaps.directions(location,airport,departure_time=now)#mode="transit"
    return directions
                                    
def gmap_duration_get(location,airport):
    directions = gmap_directions_get(location,airport)
    duration = directions[0]['legs'][0]['duration']['value']
    return duration 
                                         
                                         
                                         
                                         
                            
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
                'content':"You should leave at {leave_time}. Based on our math: {drive_time} min drive, {transit_time} min transit from parking lot, {security_time} min security line"
            },
            103:{
                'id':103,
                'content':"uh oh - I don't know how to respond..."
            }
        }
    )
    

def firebase_customer_data_get(phone_number):
    customer_data = db.reference("customers").child(str(phone_number)).get()
    return {} if customer_data == None else customer_data

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
    return customer_updated_data
    
def response_id_determine(customer_data):
    if 'response_id' not in customer_data.keys():
        return 100
    elif customer_data['response_id'] == 100:
        return 101
    elif customer_data['response_id'] == 101:
        return 102
    else:
        return 100
    
def dictionary_combine(D1,D2):
    return dict(list(D1.items()) + list(D2.items()))

def response_variable_update(response,customer_data):
    response = response['content']
    for k,v in customer_data.items():
        response = response.replace("{"+str(k)+"}",str(v))
    return response 
    
def firebase_response_get(response_id,customer_data):
    #{'100': {'content': "Welcome to Flight Advisor! What's your airline and flight number?", 'id': 100}, '101': {'content': "Thanks! Last question: What's your current address?", 'id': 101}}
    response = db.reference("responses").child(str(response_id)).get()

    response = response_variable_update(response,customer_data)
    return response

def time_stamp_from_unix(unix):
    ts = datetime.fromtimestamp(unix)
    return ts.strftime('%H:%M%p (%m/%d)')

def seconds_to_minutes_format(seconds):
    return str(round(seconds/60)) + " mins"

def customer_data_calculate(flight_number,location):
    airport,departure_time_unix = faware_flight_info_from_flight_number(flight_number)
    drive_time_seconds = gmap_duration_get(location,airport)
    transit_time_seconds = 15*60
    security_time_seconds = 15*60
    leave_time_unix = departure_time_unix - drive_time_seconds - transit_time_seconds - security_time_seconds
    
    leave_time = time_stamp_from_unix(leave_time_unix)
    transit_time = seconds_to_minutes_format(transit_time_seconds)
    drive_time = seconds_to_minutes_format(drive_time_seconds)
    security_time = seconds_to_minutes_format(security_time_seconds)
    departure_time= time_stamp_from_unix(departure_time_unix)

    return {
        
        'departure_time_unix':departure_time_unix,
        'leave_time_unix':leave_time_unix,
        'drive_time_seconds':drive_time_seconds,
        'transit_time_seconds':transit_time_seconds,
        'security_time_seconds':security_time_seconds,

        'airport':leave_time,
        'departure_time':departure_time,
        'leave_time':leave_time,
        'transit_time':transit_time,
        'drive_time':drive_time,
        'security_time':security_time
    }
    
    
def customer_data_calculate_update(customer_data,phone_number,customer_message,response_id):
    customer_updated_data = firebase_customer_data_update(phone_number,customer_message,response_id) 
    customer_data = dictionary_combine(customer_data,customer_updated_data)
    #customer_data.update(customer_updated_data)
    if 'flight_number' in customer_data.keys() and 'location' in customer_data.keys():
        customer_calculated_data = customer_data_calculate(customer_data['flight_number'],customer_data['location'])
        customer_data = dictionary_combine(customer_data,customer_calculated_data)
        #customer_data.update(customer_calculated_data)
    return customer_data 


def respond_save(phone_number,customer_message):
    print (customer_message + ' - '+ phone_number)
    firebase_initialize()
    firebase_conversation_save(phone_number,customer_message)
    
    customer_data = firebase_customer_data_get(phone_number) 
    response_id = response_id_determine(customer_data)
    
    customer_data = customer_data_calculate_update(customer_data,phone_number,customer_message,response_id)
    
    response = firebase_response_get(response_id,customer_data)#['content']
    
    firebase_conversation_save(phone_number,response,message_phone_number='4069645543')
    print (response + " - 4069645543" )
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



