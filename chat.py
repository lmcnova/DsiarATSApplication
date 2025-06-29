from flask_socketio import SocketIO, emit, join_room, leave_room
from db import messages_collection
from datetime import datetime
import logging

# Initialize SocketIO with CORS support
# socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True)

# Store connected users
connected_users = {}


@socketio.on('connect')
def handle_connect():
    """Handles a client connecting to the WebSocket."""
    print(f'Client connected: {request.sid}')
    emit('connection_status', {'status': 'connected', 'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handles a client disconnecting from the WebSocket."""
    sid = request.sid
    print(f'Client disconnected: {sid}')

    # Remove user from connected users if they were registered
    username_to_remove = None
    for username, user_sid in connected_users.items():
        if user_sid == sid:
            username_to_remove = username
            break

    if username_to_remove:
        del connected_users[username_to_remove]
        emit('user_left', {'username': username_to_remove}, broadcast=True)


@socketio.on('join')
def handle_join(data):
    """Handle user joining the chat."""
    username = data.get('username')
    if username:
        connected_users[username] = request.sid
        join_room('chat_room')  # Join a common room
        print(f'User {username} joined the chat')

        # Notify other users
        emit('user_joined', {
            'username': username,
            'message': f'{username} joined the chat'
        }, room='chat_room', include_self=False)

        # Send confirmation to the user
        emit('join_confirmation', {
            'status': 'success',
            'message': 'Successfully joined the chat'
        })


@socketio.on('leave')
def handle_leave(data):
    """Handle user leaving the chat."""
    username = data.get('username')
    if username and username in connected_users:
        leave_room('chat_room')
        del connected_users[username]
        print(f'User {username} left the chat')

        # Notify other users
        emit('user_left', {
            'username': username,
            'message': f'{username} left the chat'
        }, room='chat_room')


@socketio.on('send_message')
def handle_message(data, callback=None):
    """
    Listens for 'send_message' events, saves the message to the DB,
    and broadcasts it to all clients with acknowledgment support.
    """
    try:
        # Validate required fields
        if not data.get('username') or not data.get('text'):
            error_response = {'success': False, 'error': 'Missing username or text'}
            if callback:
                callback(error_response)
            return

        # Create message object
        message = {
            "id": data.get('id'),  # Client-generated ID for tracking
            "username": data['username'],
            "text": data['text'].strip(),
            "timestamp": data.get('timestamp', datetime.utcnow().isoformat() + "Z")
        }

        # Insert the message into the database
        try:
            result = messages_collection.insert_one(message.copy())
            message['_id'] = str(result.inserted_id)
            print(f'Message saved to DB with ID: {message["_id"]}')
        except Exception as db_error:
            print(f'Database error: {db_error}')
            error_response = {'success': False, 'error': 'Database error'}
            if callback:
                callback(error_response)
            return

        # Send acknowledgment to sender
        if callback:
            callback({
                'success': True,
                'messageId': message.get('id'),
                'dbId': message['_id'],
                'timestamp': message['timestamp']
            })

        # Broadcast message to all clients (including sender for consistency)
        emit('receive_message', {
            'id': message.get('id'),
            'username': message['username'],
            'text': message['text'],
            'timestamp': message['timestamp'],
            '_id': message['_id']
        }, room='chat_room', broadcast=True)

        # Optional: Send delivery confirmation after a short delay
        # This simulates message delivery confirmation
        socketio.sleep(0.1)  # Small delay to simulate network
        emit('message_delivered', {
            'messageId': message.get('id'),
            'status': 'delivered'
        }, room=connected_users.get(message['username']))

        print(f'Message from {message["username"]}: {message["text"]}')

    except Exception as e:
        print(f'Error handling message: {e}')
        error_response = {'success': False, 'error': 'Server error'}
        if callback:
            callback(error_response)


@socketio.on('get_message_history')
def handle_get_history(data):
    def callback(response_data):
        return response_data

    try:
        limit = data.get('limit', 50)

        messages = list(messages_collection.find().sort('timestamp', -1).limit(limit))

        formatted_messages = []
        for msg in reversed(messages):
            msg['_id'] = str(msg['_id'])
            formatted_messages.append(msg)

        print(f'Sent {len(formatted_messages)} historical messages')

        return {
            'success': True,
            'messages': formatted_messages,
            'count': len(formatted_messages)
        }

    except Exception as e:
        print(f'Error getting message history: {e}')
        return {'success': False, 'error': 'Failed to get message history'}



@socketio.on('typing_start')
def handle_typing_start(data):
    """Handle typing indicator start."""
    username = data.get('username')
    if username:
        emit('user_typing', {
            'username': username,
            'typing': True
        }, room='chat_room', include_self=False)


@socketio.on('typing_stop')
def handle_typing_stop(data):
    """Handle typing indicator stop."""
    username = data.get('username')
    if username:
        emit('user_typing', {
            'username': username,
            'typing': False
        }, room='chat_room', include_self=False)


@socketio.on('ping')
def handle_ping(data, callback=None):
    """Handle ping for connection testing."""
    if callback:
        callback({'pong': True, 'timestamp': datetime.utcnow().isoformat() + "Z"})


# Error handler
@socketio.on_error_default
def default_error_handler(e):
    """Default error handler for SocketIO events."""
    print(f'SocketIO Error: {e}')
    emit('error', {'message': 'An error occurred', 'details': str(e)})


# Import request object if needed for session ID
from flask import request

