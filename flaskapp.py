from flask import Flask, render_template
from flask import send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

import os
import pickle
from dotenv import load_dotenv
import json
import sqlite3
from flask import Flask, redirect, request, url_for
from oauthlib.oauth2 import WebApplicationClient
import requests
from flask import jsonify
load_dotenv()

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

class User(UserMixin):
    def __init__(self, id, email, name, profile_pic):
        self.id = id
        self.email = email
        self.name = name
        self.profile_pic = profile_pic 


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key_here")

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db', check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user_data = c.fetchone()
    conn.close()

    if user_data:
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        print(f"Loaded user: {user.name} with ID: {user.id}")

        return user
    return None


#init sqlite3
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    profile_pic TEXT,
    voted INTEGER DEFAULT 0,
    voted_images TEXT DEFAULT ''
)
''')
conn.commit()

client = WebApplicationClient(GOOGLE_CLIENT_ID)

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

@app.route('/getvotes')
def get_votes():
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    id = current_user.id
    c.execute("SELECT voted_images FROM users WHERE id=?", (id,))
    votes_images = c.fetchone()[0]
    
    votes = json.loads(votes_images) if votes_images else []
    return jsonify({"votes": votes})

@app.route("/vote", methods=['POST'])
@login_required
def post_votes():
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401

    votes = request.json.get('votes', [])
    if not votes:
        return jsonify({"error": "No votes provided"}), 400

    print(f"Votes received: {votes}")

    # Update the user's voted status and voted images
    c.execute('''
        UPDATE users
        SET voted = 1,
            voted_images = ?
        WHERE id = ?
    ''', (json.dumps(votes), current_user.id))
    conn.commit()

    current_user.voted = 1
    current_user.voted_images = json.dumps(votes)

    return jsonify({"message": "Votes updated successfully", "votes": votes})

@app.route('/')
def home():
    if not current_user.is_authenticated:
        return render_template('login.html')
    image_folder = 'pics'
    # images = os.listdir(image_folder)
    f = open("captions.pkl", "rb")
    caption_dict = pickle.load(f)
    id = current_user.id
    c.execute("SELECT voted_images FROM users WHERE id=?", (id,))
    votes_images = c.fetchone()[0]
    votes = json.loads(votes_images) if votes_images else []
    for item in caption_dict:
        if item[0] in votes:
            item.append("voted")
        else:
            item.append("not-voted")
    print(caption_dict)

    # shuffle caption_dict
    import random
    random.shuffle(caption_dict)
    f.close()
    return render_template('index.html', images=caption_dict, profile_pic=current_user.profile_pic, name=current_user.name, email=current_user.email)

# host files in good pics directory
@app.route('/pics/<path:filename>')
def good_pics(filename):
    filename=filename.replace("heic", "jpg")
    filename=filename.replace("HEIC", "jpg")
    print(f"Serving file: {filename}")
    return send_from_directory('Downloads', filename)

@app.route('/checklogin')
def checklogin():
    if current_user.is_authenticated:
        return "User is logged in"
    else:
        return "User is not logged in"

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri="https://39b8a66e4b9b.ngrok-free.app/login/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    print(f"Authorization code: {code}")
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
            INSERT OR REPLACE INTO users (id, email, name, profile_pic)
            VALUES (?, ?, ?, ?)
        ''', (unique_id, users_email, users_name, picture))
        conn.commit()

        user = User(unique_id, users_email, users_name, picture)
        login_user(user)

        return redirect("/")
    
    return "User email not available or not verified by Google.", 400

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    votes = request.json.get('votes', [])
    if not votes:
        return "No votes provided", 400

    if_already_voted = current_user.voted
    if if_already_voted:
        votes = json.loads(current_user.voted_images)
        return jsonify({"message": "You have already voted", "votes": votes})

    
    # Update the user's voted status and voted images
    c.execute('''
        UPDATE users
        SET voted = 1,
            voted_images = ?
        WHERE id = ?
    ''', (json.dumps(votes), current_user.id))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True,ssl_context="adhoc")  # Use adhoc for self-signed SSL certificate