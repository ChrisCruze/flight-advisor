from flask import Flask, request
import requests
from twilio.twiml.messaging_response import MessagingResponse
app = Flask(__name__)
@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False
    if "MyMillie, I want to find out if I'm going to be late!".lower() in incoming_msg:
        msg.body('What is your flight number and airline?')
    else:
        msg.body('....')
    return str(resp)
if __name__ == '__main__':
    app.run()
