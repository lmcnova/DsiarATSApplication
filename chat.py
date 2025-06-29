# --- START OF FILE chat.py ---

# DO NOT create the SocketIO instance here anymore.
# We will pass it in from app.py
from flask_socketio import emit, join_room, leave_room
from flask import request
from db import messages_collection
from datetime import datetime
import logging

# Store connected users
connected_users = {}

# This function will be imported by app.py to register all event handlers
def register_handlers(socketio):

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
        # ... (rest of the function is the same)
        username_to_remove = None
        for username, user_sid in connected_users.items():
            if user_sid == sid:
                username_to_remove = username
                break

        if username_to_remove:
            del connected_users[username_to_remove]
            emit('user_left', {'username': username_to_remove}, broadcast=True)

    # --- WRAP ALL YOUR OTHER @socketio.on DECORATORS INSIDE THIS FUNCTION ---
    # For example:

    @socketio.on('join')
    def handle_join(data):
        """Handle user joining the chat."""
        username = data.get('username')
        if username:
            connected_users[username] = request.sid
            join_room('chat_room')
            print(f'User {username} joined the chat')
            emit('user_joined', {'username': username, 'message': f'{username} joined the chat'}, room='chat_room', include_self=False)
            emit('join_confirmation', {'status': 'success', 'message': 'Successfully joined the chat'})

    # ... and so on for handle_leave, handle_message, handle_get_history, etc.
    # Just indent all of them one level to be inside the register_handlers function.

    @socketio.on('leave')
    def handle_leave(data):
        username = data.get('username')
        if username and username in connected_users:
            leave_room('chat_room')
            del connected_users[username]
            print(f'User {username} left the chat')
            emit('user_left', {'username': username, 'message': f'{username} left the chat'}, room='chat_room')


    @socketio.on('send_message')
    def handle_message(data, callback=None):
        try:
            if not data.get('username') or not data.get('text'):
                error_response = {'success': False, 'error': 'Missing username or text'}
                if callback: callback(error_response)
                return
            message = {
                "id": data.get('id'),
                "username": data['username'],
                "text": data['text'].strip(),
                "timestamp": data.get('timestamp', datetime.utcnow().isoformat() + "Z")
            }
            result = messages_collection.insert_one(message.copy())
            message['_id'] = str(result.inserted_id)
            print(f'Message saved to DB with ID: {message["_id"]}')
            if callback:
                callback({'success': True, 'messageId': message.get('id'), 'dbId': message['_id'], 'timestamp': message['timestamp']})
            emit('receive_message', {'id': message.get('id'), 'username': message['username'], 'text': message['text'], 'timestamp': message['timestamp'], '_id': message['_id']}, room='chat_room', broadcast=True)
            socketio.sleep(0.1)
            emit('message_delivered', {'messageId': message.get('id'), 'status': 'delivered'}, room=connected_users.get(message['username']))
            print(f'Message from {message["username"]}: {message["text"]}')
        except Exception as e:
            print(f'Error handling message: {e}')
            if callback: callback({'success': False, 'error': 'Server error'})


    @socketio.on('get_message_history')
    def handle_get_history(data):
        # ... (your implementation)
        try:
            limit = data.get('limit', 50)
            messages = list(messages_collection.find().sort('timestamp', -1).limit(limit))
            formatted_messages = []
            for msg in reversed(messages):
                msg['_id'] = str(msg['_id'])
                formatted_messages.append(msg)
            print(f'Sent {len(formatted_messages)} historical messages')
            return {'success': True, 'messages': formatted_messages, 'count': len(formatted_messages)}
        except Exception as e:
            print(f'Error getting message history: {e}')
            return {'success': False, 'error': 'Failed to get message history'}

    # ... include ALL your @socketio.on handlers here, indented
