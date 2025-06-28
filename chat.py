# --- START OF FILE chat.py ---


from flask_socketio import SocketIO, emit
from db import messages_collection
from datetime import datetime

# Initialize SocketIO
socketio = SocketIO(async_mode='gevent', cors_allowed_origins="*")


@socketio.on('connect')
def handle_connect():
    """Handles a client connecting to the WebSocket."""
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Handles a client disconnecting from the WebSocket."""
    print('Client disconnected')


@socketio.on('send_message')
def handle_message(data):
    """
    Listens for 'send_message' events, saves the message to the DB,
    and broadcasts it to all clients.
    """
    message = {
        "username": data['username'],
        "text": data['text'],
        "timestamp": datetime.utcnow().isoformat() + "Z"  # Use UTC for consistency
    }

    # Insert the message into the database.
    # This action adds an `_id` field of type ObjectId to the `message` dict.
    messages_collection.insert_one(message)

    # *** THE FIX IS HERE ***
    # Convert the ObjectId to a string before emitting.
    # The `_id` is a special BSON type that is not directly JSON serializable.
    message['_id'] = str(message['_id'])

    # Now the message dictionary is safe to be sent as JSON, and the frontend
    # will receive a unique ID for the new message.
    emit('receive_message', message, broadcast=True)
