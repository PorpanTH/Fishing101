
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import datetime
from tempfile import mkdtemp
import mysql.connector
from helpers import apology, login_required
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError


def avg():
    cnx = mysql.connector.connect(host='127.0.0.1',
                                  user='root',
                                  passwd='Porpan!12345',
                                  database='weather_schema')

    sql_select_Query = "select * from weather_schema.average"
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


# def binarySearch(arr, x):
#     l = 0
#     r = len(arr)
#     while (l <= r):
#         m = l + ((r - l) // 2)
#
#         res = (x == arr[m])
#
#         # Check if x is present at mid
#         if (res == 0):
#             return m - 1
#
#         # If x greater, ignore left half
#         if (res > 0):
#             l = m + 1
#
#         # If x is smaller, ignore right half
#         else:
#             r = m - 1
#
#     return -1
def binary_search(arr, low, high, x):
    # Check base case
    if high >= low:

        mid = (high + low) // 2

        # If element is present at the middle itself
        if arr[mid] == x:
            return mid

        # If element is smaller than mid, then it can only
        # be present in left subarray
        elif arr[mid] > x:
            return binary_search(arr, low, mid - 1, x)

        # Else the element can only be present in right subarray
        else:
            return binary_search(arr, mid + 1, high, x)

    else:
        # Element is not present in the array
        return -1


Current_Date = datetime.datetime.today()

Current_Date_Formatted = Current_Date.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
NextDay_Date = Current_Date + datetime.timedelta(days=1)
NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')

date, fscores = avg()
result = binary_search(date, 0, len(date), Current_Date_Formatted)
print(Current_Date_Formatted)
print(date)
print(fscores)
print(result)
fscore = fscores[result]
if(date[1] == "2021-09-08"):
    print("SAME")

