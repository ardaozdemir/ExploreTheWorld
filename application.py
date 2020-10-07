import requests
import json
from flask import Flask, render_template, request, flash, jsonify, redirect, session
from cs50 import SQL
from google_currency import convert
import os
import datetime
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, distance
import http.client
from bs4 import BeautifulSoup


app = Flask(__name__)
app.config['DEBUG'] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///country.db")

@app.route("/")
@login_required

def index():

    #Url's for weather and country info API

    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=393c1b4f02ee0aa5afe38fa55e0160e3'
    url2 = 'https://restcountries.eu/rest/v2/alpha/{}'

    #Arrays to store information about cities

    all_info = []

    cities = []

    #Getting data from the database

    city = db.execute("SELECT name FROM city")

    user_city = db.execute("SELECT city FROM users WHERE id = :userid", userid = session["user_id"])

    preferences = db.execute("SELECT * FROM preferences WHERE user_id = :userid", userid = session["user_id"])

    #Setting preferences to display

    currency_type = preferences[0]["currency"]

    distance_type = preferences[0]["distance"]

    degree_type = preferences[0]["degree"]

    #Adding cities on the database to an array

    for i in range(len(city)):

        cities.append(city[i]["name"])

    #Getting information about all cities on the array

    for city in cities:

        weather = requests.get(url.format(city)).json()
        country = weather["sys"]["country"]
        info = requests.get(url2.format(country)).json()
        data = convert(currency_type, info["currencies"][0]["code"], 1)
        currency = json.loads(data)

        temp = round(((float(weather["main"]["temp"])-32)*5)/9)

        #Checking the preferences

        if degree_type == "F":

            temp = round(float(weather["main"]["temp"]))

        distancee = distance(user_city[0]["city"], city)

        if distance_type == "miles":

            distancee = round((distance(user_city[0]["city"], city)*5)/8)


        #Adding all informationa about a city to a dictionary

        new_city = {

            "name": city,
            "temp": temp,
            "description": weather["weather"][0]["description"].capitalize(),
            "icon": weather["weather"][0]["icon"],
            "degree_type" : degree_type,
            "currency_price": currency["amount"],
            "currency_name" : currency["to"],
            "currency_type" : currency_type,
            "flag" : info["flag"],
            "distance": distancee,
            "distance_type" : distance_type,
            "time_zone" : info["timezones"][0]

        }

        #Adding city with details in a array

        all_info.append(new_city)


    return render_template("index.html", all_info = all_info)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))


        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    if request.method == "POST":

        #Checking if there is no username

        if not request.form.get("username"):
            return redirect("/register")


        if not request.form.get("password"):
            return redirect("/register")

        if not request.form.get("city"):
            return redirect("/register")

        if not request.form.get("code"):
            return redirect("/register")

        if not request.form.get("number"):
            return redirect("/register")

        if not request.form.get("firstname"):
            return redirect("/register")

        if not request.form.get("lastname"):
            return redirect("/register")


        #Checking if two password match or not

        if request.form.get("password") != request.form.get("confirmation"):
            return redirect("/register")

        #Getting the usernames with users username input

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        #Checking if the username exit

        if len(rows) == 1:

            return apology("Username was taken")

        #Saving user to the database

        if len(rows) != 1:

            db.execute("INSERT INTO users (username, firstname, lastname, hash, city, code, phone) VALUES (:username, :firstname, :lastname, :hash, :city, :code, :phone)" , username = request.form.get("username"),
            firstname = request.form.get("firstname"), lastname = request.form.get("lastname"), hash = generate_password_hash(request.form.get("password")), city = request.form.get("city"), code = request.form.get("code"),
            phone = request.form.get("number"))

        #Redirecting to the homepage

        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/account", methods=["GET", "POST"])
@login_required
def account():

    if request.method == "GET":

        #Getting all information about a person from database

        user = db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session["user_id"])

        userdict = {
            "first": user[0]["firstname"].capitalize(),
            "last": user[0]["lastname"].capitalize(),
            "city": user[0]["city"],
            "code": user[0]["code"],
            "phone": user[0]["phone"]
        }

        return render_template("account.html", userdict = userdict)

    else:
        #Checking if the two password same

        if request.form.get("password") == request.form.get("confirmation"):

            password = generate_password_hash(request.form.get("password"))

        #Updating the password

        db.execute("UPDATE users SET hash=:password WHERE id=:ids", password=password, ids= session["user_id"])

        return render_template("account.html", success=1)


@app.route("/city", methods=["GET", "POST"])
@login_required
def city():

    #Checking if user send an input

    if request.method == "POST":

        #Checking if user entered a city as input

        if not request.form.get("city"):
            return redirect("/city")

        #Getting cities named with same name

        rows = db.execute("SELECT * FROM city WHERE name = :city", city=request.form.get("city"))

        #If the city is in the database error message send

        if len(rows) == 1:

            return apology("City already in database")

        #If the city is not in the database it adds it to database

        if len(rows) != 1:

            db.execute("INSERT INTO city (person_id, name) VALUES (:user_id, :city)" , user_id = session["user_id"], city = request.form.get("city"))

        #Redirecting the city page

        return redirect("/city")

    if request.method == "GET":

        #Displaying all cities that user saved

        city = db.execute("SELECT * FROM city")

        #Sending length and city information

        return render_template("city.html", city = city, length = len(city))

@app.route("/delete/<int:city_id>")
@login_required

def delete(city_id):

    #Deleting a city from the database

    db.execute("DELETE FROM city WHERE city_id = :city_id", city_id = city_id)

    return redirect("/city")

@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():

    #Checking if user send a information

    if request.method == "POST":

        #Checking if user enter a currency

        if not request.form.get("currency"):

            return redirect("/preferences")


        currency = request.form.get("currency").upper()
        degree = ""
        distance = ""

        #Checking if user enter a degree type

        if request.form.get("deg"):

            degree = request.form.get("deg")

        #Checking if user enter a distance type

        if request.form.get("dis"):

            distance = request.form.get("dis")

        #Getting the previous preferences for the user from the database

        test = db.execute("SELECT * FROM preferences WHERE user_id = :user_id", user_id = session["user_id"])

        #Checking if a user has previous preferences

        if len(test) == 1:

            db.execute("UPDATE preferences SET currency=:currency, degree=:degree, distance=:distance WHERE user_id=:user_id", currency = currency,
            degree = degree, distance = distance, user_id= session["user_id"])

        #If user do not have a previous preferences creates a new row

        if len(test) != 1:

            db.execute("INSERT INTO preferences  (user_id, currency, degree, distance) VALUES (:user_id, :currency, :degree, :distance)" , user_id= session["user_id"], currency = currency,
            degree = degree, distance = distance)

        #Redirecting the preferences page

        return redirect("/preferences")

    #If method is get it displays the page

    else:

        return render_template("preferences.html")





def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
