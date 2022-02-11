
from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
import datetime
from tempfile import mkdtemp
import mysql.connector
from helpers import apology, login_required
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from flaskext.mysql import MySQL
from cachetools import cached, TTLCache
from flask_caching import Cache

app = Flask(__name__)
cache=TTLCache(maxsize=1024, ttl=600)
avge=TTLCache(maxsize=1024, ttl=600)
suggest=TTLCache(maxsize=100, ttl=600)

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'ba74ba05397a99'
app.config['MYSQL_DATABASE_PASSWORD'] = 'b48cfd68'
app.config['MYSQL_DATABASE_DB'] = 'heroku_5e2677edc19745f'
app.config['MYSQL_DATABASE_HOST'] = 'us-cdbr-east-04.cleardb.com'
mysql.init_app(app)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/", methods=['GET', 'POST'])
# @login_required
def index():
    if request.method == 'POST':
        if request.form.get('action1') == '>':
            Current_Date, i = Date.add(1)
        elif request.form.get('action2') == '<':
            Current_Date, i = Date.minus(1)
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
            'labels' : label,
            'values' : value,
            'today' : Date_Formatted,
            'fscore' : fscore,
            'headings1' : headings1,
            'data1' : data1
        }
        return render_template("graph.html", **context)
    else:
        Current_Date, i = Date.get()
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = mysql.connect()
    cursor = conn.cursor()

    if request.method == 'POST':

        session["email"] = request.form['email']
        username = session["email"]
        password = request.form['password']

        find_user = "select * from heroku_5e2677edc19745f.user1 where username = %s AND password = %s"
        data =[]
        val = username, password
        data.append(val)
        cursor.executemany(find_user, data)
        results = cursor.fetchall()
        if not results:
            flash('Please check your login details and try again.')
            return redirect("/login")
        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/data", methods=['GET', 'POST'])
@login_required
def data():
    Current_Date, i = Date.get()
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
                flash('Email address already exists')
                return redirect("/register")
            else:
                found = 1

                firstname = request.form['firstname']
                lastname = request.form['lastname']
                password = request.form['password']
                password1 = request.form['password1']
                while password != password1:
                    flash('Password does not match!')
                    # password = request.form['password']
                    # password1 = request.form['password1']
                    return render_template('register.html')

                insertData = """INSERT INTO heroku_5e2677edc19745f.user1
                            (username,firstname, lastname, password)
                            VALUES (%s, %s, %s, %s)"""
                data = []
                val = username, firstname, lastname, password
                data.append(val)
                cursor.execute(insertData, data)
                session["email"] = username
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

    sql = "select * from ( select datetime, score from heroku_5e2677edc19745f.weather_storm order by datetime desc limit 1000 ) t order by datetime asc"

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
        'date1' : x,
        'date2' : y
    }
    cursor.execute(sql_select_Query, data)
    # get all records

    records = cursor.fetchall()
    return records


@cached(suggest)
def sugggestion():

    conn = mysql.connect()
    cursor = conn.cursor()

    sql_select_Query = "select * from heroku_5e2677edc19745f.average where MONTH(datetime) = MONTH(CURDATE()) order by fscore desc limit 3 "

    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    return records


def binary_search(arr, low, high, x):
    if high >= low:
        mid = (high + low) // 2
        if arr[mid] == x:
            return mid
        elif arr[mid] > x:
            return binary_search(arr, low, mid - 1, x)
        else:
            return binary_search(arr, mid + 1, high, x)
    else:
        return -1


class Date:
    currentDate = datetime.datetime.today()
    i = 0

    @classmethod
    def add(cls, x):
        cls.currentDate += datetime.timedelta(days=x)
        cls.i += x
        return cls.currentDate, cls.i

    @classmethod
    def minus(cls, x):
        cls.currentDate -= datetime.timedelta(days=x)
        cls.i -= x
        return cls.currentDate, cls.i

    @classmethod
    def set(cls, x):
        cls.i = x
        return cls.i

    @classmethod
    def get(cls):
        return cls.currentDate, cls.i


# @app.errorhandler(500)
# def internal_error(error):
#     Curre
#     return "500 error"

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

# if __name__ == '__main__':
#     # port = int(os.environ.get('PORT', 5000))
#     # app.run(host='0.0.0.0', port=port)
#
#     app.run()
