from flask import Flask, render_template
from flask import send_from_directory
import os
import pickle
from dotenv import load_dotenv
import json
import sqlite3
from flask import Flask, redirect, request, url_for
from oauthlib.oauth2 import WebApplicationClient
import requests
load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


app = Flask(__name__)

#init sqlite3
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    profile_pic TEXT
)
''')
conn.commit()

client = WebApplicationClient(GOOGLE_CLIENT_ID)


@app.route('/')
def home():
    image_folder = 'pics'
    # images = os.listdir(image_folder)
    f = open("captions.pkl", "rb")
    caption_dict = pickle.load(f)

    return render_template('index.html', images=caption_dict)

# host files in good pics directory
@app.route('/pics/<path:filename>')
def good_pics(filename):
    print(f"Serving file: {filename}")
    return send_from_directory('Downloads', filename)

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri="https://127.0.0.1:5000/login/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (and it's authenticated), let's find and return
    # user's profile information from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]

        # Create a new user or update existing user's info in the database
        c.execute('''
            INSERT OR REPLACE INTO users (email, name, profile_pic)
            VALUES (?, ?, ?)
        ''', (users_email, users_name, picture))
        conn.commit()

        return redirect("/")
    
    return "User email not available or not verified by Google.", 400

if __name__ == '__main__':
    app.run(debug=True)