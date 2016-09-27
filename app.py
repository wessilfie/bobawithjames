#!/usr/bin/env python

import os

import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.tools import run_flow, argparser
import urllib2
import urllib
import pytz

import datetime
import uuid

from twilio.rest.lookups import TwilioLookupsClient
from twilio.rest.exceptions import TwilioRestException
from twilio.rest import TwilioRestClient

import flask
from flask import Flask, render_template, json, request, redirect

from time import strftime
import dateutil.parser

try:
    import argparse
    # flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    flags = argparser.parse_args([])
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Quickstart'
SECRET_KEY = str(uuid.uuid4())

app = Flask(__name__)
app.debug = True 
app.secret_key = str(uuid.uuid4())

@app.route('/')
def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """

    d = datetime.datetime.now()
    EST = pytz.timezone('US/Eastern')
    d = EST.localize(d).isoformat()

    f = {'key' : 'AIzaSyCMCTCPE4Rjla4uUs4vrO1nyQVa0Xu5XAc',
    'maxResults' : '50',
    'orderBy' : 'startTime',
    'singleEvents' : 'true',
    'timeMin' : d}

    flags = urllib.urlencode(f)

    url = "https://www.googleapis.com/calendar/v3/calendars/jamesxue100@gmail.com/events?" + flags

    content = urllib2.urlopen(url).read()
    
    content = json.loads(content)

    events = content['items'][:40]

    if not events:
        print('No upcoming events found.')

    return_list = []
    latest_time = strftime('%-I:%M %p')
    latest_time_24 = strftime('%H:%M')
    latest_time_noampm = strftime('%H:%M')
    latest_date = strftime("%a %m/%d/%y")

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        start = dateutil.parser.parse(start)
        start_time = start.strftime('%-I:%M %p')
        start_time_24 = start.strftime('%H:%M')
        start_time_noampm = start.strftime('%H:%M')
        start_date = start.strftime("%a %m/%d/%y")
        end = dateutil.parser.parse(end)
        end_time = end.strftime('%-I:%M %p')
        end_time_24 = end.strftime('%H:%M')
        end_time_noampm = end.strftime('%H:%M')
        end_date = end.strftime("%a %m/%d/%y")

        if (start_date == latest_date):
            if (start_time_24 > latest_time_24):
                if (latest_time_24 < '10:00'):
                    latest_time = end_time
                    latest_time_24 = end_time_24
                    latest_time_noampm = end_time_noampm
                    latest_date = end_date
                    continue

                FMT = '%H:%M'
                tdelta = datetime.datetime.strptime(start_time_noampm, FMT) - datetime.datetime.strptime(latest_time_noampm, FMT)
                if abs(tdelta.total_seconds()) >= 1800:
                    return_list.append([latest_time, latest_date, start_time, start_date])

        else:
            return_list.append([latest_time, latest_date, start_time, start_date])
        latest_time = end_time
        latest_time_24 = end_time_24
        latest_time_noampm = end_time_noampm
        latest_date = end_date

    return render_template('index.html', api_data=return_list)

@app.route('/oauth2callback')
def oauth2callback():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    flow = client.flow_from_clientsecrets(
        'client_secret.json',
        scope='https://www.googleapis.com/auth/calendar',
        redirect_uri=flask.url_for('oauth2callback', _external=True))
    if 'code' not in flask.request.args:
        auth_uri = flow.step1_get_authorize_url()
        return flask.redirect(auth_uri)
    else:
        auth_code = flask.request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        flask.session['credentials'] = credentials.to_json()
        return flask.redirect(flask.url_for('main'))


@app.route('/signup', methods = ['GET','POST'])
def signup():
    name = request.form['name']
    phone = request.form['phone']
    time = request.form['time']
    location = request.form['location']
    print(name, phone, time)  

    if is_valid_number(phone) == False:
        return redirect('/ohno')

    else:

        account_sid = get_credentials()[0]
        auth_token = get_credentials()[1]

        client = TwilioRestClient(account_sid, auth_token)

        #message to client
        message = client.messages.create(to=phone, from_="(509)774-2976",
                                             body="Hey " + name + "! This is your confirmation that you're getting boba with James at " + location + " on " + time + ". His phone number is (949)554-5535.")

        #message to me
        message = client.messages.create(to="(949)554-5535", from_="(509)774-2976",
                                             body=("Hey James, you're getting boba with " + name + " at " + location + " on " + time + ". Their phone number is " + phone + "."))

        return redirect('/yay')

def is_valid_number(number):
    account_sid = get_credentials()[0]
    auth_token = get_credentials()[1]
    client = TwilioLookupsClient(account_sid, auth_token)
    try:
        response = client.phone_numbers.get(number, include_carrier_info=True)
        response.phone_number  # If invalid, throws an exception.
        return True
    except TwilioRestException as e:
        if e.code == 20404:
            return False
        else:
            raise e

def get_credentials():
    if 'ACCOUNT_SID' in os.environ:
        account_sid = os.environ['ACCOUNT_SID']
    else:
        with open('twilio_auth.txt') as f:
            lines = f.read().splitlines() 
        account_sid = lines[0]
            
    if 'AUTH_TOKEN' in os.environ:
        auth_token = os.environ['AUTH_TOKEN']
    else:
        with open('twilio_auth.txt') as f:
            lines = f.read().splitlines() 
        auth_token = lines[1]

    return [account_sid, auth_token]

@app.route('/yay')
def yay():
    return render_template('yay.html')

@app.route('/ohno')
def ohno():
    return render_template('ohno.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')