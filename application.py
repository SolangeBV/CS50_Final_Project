import os
import json
import sys
import shutil
import datetime

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, months, piechart, edithtml, checkdate

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Add enum types of entries and incomes
TYPOLOGY = [
    "Household Expenses",
    "Health and Wellness",
    "Free Time",
    "Transport",
    "Family",
    "Salaries and Pensions",
    "Received Transfers",
    "Others"
    ]

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    creditrows = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
    credit=creditrows[0]["cash"]
    credit=float("{:.2f}".format(credit))

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        """Show expenses of a certain month"""
        selectedmonth=request.form.get("selectedmonth")

        # From month name (e.g.: January) to month number (e.g.: 1)
        month = int(months(selectedmonth))

        selectedyear=request.form.get("selectedyear")
        rows = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE userid = ? AND month = ? AND year = ?", session.get("user_id"), month, selectedyear)

        credit = 0
        for row in rows:
            credit = credit + row["amount"]

        thisdict = piechart(rows)
        edithtml(thisdict)

        return render_template("month.html", selectedmonth=selectedmonth, selectedyear=selectedyear, rows=rows, credit=credit, typology=TYPOLOGY)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # First, go through all the periodical payments and see if there's a recurrent payment due
        # Most likely this operation is NOT done by the server used to login a user, as this slows down the loading of the page
        # Also, this entire stupid process could be avoided by creating a thread waiting for that day for each recurrent payment, and only on that day this function would be started
        # I don't really know how to create a thread here atm^^

        today = datetime.now()
        this_day = today.day
        user_id = 0
        rows = db.execute("SELECT * FROM periodical")

        if len(rows) != None:
            for row in rows:
                hasChecked = row["checkdate"]
                user_id = row["userid"]
                description = row["description"]
                if hasChecked != this_day:
                    checkdate(user_id)
                    db.execute("UPDATE periodical SET checkdate = ? WHERE userid = ? AND checkdate = ? AND description = ?", this_day, user_id, hasChecked, description)

        return render_template("index.html", credit=credit)

@app.route("/addexpense", methods=["GET", "POST"])
@login_required
def addexpense():

    """Add expense"""
    if request.method == "POST":

        userId = session["user_id"]
        rows = db.execute("SELECT * FROM users WHERE id = ?", userId)
        credito = rows[0]["cash"]
        credito=float("{:.2f}".format(credito))

        # Ensure description was submitted
        if not request.form.get("description"):
            return apology("must provide description")

        description = request.form.get("description")

        # Ensure amount was submitted
        if not request.form.get("amount"):
            return apology("must provide amount")

        # Ensure amount is a number
        # Source: https://www.geeksforgeeks.org/python-check-for-float-string/
        test_string = request.form.get("amount")
        res = test_string.replace('.', '', 1).isdigit()
        if res == False:
            return apology("Amount must be a number with no symbols like € or $")

        positiveamount = float(request.form.get("amount"))
        amount = -abs(positiveamount)
        amount=float("{:.2f}".format(amount))

        # Ensure day was submitted
        if not request.form.get("day"):
            return apology("must provide a day")

        day = int(request.form.get("day"))

        # Ensure day is a number between 1 and 31
        if day<1 or day>31:
            return apology("day must be a number between 1 and 31")

        # Ensure month was submitted
        if not request.form.get("month"):
            return apology("must provide month")

        month = int(request.form.get("month"))

        # Ensure month is a number between 1 and 12
        if month<1 or month>12:
            return apology("month must be a number between 1 and 12")

        # Ensure year was submitted
        if not request.form.get("year"):
            return apology("must provide a year")

        year = int(request.form.get("year"))

        # Ensure type was submitted
        if not request.form.get("typology"):
            return apology("must provide type of payment")

        typology = request.form.get("typology")

        # Increase user's credit
        totale = credito + amount

        # Update database with new changes
        db.execute("UPDATE users SET cash = ? WHERE id = ?", totale, userId)
        db.execute("INSERT INTO household (userid, day, month, year, description, amount, type) VALUES (?, ?, ?, ?, ?, ?, ?)", userId, day, month, year, description, amount, typology)

        flash('Expense added')
        return redirect("/")

    # User reach route via GET
    else:
        return render_template("addexpense.html", typology=TYPOLOGY)

@app.route("/addincome", methods=["GET", "POST"])
@login_required
def addincome():
    """Add income"""
    if request.method == "POST":

        userId = session["user_id"]
        rows = db.execute("SELECT * FROM users WHERE id = ?", userId)
        credito = rows[0]["cash"]
        credito=float("{:.2f}".format(credito))

        # Ensure description was submitted
        if not request.form.get("description"):
            return apology("must provide description")

        description = request.form.get("description")

        # Ensure amount was submitted
        if not request.form.get("amount"):
            return apology("must provide amount")

        # Ensure amount is a number
        # Source: https://www.geeksforgeeks.org/python-check-for-float-string/
        test_string = request.form.get("amount")
        res = test_string.replace('.', '', 1).isdigit()
        if res == False:
            return apology("Amount must be a number with no symbols like € or $")

        amount = float(request.form.get("amount"))
        amount=float("{:.2f}".format(amount))

        # Ensure day was submitted
        if not request.form.get("day"):
            return apology("must provide a day")

        day = int(request.form.get("day"))

        # Ensure day is a number between 1 and 31
        if day<1 or day>31:
            return apology("day must be a number between 1 and 31")

        # Ensure month was submitted
        if not request.form.get("month"):
            return apology("must provide month")

        month = int(request.form.get("month"))

        # Ensure month is a number between 1 and 12
        if month<1 or month>12:
            return apology("month must be a number between 1 and 12")

        # Ensure year was submitted
        if not request.form.get("year"):
            return apology("must provide a year")

        year = int(request.form.get("year"))

        # Ensure type was submitted
        if not request.form.get("typology"):
            return apology("must provide type of payment")

        typology = request.form.get("typology")

        # Increase user's credit
        totale = credito+amount

        # Update database with new changes
        db.execute("UPDATE users SET cash = ? WHERE id = ?", totale, userId)
        db.execute("INSERT INTO household (userid, day, month, year, description, amount, type) VALUES (?, ?, ?, ?, ?, ?, ?)", userId, day, month, year, description, amount, typology)

        flash('Income added')
        return redirect("/")

    # User reach route via GET
    else:
        return render_template("addincome.html", typology=TYPOLOGY)

@app.route("/automate", methods=["GET", "POST"])
@login_required
def automate():

    """Add expense"""
    if request.method == "POST":

        current_user = session["user_id"]

        # Ensure description was submitted
        if not request.form.get("description"):
            return apology("must provide description")

        description = request.form.get("description")

        # Ensure amount was submitted
        if not request.form.get("amount"):
            return apology("must provide amount")

        # Ensure amount is a number
        # Source: https://www.geeksforgeeks.org/python-check-for-float-string/
        test_string = request.form.get("amount")
        res = test_string.replace('.', '', 1).isdigit()
        if res == False:
            return apology("Amount must be a number with no symbols like € or $")

        positiveamount = float(request.form.get("amount"))
        amount = -abs(positiveamount)
        amount=float("{:.2f}".format(amount))

        # Ensure day was submitted
        if not request.form.get("day"):
            return apology("must provide a day")

        day = int(request.form.get("day"))

        # Ensure day is a number between 1 and 31
        if day<1 or day>31:
            return apology("day must be a number between 1 and 31")

        # Ensure type was submitted
        if not request.form.get("typology"):
            return apology("must provide type of payment")

        typology = request.form.get("typology")

        # Update database with new changes
        db.execute("INSERT INTO periodical (userid, day, description, amount, type) VALUES (?, ?, ?, ?, ?)", current_user, day, description, amount, typology)

        flash('Automated expense added')
        return redirect("/")

    # User reach route via GET
    else:
        return render_template("automate.html", typology=TYPOLOGY)

@app.route("/history")
@login_required
def history():
    """Show history of expenses and incomes"""
    rows = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE userid = ? ORDER BY year DESC, month DESC, day DESC", session.get("user_id"))
    flash('Here the history of all your expenses and incomes')
    return render_template("history.html", rows=rows)

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        flash('You are now logged in')
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
    flash('You are now logged out')
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User registered via post
    if request.method == "POST":

        # Forget any user_id
        session.clear()
        username = request.form.get("username")

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure the two passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("The passwords don't match", 400)

        # Ensure the username is unique
        elif len(db.execute("SELECT * FROM users WHERE username = ?", username)) != 0:
            return apology("The username is already used", 400)

        else:
            username = request.form.get("username")
            password = request.form.get("password")
            thishash = generate_password_hash(password)

            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, thishash)

            # Redirect user to login page
            flash('You are now registered. Please log in')
            return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/removeexpense", methods=["GET", "POST"])
@login_required
def removeexpense():
    """Get expense"""
    description=request.form.get("description")
    if request.method == "POST":

        # Ensure stock quote was submitted
        if not request.form.get("description"):
            return apology("must provide description of transaction")

        # Ensure transaction exists
        transactions = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE description = ? AND userid = ?", description, session.get("user_id"))
        if len(transactions) == None:
            return apology("The transaction is not present in the database")


        # Loop this, in case the transaction name appears multiple times (e.g.: I delete all the "Stipendio" transactions)
        amount = 0
        for transaction in transactions:
            amount += transaction["amount"]

        users = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
        pastTotal = users[0]["cash"]
        newTotal = pastTotal - amount

        # Change the total credit account for that user
        db.execute("UPDATE users SET cash = ? WHERE id = ?", newTotal, session.get("user_id"))

        # Delete the row containing that expense
        db.execute("DELETE FROM household WHERE amount = ?", amount)

        message = "Expense removed"
        flash(message)
        return render_template("index.html")

    # User reach route via GET
    else:
        transactions = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE userid = ? AND amount < 0", session.get("user_id"))
        return render_template("removeexpense.html", transactions=transactions)

@app.route("/removeincome", methods=["GET", "POST"])
@login_required
def removeincome():
    """Get income"""
    description=request.form.get("description")
    if request.method == "POST":

        # Ensure stock quote was submitted
        if not request.form.get("description"):
            return apology("must provide description of transaction")

        # Ensure transaction exists
        transactions = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE description = ? AND userid = ?", description, session.get("user_id"))
        if len(transactions) == None:
            return apology("The transaction is not present in the database")

        # Loop this, in case the transaction name appears multiple times (e.g.: I delete all the "Stipendio" transactions)
        amount = 0
        for transaction in transactions:
            amount += transaction["amount"]

        users = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
        pastTotal = users[0]["cash"]
        newTotal = pastTotal - amount

        # Change the total credit account for that user
        db.execute("UPDATE users SET cash = ? WHERE id = ?", newTotal, session.get("user_id"))

        # Delete the row containing that expense
        db.execute("DELETE FROM household WHERE amount = ?", amount)

        message = "Income removed"
        flash(message)
        return render_template("index.html")

    # User reach route via GET
    else:
        transactions = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE userid = ? AND amount > 0", session.get("user_id"))
        return render_template("removeincome.html", transactions=transactions)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Get expense/income"""
    description=request.form.get("description")
    if request.method == "POST":

        # Ensure stock quote was submitted
        if not request.form.get("description"):
            return apology("must provide description of transaction")

        # Ensure transaction exists
        transactions = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE description = ? AND userid = ?", description, session.get("user_id"))
        if len(transactions) == None:
            return apology("The transaction is not present in the database")

        message = "Results for: " + description
        flash(message)
        return render_template("searched.html", transactions=transactions)

    # User reach route via GET
    else:
        transactions = db.execute("SELECT day, month, year, description, amount, type FROM household WHERE userid = ?", session.get("user_id"))
        return render_template("search.html", transactions=transactions)

@app.route("/showperiodicals")
@login_required
def showperiodicals():
    """Show all periodical payments for current user"""
    rows = db.execute("SELECT day, description, amount, type FROM periodical WHERE userid = ? ORDER BY day DESC", session.get("user_id"))
    flash('Here the list of all of your periodical payments')
    return render_template("showperiodicals.html", rows=rows)

@app.route("/stopperiodical", methods=["GET", "POST"])
@login_required
def stopperiodical():

    if request.method == "POST":

        # Ensure description was submitted
        if not request.form.get("description"):
            return apology("must provide description of transaction")
        description=request.form.get("description")

        # Ensure transaction exists
        periodicals = db.execute("SELECT day, description, amount, type FROM periodical WHERE description = ? AND userid = ?", description, session.get("user_id"))
        if len(periodicals) == None:
            return apology("The transaction is not present in the database")

        # Delete the row containing that recurrent payment
        db.execute("DELETE FROM periodical WHERE description = ? AND userid = ?", description, session.get("user_id"))

        message = "Recurrent payment removed"
        flash(message)
        return render_template("index.html")

    # User reach route via GET
    else:
        transactions = db.execute("SELECT * FROM periodical WHERE userid = ?", session.get("user_id"))
        return render_template("stopperiodical.html", transactions=transactions)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
