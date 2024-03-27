from flask import Flask, render_template, request, redirect, session, flash
import datetime
import mysql.connector
from helpers import apology, login_required
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from flaskext.mysql import MySQL
from cachetools import cached, TTLCache
from werkzeug.security import check_password_hash, generate_password_hash
import redis
from flask_session import Session

app = Flask(__name__)

cache = TTLCache(maxsize=1024, ttl=6000)
avge = TTLCache(maxsize=1024, ttl=6000)
suggest = TTLCache(maxsize=100, ttl=6000)

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 
app.config['MYSQL_DATABASE_PASSWORD'] = 
app.config['MYSQL_DATABASE_DB'] = 
app.config['MYSQL_DATABASE_HOST'] = '
mysql.init_app(app)

app.config['SECRET_KEY'] = 
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.Redis(host='redis-16378.c1.ap-southeast-1-1.ec2.cloud.redislabs.com', port='16378',
                password='')

server_session = Session(app)

# @app.before_request
# def make_session_permanent():
#     session.permanent = True
#     app.permanent_session_lifetime = datetime.timedelta(minutes=30)
#
# @app.after_request
# def after_request(response):
#     response.headers["Cache-Control"] = "public, no-store,max-age=604800, must-revalidate"
#     response.headers["Expires"] = 600
#     #tells the HTML to clear the stored data after 10 minutes
#     return response

@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    try:
        if request.method == 'POST':
            if request.form.get('action1') == '>':
                session["count"] += 1
                days = session["count"]
                Current_Date = add(days)# navigating date using class
            elif request.form.get('action2') == '<':
                session["count"] -= 1
                days = session["count"]
                Current_Date = add(days)
            Current_Date_Formatted = Current_Date.strftime('%Y-%m-%d 00:00:00')  # format the date to yyymmdd

            NextDay_Date = Current_Date + datetime.timedelta(days=0)
            Date_Formatted = NextDay_Date.strftime('%b-%d')
            labels, values = graph()
            # retrieve data from the database, only request once as the data is cached into memory
            index = binary_search(labels, 0, len(labels), Current_Date_Formatted)
            # locate today's date in the list
            i = 0

            value = []
            label = []
            while i < 24:
                value.append(values[index + i])
                label.append(labels[index + i])
                # add today's score and time into new lists
                i += 1

            date, fscores = avg()
            # load data from average table, only once as already cached
            result = binary_search(date, 0, len(date), Current_Date_Formatted)
            fscore = f'{fscores[result]:.0f}'
            headings1 = ("Date", "Score")
            # find today's date and its corresponding score
            data1 = sugggestion()
            # cached data of best days this month
            context = {
                'labels': label,
                'values': value,
                'today': Date_Formatted,
                'fscore': fscore,
                'headings1': headings1,
                'data1': data1
            }  # combine all data into a dictionary for faster HTML connection
            return render_template("graph.html", **context)
        else:
            if not "count" in session:
                session["count"] = 0
            days = session["count"]
            Current_Date = add(days)
            # Current_Date, i = Date.get()
            Current_Date_Formatted = Current_Date.strftime('%Y-%m-%d 00:00:00')  # format the date to ddmmyyyy
            NextDay_Date = Current_Date + datetime.timedelta(days=0)
            Date_Formatted = NextDay_Date.strftime('%b-%d')

            labels, values = graph()
            index = binary_search(labels, 0, len(labels), Current_Date_Formatted)
            i = 0

            value = []
            label = []
            while i < 24:
                value.append(values[index + i])
                label.append(labels[index + i])
                i += 1

            date, fscores = avg()
            result = binary_search(date, 0, len(date), Current_Date_Formatted)
            fscore = '{:.0f}'.format(fscores[result])
            headings1 = ("Date", "Score")
            data1 = sugggestion()

            context = {
                'labels': label,
                'values': value,
                'today': Date_Formatted,
                'fscore': fscore,
                'headings1': headings1,
                'data1': data1
            }
            return render_template("graph.html", **context)
    except:
        # Current_Date, i = Date.minus(1)
        session["count"] -= 1
        flash('No data available for this date. Sorry.')
        return redirect("/")

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = mysql.connect()
    cursor = conn.cursor()
    session.clear()
    if request.method == 'POST':

        username = request.form['email']  # request email as session
        password = request.form['password']  # request password

        find_user = "select * from heroku_5e2677edc19745f.user1 where username  ='%s'" % (username)
        # retrieve all the users in the database
        cursor.execute(find_user)
        results = cursor.fetchall()
        hash = []
        account = []
        for row in results:
            account.append(row[1])
            hash.append(row[4])

        # print("Password input: " + password)
        # print(check_password_hash(hash[0], password))
        if len(account) != 1 or not check_password_hash(hash[0], password) or len(password)==0:
            flash('Please check your login details and try again.','pass')
            return render_template("login.html")
        #if username and password are correct initiate the session and go to home page
        session["email"] = username
        return redirect("/")
        # if username inputed is not in the retrieved list, then out put the message
    else:

        return render_template("login.html")


@app.route("/data", methods=['GET', 'POST'])
@login_required
def data():
    # if session.get("email") is None:
    #     return redirect("/login")
    days = session["count"]
    Current_Date = add(days)
    Current_Date_Formatted = Current_Date.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
    Present_Date = Current_Date.strftime('%Y %b %d')
    NextDay_Date = Current_Date + datetime.timedelta(days=1)
    NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')
    headings = ("Time", "swell height", "swell period", "wind speed", "moon phase")
    data = getData(Current_Date_Formatted, NextDay_Date_Formatted)

    context = {
        'today': Present_Date,
        'headings': headings,
        'data': data
    }
    return render_template("weather.html", **context)


@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = mysql.connect()
    cursor = conn.cursor()

    if request.method == 'POST':
        found = 0
        while found == 0:
            username = request.form['username']
            find_user = "select * from heroku_5e2677edc19745f.user1 where username  ='%s'" % (username)
            cursor.execute(find_user)
            records = cursor.fetchall()
            if records:
                flash('Email address already exists', 'error')
                return redirect("/register")
            else:
                found == 1

                firstname = request.form['firstname']
                lastname = request.form['lastname']
                password = request.form['password']
                password1 = request.form['password1']
                if len(firstname) == 0 or len(lastname) == 0 or len(password) == 0 or len(password1) == 0:
                    flash('Please fill all the fields below.', 'pass')
                    return render_template('register.html')
                while password != password1:
                    flash('Password does not match!', 'pass')
                    return render_template('register.html')
                hash = generate_password_hash(password)
                print(hash)
                insertData = """INSERT INTO heroku_5e2677edc19745f.user1
                            (username,firstname, lastname, password)
                            VALUES (%s, %s, %s, %s)"""

                cursor.execute(insertData, (username, firstname, lastname, hash))
                session["email"]=username
                conn.commit()
                return redirect("/")
    return render_template('register.html')


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@cached(cache)
def graph():
    print("Connecting to mysql database")
    conn = mysql.connect()
    cursor = conn.cursor()

    sql = "select * from ( select datetime, score from heroku_5e2677edc19745f.weather_storm order by datetime desc limit 1000 ) " \
          "t order by datetime asc"
    #selecting the last 1000 rows and return them in ascending order
    cursor.execute(sql)

    # get all records
    records = cursor.fetchall()
    values = []
    date = []

    for row in records:
        date.append(row[0].strftime('%Y-%m-%d %H:%M:%S'))
        values.append(row[1])

    return date, values

@cached(avge)
def avg():
    conn = mysql.connect()
    cursor = conn.cursor()

    sql_select_Query = "select datetime, fscore from heroku_5e2677edc19745f.average order by datetime asc "
    #select datas from the average table, order day by ascending
    cursor.execute(sql_select_Query)
    # get all records
    records = cursor.fetchall()
    values = []
    date = []
    for row in records:
        date.append(row[0].strftime('%Y-%m-%d 00:00:00'))
        values.append(row[1])
    return date, values


@cached(cache)
def getData(x, y):
    conn = mysql.connect()
    cursor = conn.cursor()

    sql_select_Query = "select * from heroku_5e2677edc19745f.weather_storm where datetime BETWEEN %(date1)s AND %(date2)s"
    data = {
        'date1': x,
        'date2': y
    }
    cursor.execute(sql_select_Query, data)
    # get all records

    records = cursor.fetchall()
    return records


@cached(suggest)
def sugggestion():
    conn = mysql.connect()
    cursor = conn.cursor()

    sql_select_Query = "select * from heroku_5e2677edc19745f.average" \
                       " where MONTH(datetime) = MONTH(CURDATE()) order by fscore desc limit 3 "

    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    return records


def binary_search(arr, low, high, x):
    if high >= low:
        mid = (high + low) // 2 #find the middle index
        if arr[mid] == x: #check if the value at mid is what we want to find
            return mid #return this middle index if yes
        elif arr[mid] > x: #check if the value at mid is greater than what we want to find
            return binary_search(arr, low, mid - 1, x) #call the function again, update high to mid -1
        else:
            return binary_search(arr, mid + 1, high, x) #call the function again, update low to mid +1
    else:
        return -1 #if not found return -1


# class Date:
    # currentDate = datetime.datetime.today()
    # i = 0
    # def __init__(self):
    #     self.currentDate = datetime.datetime.today()
    #     self.i = 0
    # @classmethod
def add(x):
    currentDate = datetime.datetime.today()
    currentDate += datetime.timedelta(days=x)

    return currentDate

# @classmethod
def minus(x):
    currentDate = datetime.datetime.today()
    currentDate -= datetime.timedelta(days=x)

    return currentDate
    #
    # def get(self):
    #     return self.currentDate, self.i

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


def is_provided(field):
    if not request.form.get(field):
        return apology(f"must provide {field}", 403)


for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
