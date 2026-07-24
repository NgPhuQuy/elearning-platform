import os

import cloudinary
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = "KNJBJku f<j ]f2;w]r[jnofpmc,snKZD l12sa,lm2njwqd"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
cloudinary.config(cloud_name='dtvg4cpoq',
                  api_key='211564137488191',
                  api_secret='otiD0T9BFzzg9UyKGcTb6MHi3Ow')

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

db = SQLAlchemy(app)

login = LoginManager(app)

oauth = OAuth(app)

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_DISCOVERY_URL,
    client_kwargs={"scope": "openid email profile"},
)