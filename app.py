import os

from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session
import datetime
from tempfile import mkdtemp
import mysql.connector
from helpers import apology
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError


# from flask_mysqldb import MySQL
# format the date to ddmmyyyy

app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# app.config['MYSQL_HOST'] = 'us-cdbr-east-04.cleardb.com'
# app.config['MYSQL_USER'] = 'ba74ba05397a99'
# app.config['MYSQL_PASSWORD'] = 'b48cfd68'
# app.config['MYSQL_DB'] = 'heroku_5e2677edc19745f'
#
# mysql = MySQL(app)

@app.route("/", methods=['GET', 'POST'])
def index():
    if not session.get("email"):
        return redirect("/login")
    if request.method == 'POST':
        if request.form.get('action1') == '>':
            Current_Date, i = Date.add(1)
        elif request.form.get('action2') == '<':
            Current_Date, i = Date.minus(1)
        Current_Date_Formatted = Current_Date.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
        NextDay_Date = Current_Date + datetime.timedelta(days=1)
        NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')

        labels, values = graph(Current_Date_Formatted, NextDay_Date_Formatted)
        date, fscores = avg()

        result = binary_search(date, 0, len(date), Current_Date_Formatted)
        fscore = fscores[result]
        headings = ("Time", "swell height", "swell period", "wind speed", "moon phase")
        data = getData(Current_Date_Formatted, NextDay_Date_Formatted)
        headings1 = ("Date", "Score")
        data1 = sugggestion()

        return render_template("graph.html", labels=labels, values=values, today=Current_Date_Formatted, fscore=fscore,
                               headings=headings, data=data, headings1=headings1, data1=data1 )
    else:
        Current_Date_Formatted = datetime.datetime.today().strftime('%Y-%m-%d')  # format the date to ddmmyyyy
        NextDay_Date = datetime.datetime.today() + datetime.timedelta(days=1)
        NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')

        labels, values = graph(Current_Date_Formatted, NextDay_Date_Formatted)
        date, fscores = avg()
        result = binary_search(date, 0, len(date), Current_Date_Formatted)
        fscore = fscores[result]
        headings = ("Time", "swell height", "swell period", "wind speed", "moon phase")
        data = getData(Current_Date_Formatted, NextDay_Date_Formatted)
        headings1 = ("Date", "Score")
        data1 = sugggestion()

        return render_template("graph.html", labels=labels, values=values, today=Current_Date_Formatted, fscore=fscore,
                               headings=headings, data=data, headings1=headings1, data1=data1)

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    if request.method == 'POST':

        session["email"],username = request.form['email']
        password = request.form['password']
        # cursor = mysql.connection.cursor()
        cursor =cnx.cursor()
        find_user = "select * from heroku_5e2677edc19745f.user1 where username = %s AND password = %s"
        cursor.execute(find_user, (username, password))
        results = cursor.fetchall()
        if not results:
            flash('Please check your login details and try again.')
            return redirect("/login")
        data = []
        for row in results:
            data.append(row[0])
        session["user_id"] = data
        return redirect("/")

    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    if request.method == 'POST':
        found = 0
        while found == 0:
            username = request.form['username']
            find_user = "select * from heroku_5e2677edc19745f.user1 where username  ='%s'" % (username)
            cursor = cnx.cursor()
            cursor.execute(find_user)
            records = cursor.fetchall()
            if records:
                flash('Email address already exists')
                return redirect("/register")
            else:
                found == 1

                firstname = request.form['firstname']
                lastname = request.form['lastname']
                password = request.form['password']
                password1 = request.form['password1']
                while password != password1:
                    password = request.form['password']
                    password1 = request.form['password1']
                    return render_template('register.html')

                insertData= """INSERT INTO heroku_5e2677edc19745f.user1
                            (username,firstname, lastname, password)
                            VALUES (%s, %s, %s, %s)"""
                prim_key = cursor.execute(insertData, (username, firstname, lastname, password))
                session["user_id"] = prim_key
                cnx.commit()
                return redirect("/")
    return render_template('register.html')

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

def graph(x, y):
    print("Connecting to mysql database")
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    cursor = cnx.cursor()
    sql_select_Query = "select datetime, score from heroku_5e2677edc19745f.weather_storm where datetime BETWEEN %s AND %s"
    cursor.execute(sql_select_Query, (x, y))
    # get all records
    records = cursor.fetchall()
    labels = []
    values = []
    for row in records:
        labels.append(row[0])
        values.append(row[1])
    return labels, values


def avg():
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    sql_select_Query = "select * from heroku_5e2677edc19745f.average"
    cursor = cnx.cursor()
    cursor.execute(sql_select_Query)
    # get all records
    records = cursor.fetchall()
    values = []
    date = []
    for row in records:
        date.append(row[0].strftime('%Y-%m-%d'))
        values.append(row[1])
    return date, values

def getData(x,y):
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    sql_select_Query = "select * from heroku_5e2677edc19745f.weather_storm where datetime BETWEEN %s AND %s"
    cursor = cnx.cursor()
    cursor.execute(sql_select_Query, (x, y))
    # get all records

    records = cursor.fetchall()
    return records

def sugggestion():
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    sql_select_Query = "select * from heroku_5e2677edc19745f.average order by fscore desc limit 3"
    cursor = cnx.cursor()
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


if __name__ == '__main__':
    # port = int(os.environ.get('PORT', 5000))
    # app.run(host='0.0.0.0', port=port)

    app.run()