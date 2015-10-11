from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.tools import run_flow, argparser
import urllib2
import urllib
import pytz

import datetime
import uuid

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import flask
from flask import Flask, render_template, json, request, redirect

import base64
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

    print(d)
    
    f = {'key' : 'AIzaSyCMCTCPE4Rjla4uUs4vrO1nyQVa0Xu5XAc',
    'maxResults' : '50',
    'orderBy' : 'startTime',
    'singleEvents' : 'true',
    'timeMin' : d}

    flags = urllib.urlencode(f)

    url = "https://www.googleapis.com/calendar/v3/calendars/jamesxue100@gmail.com/events?" + flags

    content = urllib2.urlopen(url).read()
    
    content = json.loads(content)

    # print(content)

    # if 'credentials' not in flask.session:
    #     return flask.redirect(flask.url_for('oauth2callback'))
    # credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
    # if credentials.access_token_expired:
    #     return flask.redirect(flask.url_for('oauth2callback'))
    # else:
    #     http = credentials.authorize(httplib2.Http())
    #     service = discovery.build('calendar', 'v3', http=http)

    # credentials = get_credentials()
    # http = credentials.authorize(httplib2.Http())
    # service = discovery.build('calendar', 'v3', http=http)

    # now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    # print('Getting the upcoming 20 events')
    # eventsResult = service.events().list(
    #     calendarId='primary', timeMin=now, maxResults=20, singleEvents=True,
    #     orderBy='startTime').execute()

    # print(eventsResult)

    # events = eventsResult.get('items', [])

    events = content['items'][:40]

    if not events:
        print('No upcoming events found.')

    latest_time = strftime('%I:%M %p')
    latest_date = strftime("%a %m/%d/%y")
    return_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start = dateutil.parser.parse(start)
        start_time = start.strftime('%I:%M %p')
        start_date = start.strftime("%a %m/%d/%y")
        end = dateutil.parser.parse(end)
        end_time = end.strftime('%I:%M %p')
        end_date = end.strftime("%a %m/%d/%y")

        if (start_time > latest_time):
            return_list.append([latest_time, latest_date, start_time, start_date])
        latest_time = end_time
        latest_date = end_date

    print(return_list)
    return render_template('index.html', api_data=return_list)

# def get_credentials():
#     home_dir = os.path.expanduser('~')
#     credential_dir = os.path.join(home_dir, '.credentials')
#     if not os.path.exists(credential_dir):
#         os.makedirs(credential_dir)
#     credential_path = os.path.join(credential_dir,
#                                    'calendar-python-quickstart.json')

#     store = oauth2client.file.Storage(credential_path)
#     credentials = store.get()
#     if not credentials or credentials.invalid:
#         flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
#         flow.user_agent = APPLICATION_NAME
#         if flags:
#             credentials = tools.run_flow(flow, store, flags)
#         else: # Needed only for compatability with Python 2.6
#             credentials = tools.run(flow, store)
#         print('Storing credentials to ' + credential_path)
#     return credentials


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
    email = request.form['email']
    location = request.form['location']
    time = request.form['time']

    print(name, email, location, time)


    me = "bobawithjames@gmail.com"
    you = email

    to = [you, 'jamesxue100@gmail.com']
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "You're getting boba with James!"
    msg['From'] = me
    msg['To'] = you
    msg['Cc'] = 'jamesxue100@gmail.com'

    html = '<html><head></head><body><p>Hi there '+name+'!<br>You are scheduled for boba at '+location+' at '+time+'.<br>If you have any questions, email James (cced on this email), text James at (949)554-5535 or message him on <a href="https://www.facebook.com/jamesxue100">Facebook</a>.</p></body</html>'

    part2 = MIMEText(html, 'html')

    msg.attach(part2)

    s = smtplib.SMTP(host='smtp.gmail.com', port=587)
    s.ehlo()
    s.starttls()
    s.ehlo()
    username = "bobawithjames@gmail.com"
    password = "bobawithjames123"
    s.login(username, password)
    s.sendmail(me, to, msg.as_string())
    s.quit()

    return redirect('/yay')

@app.route('/yay')
def yay():
    return render_template('yay.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')