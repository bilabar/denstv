from flask import Flask
from requests import Request, Session, codes
from http.cookiejar import LWPCookieJar
from datetime import date, datetime
from os.path import isfile
import json
import sqlite3

cj = LWPCookieJar('cookies.txt')

# Load existing cookies (file might not yet exist)
try:
	cj.load()
except:
	pass

s = Session()
s.cookies = cj
s.headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
	'Host': 'www.dens.tv',
	'Accept': 'application/json, text/javascript, */*; q=0.01',
	'X-Requested-With': 'XMLHttpRequest',
	'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
	'Origin': 'https://www.dens.tv',
	'Referer': 'https://www.dens.tv/channels?watch',
	'Accept-Encoding': 'gzip, deflate',
	'Accept-Language': 'en-US,en;q=0.9',
	'Connection': 'keep-alive'
}

app = Flask(__name__)

base_uri = 'https://www.dens.tv'

def save_json(filename, r):
	with open(filename, 'w') as f:
		f.write(json.dumps(r))

def read_json(filename):
	with open(filename, 'r') as f:
		content = f.read()
		if len(content):
			return json.loads(content)

def request_channels(id_category):
	payload = {'listing': 1}
	url = '%s/tvpage_octo/channelgen/%s' % (base_uri, id_category)
	req = Request('POST',  url, data=payload)
	prepped = s.prepare_request(req)
	res = s.send(prepped)
	cj.save(ignore_discard=True)
	return res

def request_player_live(id_channels):
	payload = {'listing': 1}
	url = '%s/tvpage_octo/player_tv/1/%s' % (base_uri, id_channels)
	req = Request('POST',  url, data=payload)
	prepped = s.prepare_request(req)
	res = s.send(prepped)
	cj.save(ignore_discard=True)
	return res

def request_player_catchup(id_catchup):
	url = "%s/tvpage_octo/player_catchup_v2/%s" % (base_uri, id_catchup)
	req = Request('GET',  url)
	prepped = s.prepare_request(req)
	del prepped.headers['Content-Type']
	del prepped.headers['Origin']
	del prepped.headers['X-Requested-With']
	res = s.send(prepped)
	cj.save(ignore_discard=True)
	return res

def request_epg(id_channels, date=0):
	url = "%s/tvpage_octo/epgchannel2/%s/%s" % (base_uri, date, id_channels)
	payload = {'listing': 1}
	req = Request('POST',  url, data=payload)
	prepped = s.prepare_request(req)
	res = s.send(prepped)
	cj.save(ignore_discard=True)
	return res


@app.route('/')
def home():
	return 'Hello World!'

@app.route("/channels/")
@app.route("/channels/<int:id_category>")
def all_channels(id_category=1):
	filename = 'channels-%s.json' % id_category
	if not isfile(filename):
		r = request_channels(id_category)
		if r.status_code == codes.ok and not "PHP Error" in r.text and len(r.json()['data']):
			save_json(filename, r.json())
			return r.json()
		else:
			return 'Try again.'
	else:
		return read_json(filename)


@app.route('/live/<int:id_channels>')
def player_live(id_channels):
	filename = 'live-%s.json' % (id_channels)
	if not isfile(filename):
		r = request_player_live(id_channels)
		if r.status_code == codes.ok and not "PHP Error" in r.text:
			save_json(filename, r.json())
			return r.json()
		else:
			return 'Try again.'
	else:
		return read_json(filename)


@app.route('/catchup/<int:id_catchup>')
def player_catchup(id_catchup):
	filename = 'catchup-%s.json' % (id_catchup)
	if not isfile(filename):
		r = request_player_catchup(id_catchup)
		if r.status_code == codes.ok and not "PHP Error" in r.text and len(r.json()['data']):
			save_json(filename, r.json())
			return r.json()
		else:
			return 'Try again.'		
	else:
		return read_json(filename)


@app.route('/epg/live/<int:id_channels>')
def epg_live(id_channels):
	filename = 'epg %s %s.json' % (str(date.today()), id_channels)
	if not isfile(filename):
		r = request_epg(id_channels)
		if r.status_code == codes.ok and not "PHP Error" in r.text and len(r.json()['data']):
			save_json(filename, r.json())
			return r.json()
		else:
			return 'Try again.'		
	else:
		return read_json(filename)


@app.route('/epg/catchup/<dates>/<int:id_channels>')
def epg_catchup(id_channels, dates):
	if len(dates) != 10 or len(dates.split('-')) != 3:
		return 'Date format: YYYY-MM-DD'
	try:
		datetime.strptime(dates, '%Y-%m-%d')
	except Exception as e:
		raise e
	filename = 'epg %s %s.json' % (dates, id_channels)
	if not isfile(filename):
		r = request_epg(id_channels, dates)
		if r.status_code == codes.ok and not "PHP Error" in r.text and len(r.json()['data']):
			save_json(filename, r.json())
			return r.json()
		else:
			return 'Try again.'		
	else:
		return read_json(filename)

