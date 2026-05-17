import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config
import events
import users

app = Flask(__name__)
app.secret_key = config.secret_key


@app.route("/")
def index():
    event_list = events.get_events()
    return render_template("index.html", events=event_list)


@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return """VIRHE: tunnus on jo varattu
                <hr />
                    <p>
                        <a href="/">Etusivulle</a>
                    </p>"""

    return """Tunnus luotu
            <hr />
                <p>
                    <a href="/">Etusivulle</a>
                </p>"""

@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    user_id = users.check_login(username, password)
    if user_id:
        session["user_id"] = user_id
        return redirect("/")
    else:
        return "VIRHE: väärä tunnus tai salasana"

@app.route("/logout")
def logout():
    del session["user_id"]
    return redirect("/")

@app.route("/new_event", methods=["POST"])
def new_event():
    title = request.form["title"]
    date = request.form["date"]
    num_players = request.form["num_players"]
    description = request.form["description"]
    user_id = session["user_id"]

    event_id = events.add_event(title, date, num_players, description, user_id)
    return redirect("/event/" + str(event_id))

@app.route("/event/<int:event_id>")
def event_page(event_id):
    event = events.get_event(event_id)
    return render_template("event.html", event=event)

@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    event = events.get_event(event_id)

    if request.method == "GET":
        return render_template("edit.html", event=event)

    if request.method == "POST":
        description = request.form["description"]
        event.update_event(event["id"], description)
        return redirect("/event/" + str(event["event_id"]))