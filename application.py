import os
from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

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

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
#db.execute("CREATE TABLE transactions (transaction_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, symbol TEXT NOT NULL, shares INTEGER NOT NULL, price NUMERIC NOT NULL)")
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    transactions = db.execute("SELECT symbol, SUM(shares), price FROM transactions where user_id= :user_id GROUP BY symbol", user_id=user_id)
    cash = db.execute("SELECT cash from users where id= :id", id=user_id)
    return render_template("index.html", transactions=transactions, cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        date_time = datetime.now()
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if not symbol:
            return apology("Must enter Symbol")

        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("shares must be a integer", 400)

        if shares <= 0:
            return apology("can't buy less than or 0 shares", 400)

        quote = lookup(symbol)
        if quote is None:
            return apology("Invalid Symbol", 400)
        user_id=session["user_id"]
        rows = db.execute("SELECT * FROM users where id = :user_id", user_id=user_id)
        cash_remaining = rows[0]["cash"]
        price_per_share = quote["price"]
        total_price = price_per_share * shares
        if total_price > cash_remaining:
            return apology("not enough funds")
        db.execute("UPDATE users SET cash=cash- :price where id= :user_id", price=total_price, user_id=user_id)
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date, time) VALUES (:user_id, :symbol, :shares, :price, :date, :time)",
            user_id = session["user_id"],
            symbol = symbol,
            shares = shares,
            price = price_per_share,
            date = "{}-{}-{}".format(date_time.day ,date_time.month, date_time.year),
            time = "{}:{}".format(date_time.hour, date_time.minute))
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM transactions where user_id= :user_id", user_id=session["user_id"])
    return render_template("history.html", transactions=transactions)


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

@app.route("/reset", methods=["GET", "POST"])
def reset():
    """Resets Password"""
    if request.method=="GET":
        return render_template("reset.html")
    username=request.form.get("username")
    old_password=request.form.get("old-password")

    rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], old_password):
        return apology("invalid username and/or password", 403)

    new_password=request.form.get("new-password")
    confirm_password=request.form.get("confirm-password")
    if new_password != confirm_password:
        return apology("Confirm Password Mismatch")
    db.execute("UPDATE users SET hash= :hash_value where id= :user_id",
            hash_value=generate_password_hash(new_password),
            user_id=rows[0]["id"])
    return redirect("/login")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quote = lookup(symbol)
        print(quote)
        if symbol == None:
            return apology("invalid symbol", 400)
        return render_template("quoted.html", quote=quote)
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return apology("must provide username", 403)
        user_id = db.execute("SELECT id from users WHERE username=?", username);
        if user_id:
            return apology("Username already exists",403)
        # Ensure password was submitted
        if not password:
            return apology("must provide password", 403)
        if password != request.form.get("confirmation"):
            return apology("Password Mismatch", 403)
        hash_value = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash_value)
        session["user_id"] = user_id
        return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    transactions = db.execute("SELECT symbol, SUM(shares), price FROM transactions where user_id= :user_id GROUP BY symbol", user_id=session["user_id"])
    if request.method == "POST":
        date_time = datetime.now()
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        if shares <= 0:
            return apology("Shares must be a positive Integer")
        for transaction in transactions:
            if transaction["symbol"] == symbol:
                quote = lookup(symbol)
                has_shares = transaction["SUM(shares)"]
                if has_shares < shares:
                    return apology("Not enough shares")
                user_id = session["user_id"]
                price_per_share = int(quote["price"])
                total_price = price_per_share * shares
                db.execute("UPDATE users SET cash=cash+ :price where id= :user_id", price=total_price, user_id=user_id)
                db.execute("INSERT INTO transactions (user_id, symbol, shares, price, date, time) VALUES (:user_id, :symbol, :shares, :price, :date, :time)",
                    user_id = user_id,
                    symbol = symbol,
                    shares = -shares,
                    price = price_per_share,
                    date = "{}-{}-{}".format(date_time.day ,date_time.month, date_time.year),
                    time = "{}:{}".format(date_time.hour, date_time.minute))
    return render_template("sell.html", transactions=transactions)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
