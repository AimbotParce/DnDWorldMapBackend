import secrets

import flask
from flask_cors import CORS
from flask_socketio import SocketIO

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_urlsafe(16)
CORS(app)
socketio = SocketIO(app)

app.config["DM_PASSWORD"] = open("admin.key").read().strip()
app.config["WORLD"] = None
