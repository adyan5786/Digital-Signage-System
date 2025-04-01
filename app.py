import os
import secrets
import logging
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Secure random secret key for session management
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# SocketIO setup with CORS support
allowed_origins = ["https://digital-signage-system.onrender.com", "http://localhost:5000"]
socketio = SocketIO(app, ping_timeout=120, ping_interval=25, cors_allowed_origins=allowed_origins)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Secure session settings
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Track logged-in users
logged_in_users = {}

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clear uploads on login
def clear_uploads_on_login():
    """Delete all files in uploads folder when called."""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

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
        logger.info(f"Login attempt for user: {username}")

        env_username = os.getenv("ADMIN_USERNAME")
        env_password = os.getenv("ADMIN_PASSWORD")

        if username == env_username and password == env_password:
            clear_uploads_on_login()
            session["user"] = username
            logged_in_users[username] = True
            socketio.emit("user_logged_in", {}, room="page2_users")
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for("editor"))
        else:
            logger.warning(f"Failed login attempt for user: {username}")

    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    username = session.get("user")
    if username:
        logged_in_users.pop(username, None)
        logger.info(f"User {username} logged out")

    session.clear()

    # Notify all TV displays that the user logged out
    socketio.emit("user_logged_out", {}, room="page2_users")

    return redirect(url_for("login"))

# Editor Page (Protected)
@app.route("/editor")
def editor():
    if "user" not in session or session.get("user") is None:
        logger.warning("Unauthorized access to editor page")
        return redirect(url_for("login"))

    # Notify all connected display screens that a user is logged in
    socketio.emit("user_logged_in", {}, room="page2_users")
    logger.info("User accessed the editor page")

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
        logger.info("New connection to page2_users room")

        # Send login status when a new display connects
        is_logged_in = any(logged_in_users.values())
        emit("check_login_status", {"logged_in": is_logged_in})
    else:
        join_room("page1_users")
        logger.info("New connection to page1_users room")

@socketio.on("send_text")
def handle_text(data):
    socketio.emit("update_content", {"type": "text", "message": data["message"], "align": data.get("align", "left")}, room="page2_users")
    logger.info(f"Text message sent: {data['message']}")

@socketio.on("clear_display")
def handle_clear_display():
    socketio.emit("clear_display", {}, room="page2_users")
    logger.info("Clear display signal sent")

@socketio.on("check_login_status")
def check_login_status(data=None):
    """Check if any user is logged in when a new tab connects."""
    is_logged_in = any(logged_in_users.values())
    emit("check_login_status", {"logged_in": is_logged_in}, to=request.sid)
    logger.info("Checked login status")

@socketio.on("disconnect")
def handle_disconnect():
    logger.info("Client disconnected")

@socketio.on("video_control")
def handle_video_control(data):
    socketio.emit("video_control", data, room="page2_users")
    logger.info(f"Video control signal sent: {data}")

@socketio.on("autoplay_blocked")
def handle_autoplay_blocked():
    socketio.emit("autoplay_blocked", room="page1_users")
    logger.info("Autoplay blocked signal sent")

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        logger.warning("No file uploaded")
        return "No file uploaded", 400

    file = request.files["file"]
    if file.filename == "":
        logger.warning("No selected file")
        return "No selected file", 400

    if not allowed_file(file.filename):
        logger.warning("Invalid file type uploaded")
        return "Invalid file type", 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)
    logger.info(f"File uploaded: {filename}")

    file_url = f"/uploads/{filename}"
    file_type = "image" if file.content_type.startswith("image") else "video"

    socketio.emit("update_content", {"type": file_type, "file_url": file_url}, room="page2_users")

    return "File uploaded successfully", 200

if __name__ == "__main__":
    # Disable debug mode for production
    socketio.run(app, debug=False)