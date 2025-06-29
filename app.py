# --- START OF FILE app.py ---
import eventlet
eventlet.monkey_patch()



from flask import Flask, jsonify
from flask_cors import CORS
from auth import auth_bp
from chat import socketio
from db import messages_collection
from bson import json_util
import json

# Create and configure the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key!'  # Change this in production
CORS(app, resources={r"/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(auth_bp)


@app.route('/messages', methods=['GET'])
def get_messages():
    """
    Fetches all historical chat messages from the database, sorted by timestamp.
    """
    # Fetch messages and sort by timestamp in ascending order
    messages = list(messages_collection.find({}).sort("timestamp", 1))

    # Use bson.json_util to handle MongoDB-specific types like ObjectId
    # This prevents serialization errors and correctly formats the data
    return json.loads(json_util.dumps(messages))


if __name__ == "__main__":
    import eventlet
    import eventlet.wsgi
    socketio.init_app(app, cors_allowed_origins="*")
    socketio.run(app, host='0.0.0.0', port=10000)
