from flask import Flask, request, render_template, session, redirect, url_for, send_from_directory, flash
from flask_session import Session
from datetime import datetime, timedelta
import random
import os
import glob
import csv
import bcrypt
from src.chat_bot import ChatBot

KEYPHRASE_FILE = os.path.join(os.path.dirname(__file__), 'keyphrases.csv')

# Ensure keyphrase file exists
if not os.path.exists(KEYPHRASE_FILE):
    with open(KEYPHRASE_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'keyphrase'])

def load_keyphrases():
    keyphrases = {}
    with open(KEYPHRASE_FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keyphrases[row['username']] = row['keyphrase']
    return keyphrases

def save_keyphrase(username, keyphrase):
    keyphrases = load_keyphrases()
    # Hash the new keyphrase
    hashed = bcrypt.hashpw(keyphrase.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    keyphrases[username] = hashed
    # Write updated keyphrases to CSV
    with open(KEYPHRASE_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'keyphrase'])
        for user, key in keyphrases.items():
            writer.writerow([user, key])

# Flask setup
app = Flask(
    __name__,
    static_folder="../web/static",    
    template_folder="../web"            
)
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

@app.route("/delete_all_chats", methods=["POST"])
def delete_all_chats():
    username = session.get("username")
    if not username:
        return redirect(url_for("index"))

    deleted_count = 0
    try:
        for filename in os.listdir(CHAT_LOG_DIR):
            if filename.startswith(f"{username}_") and filename.endswith(".txt"):
                file_path = os.path.join(CHAT_LOG_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1

        # Clear current_log_id since all chats are gone
        session.pop("current_log_id", None)

        if deleted_count:
            flash(f"Deleted {deleted_count} conversation(s).", "success")
        else:
            flash("No conversations to delete.", "info")

    except Exception as e:
        flash(f"Error deleting chat history: {str(e)}", "danger")

    return redirect(url_for("chat"))

bot = ChatBot()

#Generate bot reply
def chit_chat(message):
    if not message.strip():
        return "Please say something!"
    return bot.get_response(message)

# Home page: enter name
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Please enter your name.", "danger")
            return redirect(url_for("index"))

        session["username"] = username
        session["keyphrase_verified"] = False  # Always reset on login

        # Check if user has a stored keyphrase
        keyphrases = load_keyphrases()
        if username in keyphrases:
            return redirect(url_for("verify_keyphrase"))

        # Otherwise go straight to chat
        return redirect(url_for("chat"))

    return render_template("index.html")

@app.route("/verify_keyphrase", methods=["GET", "POST"])
def verify_keyphrase():
    if request.method == "GET":
        return redirect(url_for("chat"))

    username = session.get("username")
    submitted_key = request.form.get("keyphrase", "")
    keyphrases = load_keyphrases()
    stored_key = keyphrases.get(username)

    if stored_key and bcrypt.checkpw(submitted_key.encode(), stored_key.encode()):  # bcrypt check
        session["keyphrase_verified"] = True
        flash("Keyphrase verified successfully.", "success")
    else:
        flash("Incorrect keyphrase. Try again.", "danger")

    return redirect(url_for("chat"))

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

@app.route("/chat", methods=["GET", "POST"])
def chat():
    username = session.get("username")
    if not username:
        return redirect(url_for("index"))

    keyphrases = load_keyphrases()
    stored_key = keyphrases.get(username)
    existing_files = glob.glob(os.path.join(CHAT_LOG_DIR, f"{username}_*.txt"))
    keyphrase_verified = session.get("keyphrase_verified", False)

    # Determine modal display flags
    show_set_keyphrase_modal = stored_key is None
    show_verify_keyphrase_modal = (
        stored_key is not None and
        existing_files and
        not keyphrase_verified
    )

    # 🔒 Block manual access to ?log=... if keyphrase not verified
    selected_log_id = request.args.get("log")
    if selected_log_id and not keyphrase_verified:
        return redirect(url_for("index"))

    # 🆔 Ensure there's a current log ID
    if "current_log_id" not in session:
        now = datetime.utcnow() + timedelta(hours=3)
        session["current_log_id"] = now.strftime("%Y-%m-%d_%H-%M")

    # 📨 Handle message sending
    if request.method == "POST":
        user_msg = request.form.get("message", "").strip()
        log_id = session.get("current_log_id")

        if not show_verify_keyphrase_modal and user_msg and log_id:
            now = datetime.utcnow() + timedelta(hours=3)
            save_message_to_file(username, username, user_msg, now, log_id)

            bot_reply = chit_chat(user_msg)
            bot_time = datetime.utcnow() + timedelta(hours=3)
            save_message_to_file(username, "Bot", bot_reply, bot_time, log_id)

    # 💬 Load chat history only if keyphrase is verified
    chat_history = []
    if not show_verify_keyphrase_modal:
        if selected_log_id:
            chat_history = load_chat_from_file(username, selected_log_id)
            session["current_log_id"] = selected_log_id
        else:
            chat_history = load_chat_from_file(username)

    return render_template(
        "index.html",
        chat_history=chat_history,
        username=username,
        all_conversations=list_user_conversations(username) if not show_verify_keyphrase_modal else [],
        current_log=session.get("current_log_id"),
        show_set_keyphrase_modal=show_set_keyphrase_modal,
        show_verify_keyphrase_modal=show_verify_keyphrase_modal
    )

@app.route("/set_keyphrase", methods=["POST"])
def set_keyphrase():
    if 'username' not in session:
        flash("Please enter your name first.", "danger")
        return redirect(url_for("index"))

    username = session["username"]
    keyphrase = request.form.get("keyphrase", "").strip()

    if keyphrase:
        save_keyphrase(username, keyphrase)
        session['keyphrase_verified'] = True
        flash("Keyphrase set successfully.", "success")
    else:
        flash("Keyphrase cannot be empty.", "danger")

    return redirect(url_for("chat"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
