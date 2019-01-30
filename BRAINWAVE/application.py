from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, make_response
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
import datetime
import requests
import json
import random
from random import shuffle
import re

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")


@app.route("/")
def index():

    return render_template("index.html")


@app.route("/spelregels")
def spelregels():

    return render_template("spelregels.html")


@app.route("/scoreOnline", methods=["GET", "POST"])
def scoreOnline():
    if request.method == "POST":
        # Retrieve value of category
        data = request.data
        category_load = json.loads(data)
        category = category_load.get('category')
        # Ensure that the scores of users will be put into a table to view
        if category == '0':
            scoreOnline = db.execute("SELECT username, score, timestamp FROM scores ORDER BY score DESC")
        else:
            scoreOnline = db.execute("SELECT username, score, timestamp FROM scores WHERE category = :category ORDER BY score DESC", category=category)
        return render_template("scoreOnline.html", scoreOnline=scoreOnline)
    if request.method == "GET":
        return render_template("scoreOnline.html")


@app.route("/speelpagina")
def speelpagina():

    return render_template("speelpagina.html")


@app.route("/speelpaginaoffline")
def speelpaginaoffline():

    return render_template("speelpaginaoffline.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    gebruikersnaam = session["username"]
    if request.method == "POST":
        # Retrieve value of category
        data = request.data
        category_load = json.loads(data)
        category = category_load.get('category')
        # Ensure that the scores of users will be put into a table to view
        if category == '0':
            scores = db.execute("SELECT username, score, timestamp FROM scores WHERE id = :id ORDER BY score DESC", id=session["user_id"])
        else:
            scores = db.execute("SELECT username, score, timestamp FROM scores WHERE category = :category AND id = :id ORDER BY score DESC", category=category, id=session["user_id"])
        return render_template("account.html", gebruikersnaam=gebruikersnaam, scores=scores)
    if request.method == "GET":
        gebruikersnaam = session["username"]
        return render_template("account.html", gebruikersnaam=gebruikersnaam)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # remember username
        session["username"] = rows[0]["username"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "POST":

        # Ensure username is provided
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password is provided
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure password is longer than 4 characters
        elif len(request.form.get("password")) < 4:
            return apology("enter password with more than 4 characters")

        # Ensure username does not contain spaces
        elif ' ' in request.form.get("username"):
            return apology("No spaces allowed in username")

        # Ensure password does not contain spaces
        elif ' ' in request.form.get("password"):
            return apology("No spaces allowed in password")

        # Ensure password confirmation is provided
        elif not request.form.get("confirmation"):
            return apology("must provide password (again)")

        # Ensure that password and the confirmation are the same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords not the same")

        password = pwd_context.hash(request.form.get("password"))

        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hashpassword)",
                                username=request.form.get("username"),
                                hashpassword=password)

        if not result:
            return apology("The username is already taken")

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                                   username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        # remember username
        session["username"] = rows[0]["username"]

        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/speelopties", methods=['GET', 'POST'])
def speelopties():
    if request.method == "POST":
        entry = request.get_json()
        print(entry['game'])
        if entry['game'] == 'ranked':
            ranked = True
        else:
            ranked = False

        print(ranked)
        # Get category by number
        iCategory = str(entry['category'])
        session['category'] = iCategory
        # Get total amount of questions
        iAmount = '10'

        if iCategory != "-1":
            url = "https://opentdb.com/api.php?amount="+iAmount+"&category="+iCategory+"&medium=medium"+"&type=multiple"
            # get the data corresponded to the url
            data = requests.get(url).text
            # replace unique tokens for the original symbol
            data = data.replace("&quot;", "'")
            data = data.replace("&#039;", "'")
            data = data.replace("&amp;", "&")
            data = data.replace("I&ntilde;&aacute;rritu;", " ")
            data = data.replace("Zeln&iacute;čkov&aacute;", "Zelníčková")
            data = data.replace("&acute;", "a")
            data = data.replace("&ecute;", "e")
            data = data.replace("&Prime;", "'")

            data = json.loads(data)
            # format first question:
            questions = []
            for entry in data["results"]:
                q = [x for x in entry["incorrect_answers"]]
                q.append(entry["correct_answer"])
                q = sorted(q, key=lambda x: random.random())

                entry["random_answers"] = q
                questions.append(entry)

        else:
            questionHolder = []
            for num in ['11', '12', '15', '21', '26']:
                url = "https://opentdb.com/api.php?amount="+'2'+"&category="+num+"&medium=medium"+"&type=multiple"
                data = requests.get(url).text
                data = data.replace("&quot;", "'")
                data = data.replace("&#039;", "'")
                data = data.replace("&amp;", "&")
                data = data.replace("I&ntilde;&aacute;rritu;", " ")
                data = data.replace("Zeln&iacute;čkov&aacute;","Zelníčková")
                data = data.replace("&acute;", "a")
                data = data.replace("&ecute;", "e")
                data = data.replace("&Prime;", "'")

                data = json.loads(data)
                # format first question:
                questionHolder.append(data["results"][0])
                questionHolder.append(data["results"][1])

            # format first question:
            questions = []
            for entry in questionHolder:
                q = [x for x in entry["incorrect_answers"]]
                q.append(entry["correct_answer"])
                q = sorted(q, key=lambda x: random.random())

                entry["random_answers"] = q
                questions.append(entry)

            # Will put the answers in a different order on every question
            questions = sorted(questions, key=lambda x: random.random())
        if ranked == True:
            return render_template('api.html', url=url, output=data, questions=questions, iCategory=iCategory)
        else:
            # Gives a random message to a player while playing the game
            random_message = ["Tijd om een bad te nemen ",
                              "Even een kopje koffie zetten ",
                              "Sluit je ogen en tel tot 100.000.000 ",
                              "Niet spieken ",
                              "Ik zie je wel kijken! ",
                              "Koop een taart en vier je overwinning ",
                              "Wel winnen he! ",
                              "Even een speld in een hooiberg zoeken ",
                              "Verzin een mooi gedicht ",
                              "Tijd om te stofzuigen "
                              ]
            # Random message for each player
            r1 = random_message[random.randrange(len(random_message))]
            r2 = random_message[random.randrange(len(random_message))]
            return render_template('apiLocal.html', url=url, output=data, questions=questions, iCategory=iCategory, r1=r1,r2=r2)

    return render_template("speelopties.html")


@app.route("/eindresultaat", methods=['GET', 'POST'])
def eindresultaat():
    if request.method == "POST":
        Answers = request.get_json()
        print(Answers)
        if "game" in Answers:

            # Checks the correct answers of each player
            p1Good = [True if Answers["ca" + str(i)] == Answers["a" + str(i)+"p1"] else False for i in range(10) if "a" + str(i)+"p1" in Answers]
            p2Good = [True if Answers["ca" + str(i)] == Answers["a" + str(i)+"p2"] else False for i in range(10) if "a" + str(i)+"p2" in Answers]
            p1Score = p1Good.count(True)
            p2Score = p2Good.count(True)
            return render_template("eindresultaat.html", Answers=Answers, Score1=p1Score, Score2=p2Score, mode="local")

        else:
            username = session.get("username")
            category = session.get('category')

            # Checks if the answer of the user is the same as te correct answer
            good = []
            for i in range(10):
                try:
                    if Answers["ca" + str(i)] == Answers["a" + str(i)]:
                        good.append("True")
                    else:
                        good.append("False")
                except KeyError:
                    good.append("False")

            # Counts the amount of correct answers
            Score = 0
            for i in good:
                if i == "True":
                    Score += 1
                else:
                    Score == Score

            if username is not None:
                # Stores score in database to the corresponding user
                db.execute("INSERT INTO 'scores' (id, username, score, category) VALUES(:id, :username, :Score, :category)",
                       id=session["user_id"], username=username, Score=Score, category=category)
            return render_template("eindresultaat.html", Answers=Answers, Score=Score, mode="ranked")
