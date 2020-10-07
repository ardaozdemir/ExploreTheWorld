import os
import requests
import urllib.parse
import requests
import json

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



def distance(city1, city2):

    #Api to get city lat and long information

    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=393c1b4f02ee0aa5afe38fa55e0160e3'

    #Getting coordinates for two city

    coord1 = requests.get(url.format(city1)).json()

    coord2 = requests.get(url.format(city2)).json()

    lat_1 = coord1["coord"]["lat"]

    long_1 = coord1["coord"]["lon"]

    lat_2 = coord2["coord"]["lat"]

    long_2 = coord2["coord"]["lon"]

    #Api to calculate distance between to cities

    url = "https://distance-calculator.p.rapidapi.com/distance/simple"

    querystring = {"unit":"kilometers","lat_1":lat_1,"long_1":long_1,"lat_2":lat_2,"long_2":long_2}

    headers = {
        'x-rapidapi-host': "distance-calculator.p.rapidapi.com",
        'x-rapidapi-key': "cbdb5ea700msh9284def946f9791p1ecdfdjsn3248da96a848",
        'content-type': "application/json"
        }

    #Returning distance information
    return int(requests.request("GET", url, headers=headers, params=querystring).json()["distance"])



