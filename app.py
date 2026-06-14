import re
import secrets
import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session, abort, flash, make_response
from werkzeug.security import generate_password_hash
import db
import config
import events
import users

app = Flask(__name__)
app.secret_key = config.secret_key

def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route("/")
def index():
    event_list = events.get_events()
    all_genres = events.get_all_genres()
    return render_template("index.html", events=event_list, all_genres=all_genres)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", filled={})
    
    if request.method == "POST":
        username = request.form["username"]
        if not username or len(username) > 16:
            flash("VIRHE: käyttäjänimen maksimipituus on 16 merkkiä")
            filled = {"username": username}
            return render_template("register.html", filled=filled)
        password1 = request.form["password1"]
        password2 = request.form["password2"]

        if password1 != password2 or not password1 or not password2:
            flash("VIRHE: salasanat eivät ole samat")
            filled = {"username": username}
            return render_template("register.html", filled=filled)

        try:
            users.create_user(username, password1)
            flash("Tunnuksen luominen onnistui")
            return redirect("/")
        except sqlite3.IntegrityError:
            flash("VIRHE: käyttäjänimi on jo käytössä")
            filled = {"username": username}
            return render_template("register.html", filled=filled)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    user_id = users.check_login(username, password)
    if user_id:
        session["user_id"] = user_id
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    else:
        flash("VIRHE: väärä tunnus tai salasana")
        return redirect("/")

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
    if "csrf_token" in session:
        del session["csrf_token"]
    return redirect("/")

@app.route("/new_event", methods=["POST"])
def new_event():
    require_login()
    check_csrf()

    title = request.form["title"]
    if not title or len(title) > 30:
        abort(403)
    date = request.form["date"]
    if not date:
        abort(403)
    try:
        num_players = int(request.form["num_players"])
        if num_players < 1 or num_players > 100:
            abort(403)
    except ValueError:
        abort(403)
    description = request.form["description"]
    if not description or len(description) > 200:
        abort(403)
    genre = request.form.get("genre")
    all_genres = events.get_all_genres()
    if not genre or genre not in all_genres:
        abort(403)
    
    user_id = session["user_id"]
    event_id = events.add_event(title, date, num_players, description, user_id, genre)
    return redirect("/event/" + str(event_id))

@app.route("/event/<int:event_id>")
def event_page(event_id):
    event = events.get_event(event_id)
    if not event:
        abort(404)
    registrations = events.get_registrations(event_id)
    return render_template("event.html", event=event, registrations=registrations)

@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    require_login()
    event = events.get_event(event_id)
    if not event:
        abort(404)
    if event["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        all_genres = events.get_all_genres()
        return render_template("edit.html", event=event, all_genres=all_genres, genre=event["genre"])

    if request.method == "POST":
        check_csrf()
        title = request.form["title"]
        if not title or len(title) > 30:
            abort(403)
        date = request.form["date"]
        if not date:
            abort(403)
        try:
            num_players = int(request.form["num_players"])
            if num_players < 1 or num_players > 100:
                abort(403)
        except ValueError:
            abort(403)
        description = request.form["description"]
        if not description or len(description) > 200:
            abort(403)
        genre = request.form.get("genre")
        all_genres = events.get_all_genres()
        if not genre or genre not in all_genres:
            abort(403)

        events.update_event(event["id"], title, date, num_players, description, genre)
        return redirect("/event/" + str(event_id))

@app.route("/remove/<int:event_id>", methods=["GET", "POST"])
def remove_event(event_id):
    require_login()
    event = events.get_event(event_id)
    if not event:
        abort(404)
    if event["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("remove.html", event=event)

    if request.method == "POST":
        check_csrf()
        if "continue" in request.form:
            events.remove_event(event_id)
        return redirect("/")

@app.route("/search")
def search_events():
    query = request.args.get("query")
    if query:
        results = events.search_events(query)
    else:
        results = []
    return render_template("search.html", query=query, results=results)

@app.route("/join/<int:event_id>", methods=["POST"])
def join_event(event_id):
    require_login()
    check_csrf()
    event = events.get_event(event_id)
    if not event:
        abort(404)
    user_id = session["user_id"]
    if events.join_event(user_id, event_id) is False:
        return "Olet jo ilmoittautunut "
    return redirect("/event/" + str(event_id))

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    user_events = events.get_user_events(user_id)
    return render_template("user.html", user=user, user_events=user_events)

def require_login():
    if not session.get("user_id"):
        flash("Kirjaudu sisään")
        abort(403)

@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    require_login()

    if request.method == "GET":
        return render_template("add_image.html")

    if request.method == "POST":
        check_csrf()
        if "image" not in request.files:
            abort(403)
        file = request.files["image"]
        if not file or not file.filename.endswith(".jpg"):
            return "VIRHE: väärä tiedostomuoto"

        image = file.read()
        if len(image) > 100 * 1024:
            return "VIRHE: liian suuri kuva"

        user_id = session["user_id"]
        users.update_image(user_id, image)
        return redirect("/user/" + str(user_id))

@app.route("/image/<int:user_id>")
def show_image(user_id):
    image = users.get_image(user_id)
    if not image:
        abort(404)

    response = make_response(bytes(image))
    response.headers.set("Content-Type", "image/jpeg")
    return response