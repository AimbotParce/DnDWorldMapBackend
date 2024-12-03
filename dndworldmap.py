import argparse

parser = argparse.ArgumentParser(description="Serve")
parser.add_argument("--port", type=int, default=8000, help="The port to serve the app on")
args = parser.parse_args()

from api.app import app, socketio
from api.endpoints import *

socketio.run(app, port=args.port, debug=True)
