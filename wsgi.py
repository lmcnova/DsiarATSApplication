from app import app, socketio

# The Gunicorn command will point to this file and use the 'socketio' object.
# The socketio object will manage both standard HTTP and WebSocket traffic.

if __name__ == "__main__":
    # This allows you to run the app locally for testing with 'python wsgi.py'
    # It's more representative of the production setup than running app.py directly.
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
