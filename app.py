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


@app.route("/")
def index():
    event_list = events.get_events()
    return render_template("index.html", events=event_list)

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
        return redirect("/")
    else:
        flash("VIRHE: väärä tunnus tai salasana")
        return redirect("/")

@app.route("/logout")
def logout():
    del session["user_id"]
    return redirect("/")

@app.route("/new_event", methods=["POST"])
def new_event():
    require_login()
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
    if not event:
        abort(404)
    registrations = events.get_registrations(event_id)
    return render_template("event.html", event=event, registrations=registrations)

@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    event = events.get_event(event_id)

    if request.method == "GET":
        return render_template("edit.html", event=event)

    if request.method == "POST":
        title = request.form["title"]
        date = request.form["date"]
        num_players = request.form["num_players"]
        description = request.form["description"]
        events.update_event(event["id"], title, date, num_players, description)
        return redirect("/event/" + str(event_id))

@app.route("/remove/<int:event_id>", methods=["GET", "POST"])
def remove_event(event_id):
    event = events.get_event(event_id)

    if request.method == "GET":
        return render_template("remove.html", event=event)

    if request.method == "POST":
        if "continue" in request.form:
            events.remove_event(event_id)
        return redirect("/")

@app.route("/search")
def search_events():
    query = request.args.get("query")
    results = events.search_events(query) if query else []
    return render_template("search.html", query=query, results=results)

@app.route("/join/<int:event_id>", methods=["POST"])
def join_event(event_id):
    user_id = request.form["user_id"]
    if not user_id:
        abort(400)
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
        return redirect("/")

@app.route("/add_image", methods=["GET", "POST"])
def add_image():
    require_login()

    if request.method == "GET":
        return render_template("add_image.html")

    if request.method == "POST":
        file = request.files["image"]
        if not file.filename.endswith(".jpg"):
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