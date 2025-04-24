import os
import secrets
import logging
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_socketio import SocketIO, emit, join_room
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Secure secret key for session management
socketio = SocketIO(app, ping_timeout=120, ping_interval=25, cors_allowed_origins="*")

# Configuration for file uploads and session security
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logged_in_users = {}  # Tracks active user sessions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "mkv", "quicktime"}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_uploads_on_login():
    """Clear uploads directory when a new user logs in"""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                logging.info(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            logging.error(f"Error deleting {file_path}: {e}")

@app.after_request
def add_header(response):
    """Prevent caching of responses"""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
def login():
    """Handle user login with hardcoded credentials"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        logging.info(f"Login attempted with username: {username}")

        if username == "RizviSignage" and password == "CodeLike":
            clear_uploads_on_login()
            session["user"] = username
            logged_in_users[username] = True
            logging.info(f"User logged in: {username}")
            socketio.emit("user_logged_in", {}, room="page2_users")
            return redirect(url_for("editor"))
        
        return redirect(url_for("login", error=True))

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Handle user logout and clear session"""
    username = session.get("user")
    if username:
        logged_in_users.pop(username, None)
        logging.info(f"User logged out: {username}")

    session.clear()
    socketio.emit("user_logged_out", {}, room="page2_users")
    return redirect(url_for("login"))

@app.route("/editor")
def editor():
    """Editor page - requires authentication"""
    if "user" not in session or session.get("user") is None:
        return redirect(url_for("login"))  
    
    socketio.emit("user_logged_in", {}, room="page2_users")
    return render_template("page1.html")

@app.route("/other")
def page2():
    """Display page - no authentication required"""
    return render_template("page2.html")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/upload", methods=["POST"])
def upload():
    """Handle file uploads and broadcast to display page"""
    clear_uploads_on_login()

    if "files[]" not in request.files:
        logging.warning("No files uploaded")
        return "No files uploaded", 400

    files = request.files.getlist("files[]")
    uploaded_files = []

    for file in files:
        if file.filename == "":
            continue
        if not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        file_url = f"/uploads/{filename}"
        file_type = "image" if file.content_type.startswith("image") else "video"
        uploaded_files.append({
            "type": file_type,
            "url": file_url,
            "content_type": file.content_type
        })

    if not uploaded_files:
        return "No valid files uploaded", 400

    # Broadcast to display clients
    if len(uploaded_files) > 1:
        socketio.emit("update_content", {
            "type": "multiple_files",
            "files": uploaded_files
        }, room="page2_users")
    else:
        socketio.emit("update_content", {
            "type": uploaded_files[0]["type"],
            "file_url": uploaded_files[0]["url"]
        }, room="page2_users")

    return {"uploaded_files": [f['url'] for f in uploaded_files]}, 200

@app.route("/get_uploaded_files", methods=["GET"])
def get_uploaded_files():
    """Return list of uploaded files"""
    try:
        files = os.listdir(app.config["UPLOAD_FOLDER"])
        files = [file for file in files if os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], file))]
        files_urls = [f"/uploads/{file}" for file in files]
        return {"files": files_urls}, 200
    except Exception as e:
        logging.error(f"Error fetching files: {e}")
        return {"error": "Could not retrieve files"}, 500

# SocketIO event handlers
@socketio.on("connect")
def on_connect():
    """Handle new socket connections and room joining"""
    referer = request.headers.get("Referer", "")
    logging.info(f"Socket connected. Referer: {referer}")
    if "other" in referer:
        join_room("page2_users")  # Display page clients
        is_logged_in = any(logged_in_users.values())
        emit("check_login_status", {"logged_in": is_logged_in})
    else:
        join_room("page1_users")  # Editor page clients

@socketio.on("send_text")
def handle_text(data):
    """Broadcast text updates to display page"""
    socketio.emit(
        "update_content", 
        {
            "type": "text", 
            "message": data["message"], 
            "align": data.get("align", "left"),
            "animation": data.get("animation", "fade")
        }, 
        room="page2_users"
    )
    
@socketio.on("clear_display")
def handle_clear_display():
    """Clear content on display page"""
    socketio.emit("clear_display", {}, room="page2_users")

@socketio.on("check_login_status")
def check_login_status(data=None):
    """Respond with current login status"""
    is_logged_in = any(logged_in_users.values())
    emit("check_login_status", {"logged_in": is_logged_in}, to=request.sid)  

@socketio.on("disconnect")
def handle_disconnect():
    """Handle socket disconnection"""
    pass

@socketio.on("video_control")
def handle_video_control(data):
    """Control video playback on display page"""
    socketio.emit("video_control", data, room="page2_users")

@socketio.on("autoplay_blocked")
def handle_autoplay_blocked():
    """Notify editor when autoplay is blocked"""
    socketio.emit("autoplay_blocked", room="page1_users")

if __name__ == "__main__":
    socketio.run(app, debug=True)
