from flask import Flask, request, render_template, session, redirect, url_for, send_from_directory, flash
from flask_session import Session
from datetime import datetime, timedelta
import random
import os
import glob

# Flask setup
app = Flask(__name__, template_folder='../web', static_folder='../web/static')
app.secret_key = 'chatbot_secret_key'
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Directory to save chat logs
CHAT_LOG_DIR = os.path.join(os.path.dirname(__file__), 'chat_logs')
os.makedirs(CHAT_LOG_DIR, exist_ok=True)


# Save a message to a uniquely named file
def save_message_to_file(username, sender, message, timestamp, log_id):
    filename = f"{username}_{log_id}.txt"
    filepath = os.path.join(CHAT_LOG_DIR, filename)
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp.strftime('%H:%M')}] {sender}: {message}\n")


# Load a chat file into structured list
def load_chat_from_file(username, log_id=None):
    if not log_id:
        log_id = session.get("current_log_id")

    if not log_id:
        return []

    filename = f"{username}_{log_id}.txt"
    filepath = os.path.join(CHAT_LOG_DIR, filename)
    chat_history = []

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    timestamp_part, rest = line.strip().split("] ", 1)
                    timestamp = datetime.strptime(timestamp_part[1:], "%H:%M")
                    sender, message = rest.split(":", 1)
                    name = sender.strip()
                    msg = message.strip()
                    who = "bot" if name.lower() == "bot" else "user"
                    chat_history.append((who, name, msg, timestamp))
                except ValueError:
                    continue  # ignore malformed lines
    return chat_history

# List all conversation logs for the user
def list_user_conversations(username):
    files = glob.glob(os.path.join(CHAT_LOG_DIR, f"{username}_*.txt"))
    history = []

    for filepath in sorted(files, reverse=True):
        filename = os.path.basename(filepath)
        try:
            # Extract log ID (date-time) from filename
            log_id = filename.split(f"{username}_")[1].replace(".txt", "")
            readable = datetime.strptime(log_id, "%Y-%m-%d_%H-%M").strftime("%b %d, %Y %H:%M")

            # Read first message preview
            with open(filepath, "r", encoding="utf-8") as f:
                first_line = next(f, "").strip()
                if "] " in first_line and ":" in first_line:
                    _, rest = first_line.split("] ", 1)
                    sender, message = rest.split(":", 1)
                    preview = f"{sender.strip()}: {message.strip()}"
                else:
                    preview = "(no message)"
            
            # Limit preview length and format
            display_name = preview if len(preview) <= 40 else preview[:37] + "..."
            history.append((log_id, readable, display_name))

        except Exception:
            continue  # skip malformed logs

    return history

@app.route("/delete_chat/<log_id>", methods=["POST"])
def delete_chat(log_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("index"))

    filename = f"{username}_{log_id}.txt"
    filepath = os.path.join(CHAT_LOG_DIR, filename)

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            flash("Conversation deleted successfully.", "success")
        else:
            flash("Conversation not found.", "danger")
    except Exception as e:
        flash(f"Error deleting conversation: {str(e)}", "danger")

    return redirect(url_for("chat"))

# Generate bot reply
def chit_chat(message):
    responses = [
        "That's interesting!",
        "Tell me more!",
        "I like chatting with you.",
        "Haha, good one!",
        "Why do you say that?",
        "Sounds cool!",
    ]
    return random.choice(responses)


# Home page: enter name
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("username")
        if name:
            session['username'] = name
            return redirect(url_for("new_conversation"))
    return render_template("index.html", username=None)


# Create a new conversation
@app.route("/new")
def new_conversation():
    username = session.get("username")
    if not username:
        return redirect(url_for("index"))

    now = datetime.utcnow() + timedelta(hours=3)
    log_id = now.strftime("%Y-%m-%d_%H-%M")
    session['current_log_id'] = log_id
    return redirect(url_for("chat"))


# Chat view
@app.route("/chat", methods=["GET", "POST"])
def chat():
    username = session.get("username")
    if not username:
        return redirect(url_for("index"))

    # If viewing an old conversation
    selected_log_id = request.args.get("log")

    if request.method == "POST":
        user_msg = request.form.get("message", "").strip()
        log_id = session.get("current_log_id")

        if user_msg and log_id:
            now = datetime.utcnow() + timedelta(hours=3)
            save_message_to_file(username, username, user_msg, now, log_id)

            bot_reply = chit_chat(user_msg)
            bot_time = datetime.utcnow() + timedelta(hours=3)
            save_message_to_file(username, "Bot", bot_reply, bot_time, log_id)

    # Determine which conversation to load
    if selected_log_id:
        chat_history = load_chat_from_file(username, selected_log_id)
    else:
        chat_history = load_chat_from_file(username)

    all_conversations = list_user_conversations(username)
    return render_template("index.html",
                           chat_history=chat_history,
                           username=username,
                           all_conversations=all_conversations,
                           current_log=session.get("current_log_id"))


# Download chat
@app.route("/download_chat/<filename>")
def download_chat(filename):
    return send_from_directory(CHAT_LOG_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
