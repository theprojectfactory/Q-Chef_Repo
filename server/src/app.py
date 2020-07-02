################################################################################
# Q-Chef Server
# Authors: Q-Chef Backend Programmers
# Updated: 20200621

################################################################################
# Imports and Server Initialisation
################################################################################
import os
import json

import firebase_admin
from firebase_admin import credentials, firestore

# Use the application default credentials
cred = credentials.Certificate("./keyKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

from flask import Flask
app = Flask(__name__)
config = {}
with open("./config.json", 'r') as f:
  config = json.loads(f.read())

from routes import *

if __name__ == "__main__":
  app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))