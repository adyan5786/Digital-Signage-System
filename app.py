import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Secure random secret key for session management
app.secret_key = secrets.token_hex(32)

# SocketIO setup with CORS support
socketio = SocketIO(app, ping_timeout=120, ping_interval=25, cors_allowed_origins="*")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Secure session settings
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Track logged-in users (Key: user_id, Value: boolean)
logged_in_users = {}

# Clear uploads on login
def clear_uploads_on_login():
    """Delete all files in uploads folder when called."""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "mkv", "quicktime"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Prevent caching of secure pages
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

# Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "password":
            clear_uploads_on_login()  # <- Clear uploads on successful login
            session["user"] = username
            logged_in_users[username] = True
            socketio.emit("user_logged_in", {}, room="page2_users")
            return redirect(url_for("editor"))

    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    username = session.get("user")
    if username:
        logged_in_users.pop(username, None)  # Remove from tracking

    session.clear()  # Clears session data

    # Notify all TV displays that the user logged out
    socketio.emit("user_logged_out", {}, room="page2_users")

    return redirect(url_for("login"))

# Editor Page (Protected)
@app.route("/editor")
def editor():
    if "user" not in session or session.get("user") is None:
        return redirect(url_for("login"))  

    # Notify all connected display screens that a user is logged in
    socketio.emit("user_logged_in", {}, room="page2_users")

    return render_template("page1.html")

# TV Display Page
@app.route("/other")
def page2():
    return render_template("page2.html")

# File Uploads
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@socketio.on("connect")
def on_connect():
    referer = request.headers.get("Referer", "")
    if "other" in referer:
        join_room("page2_users")

        # Send login status when a new display connects
        is_logged_in = any(logged_in_users.values())  # If any user is logged in
        emit("check_login_status", {"logged_in": is_logged_in})
    else:
        join_room("page1_users")

@socketio.on("send_text")
def handle_text(data):
    socketio.emit(
        "update_content", 
        {
            "type": "text", 
            "message": data["message"], 
            "align": data.get("align", "left"),
            "animation": data.get("animation", "fade")  # Include animation type
        }, 
        room="page2_users"
    )
    
@socketio.on("clear_display")
def handle_clear_display():
    socketio.emit("clear_display", {}, room="page2_users")

@socketio.on("check_login_status")
def check_login_status(data=None):
    """Check if any user is logged in when a new tab connects."""
    is_logged_in = any(logged_in_users.values())  # Check if any user is logged in
    emit("check_login_status", {"logged_in": is_logged_in}, to=request.sid)  

@socketio.on("disconnect")
def handle_disconnect():
    pass

@socketio.on("video_control")
def handle_video_control(data):
    socketio.emit("video_control", data, room="page2_users")

@socketio.on("autoplay_blocked")
def handle_autoplay_blocked():
    socketio.emit("autoplay_blocked", room="page1_users")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400

    if not allowed_file(file.filename):
        return "Invalid file type", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    file_url = f"/uploads/{filename}"
    file_type = "image" if file.content_type.startswith("image") else "video"

    socketio.emit("update_content", {"type": file_type, "file_url": file_url}, room="page2_users")

    return "File uploaded successfully", 200

if __name__ == "__main__":
    socketio.run(app, debug=True)