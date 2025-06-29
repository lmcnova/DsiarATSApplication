# --- START OF FILE app.py ---

import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO # <-- Import SocketIO directly here
from bson import json_util
import json
import os

# --- 1. App and SocketIO Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-fallback-secret-key!')
CORS(app, resources={r"/*": {"origins": "*"}})

# Create the SocketIO server, linking it with the Flask app.
# async_mode='eventlet' is crucial for Gunicorn to work correctly.
# From this point on, 'socketio' is a callable WSGI application.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


# --- 2. Import and Register Blueprints and Handlers ---
from auth import auth_bp
from chat import register_handlers as register_chat_handlers
from db import messages_collection

app.register_blueprint(auth_bp)
register_chat_handlers(socketio) # Call the function from chat.py to set up handlers


# --- 3. Define Main Routes ---
@app.route('/messages', methods=['GET'])
def get_messages():
    """
    Fetches all historical chat messages from the database, sorted by timestamp.
    """
    messages = list(messages_collection.find({}).sort("timestamp", 1))
    return json.loads(json_util.dumps(messages))

# Note: The if __name__ == "__main__" block can now be removed or kept in wsgi.py
# for local testing. Gunicorn will not use it.
