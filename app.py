import json
from flask import Flask, jsonify, make_response, redirect,render_template, url_for,request
from flask import session as login_session
from flask_cors import CORS, cross_origin 
import requests
import random
import string
from credentials import client_id, client_secret # credentials.py has the client_id and client_secret

app = Flask(__name__)
CORS(app) #allows CORS on all routes

authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
request_url = 'https://api.github.com'


@app.route('/')
def showLogin():
  state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
  login_session['state'] = state
  # return jsonify(state=state) # to return state in a json response
  return jsonify({"state":state})


@app.route('/handleLogin', methods=["GET"])
def handleLogin():
    if login_session['state'] == request.args.get('state'):
        #print login_session['state']
        fetch_url = authorization_base_url + \
                    '?client_id=' + client_id + \
                    '&state=' + login_session['state'] + \
                    '&scope=user%20repo%20public_repo' + \
                    '&allow_signup=true'
        #print fetch_url
        return redirect(fetch_url)
    else:
        return jsonify(invalid_state_token="invalid_state_token")

@app.route('/callback', methods=['GET', 'POST'])
def handle_callback():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter!'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if 'code' in request.args:
        #return jsonify(code=request.args.get('code'))
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': request.args['code']
        }
        headers = {'Accept': 'application/json'}
        req = requests.post(token_url, params=payload, headers=headers)
        resp = req.json()

        if 'access_token' in resp:
            login_session['access_token'] = resp['access_token']
            return jsonify(access_token=resp['access_token'])
            #return redirect(url_for('index'))
        else:
            return jsonify(error="Error retrieving access_token"), 404
    else:
        return jsonify(error="404_no_code"), 404

@app.route('/index')
def index():
    # Check for access_token in session
    if 'access_token' not in login_session:
        return 'Never trust strangers', 404
    # Get user information from github api
    access_token_url = 'https://api.github.com/user?access_token={}'
    r = requests.get(access_token_url.format(login_session['access_token']))
    try:
        resp = r.json()
        gh_profile = resp['html_url'] 
        username = resp['login']
        avatar_url = resp['avatar_url']
        bio = resp['bio']
        name = resp['name']
        return jsonify(
          gh_profile=gh_profile,
          gh_username=username,
          avatar_url=avatar_url,
          gh_bio=bio,
          name=name
        )
    except AttributeError:
        app.logger.debug('error getting username from github, whoops')
        return "I don't know who you are; I should, but regretfully I don't", 500

if __name__ == "__main__":
    app.secret_key = "fart_fart"
    app.debug = True
    app.run('0.0.0.0',port=5000)