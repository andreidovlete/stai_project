from flask import Flask, request, render_template, session, redirect, url_for
from flask_session import Session
from datetime import datetime, timedelta
import random

# Flask setup with custom folders
app = Flask(__name__, template_folder='../web', static_folder='../web/static')
app.secret_key = 'chatbot_secret_key'  
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Simple response generator
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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("username")
        if name:
            session['username'] = name
            session['chat_history'] = []
            return redirect(url_for("chat"))
    return render_template("index.html", username=None)

@app.route("/chat", methods=["GET", "POST"])
def chat():
    username = session.get("username", "You")
    if "chat_history" not in session:
        session["chat_history"] = []

    if request.method == "POST":
        user_msg = request.form.get("message", "").strip()
        if user_msg:
            now = datetime.utcnow() + timedelta(hours=3)  # GMT+3
            session['chat_history'].append(("user", username, user_msg, now))
            bot_reply = chit_chat(user_msg)
            bot_time = datetime.utcnow() + timedelta(hours=3)
            session['chat_history'].append(("bot", "Bot", bot_reply, bot_time))
            session.modified = True

    return render_template("index.html", chat_history=session["chat_history"], username=username)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
