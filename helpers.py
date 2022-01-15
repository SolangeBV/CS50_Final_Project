import os
import requests
import urllib.parse
import shutil

from datetime import datetime
from cs50 import SQL
from flask import redirect, render_template, request, session
from functools import wraps

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def months(s):

    """Turns name of months into their values"""
    for old, new in [("January", "1"), ("February", "2"), ("March", "3"), ("April", "4"),
                     ("May", "5"), ("June", "6"), ("July", "7"), ("August", "8"),
                     ("September", "9"), ("October", "10"), ("November", "11"), ("December", "12")]:
        s = s.replace(old, new)
    return s

def piechart(rows):

    """Calculates the percentages of the entries of a month"""

    total = 0

    household_expenses = 0
    health_and_wellness = 0
    free_time = 0
    transport = 0
    family = 0
    salaries_and_pensions = 0
    received_transfers = 0
    others = 0

    # Sum each amount into its own category
    for row in rows:
        total += row["amount"]

        if row["type"] == "Household Expenses":
            household_expenses += row["amount"]
        if row["type"] == "Health and Wellness":
            health_and_wellness += row["amount"]
        if row["type"] == "Free Time":
            free_time += row["amount"]
        if row["type"] == "Transport":
            transport += row["amount"]
        if row["type"] == "Family":
            family += row["amount"]
        if row["type"] == "Salaries and Pensions":
            salaries_and_pensions += row["amount"]
        if row["type"] == "Received Transfers":
            received_transfers += row["amount"]
        if row["type"] == "Others":
            others += row["amount"]

    # Create a dictionary storing all of this information
    thisdict = {
        'household_expenses': household_expenses,
        'health_and_wellness': health_and_wellness,
        'free_time': free_time,
        'transport': transport,
        'family': family,
        'salaries_and_pensions': salaries_and_pensions,
        'received_transfers': received_transfers,
        'others': others
    }

    return thisdict

# Rewrite "month.html" file, so that I can add a few lines in JavaScript
def edithtml(thisdict):

    # Rewrite exactly the beginning of "month.html" until line 20
    beginning = ""


    # Create a string called "jsonstr" containing the python dictionary and the JavaScript notation:

    jsonstr = "{% extends \"month_layout.html\" %}"
    jsonstr += "\n"
    jsonstr += "{% block div %}"
    jsonstr += "\n"
    jsonstr += "<script type ='text/javascript'>"
    jsonstr += "let jsonstr = "
    jsonstr += "'[{"
    counter = 0
    for key, value in thisdict.items():
        jsonstr += '"'
        jsonstr += key
        jsonstr += '": '
        jsonstr += str(value)
        counter+=1
        if counter != 8:
            jsonstr += ', '
    jsonstr += "}]';"
    jsonstr += "</script>"
    jsonstr += "\n"
    jsonstr += "{% endblock %}"

    # Create a html file with that string inside
    file = open('month.html', 'w')
    file.write(jsonstr)
    file.close()

    # Move that file into the "templates" folder
    src_path = "/home/ubuntu/project/month.html"
    dst_path = "/home/ubuntu/project/templates/month.html"
    shutil.move(src_path, dst_path)

# Create the possibility to automate regular payments
# This functions checks everyday if there's a recurrent expense to be transferred
def checkdate(user_id):
    today = datetime.now()
    this_year = today.year
    this_month = today.month
    this_day = today.day
    current_user = user_id

    transactions= db.execute("SELECT * FROM periodical WHERE userid = ? AND day = ?", current_user, this_day)
    credito = db.execute("SELECT cash FROM users WHERE id = ?", current_user)
    credito = credito[0]["cash"]

    if len(transactions) != None:
        for transaction in transactions:
            amount = transaction["amount"]
            description = transaction["description"]
            typology = transaction["type"]
            credito -= amount
            db.execute("INSERT INTO household (userid, day, month, year, description, amount, type) VALUES (?, ?, ?, ?, ?, ?, ?)", current_user, this_day, this_month, this_year, description, amount, typology)
            db.execute("UPDATE users SET cash = ? WHERE id = ?", credito, current_user)
