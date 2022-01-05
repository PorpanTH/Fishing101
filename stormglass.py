import time
import requests
import mysql.connector
from extract import json_extract
import datetime

def calScore(a, b, c, d):
    score1 = -32.7 * a * a + 69 * a + 51
    score2 = -2.27 * b * b + 26 * b + 2.3
    score3 = -1.5*c*c +4.8*c+ 81
    score4 = -453 * d * d * d + 788 * d * d - 352 * d + 99
    score = (score1 + score2 + score3 + score4)/4
    return score

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

response = requests.get(
    'https://api.stormglass.io/v2/weather/point',
    params={
        'lat': 7.873644,
        'lng': 98.414624,
        'params': ','.join(['swellHeight', 'swellPeriod', 'windSpeed']),
    },
    headers={
        'Authorization': 'c95a4c7a-f811-11eb-862d-0242ac130002-c95a4cf2-f811-11eb-862d-0242ac130002'
    }
)
response1 = requests.get(
    'https://api.stormglass.io/v2/astronomy/point',
    params={
        'lat': 7.873644,
        'lng': 98.414624,
    },
    headers={
        'Authorization': 'c95a4c7a-f811-11eb-862d-0242ac130002-c95a4cf2-f811-11eb-862d-0242ac130002'
    }
)

json_data = response.json()
json_data1 = response1.json()

# print("Connecting to mysql database")
# cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
#                               user='ba74ba05397a99',
#                               passwd='b48cfd68',
#                               database='heroku_5e2677edc19745f')

try:
    print("Connecting to mysql database")
    start_time = time.time()
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    cursor = cnx.cursor()

    delete_weather_data = "delete from heroku_5e2677edc19745f.weather_storm where datetime >= CURDATE()"
    cursor.execute(delete_weather_data)
    cnx.commit()

    my_values = json_extract(response.json(), 'sg')
    time = json_extract(response.json(), 'time')
    my_values1 = json_extract(response1.json(), 'value')
    times = json_extract(response1.json(), 'time')
    swellHeight = my_values[0::3]
    swellPeriod = my_values[1::3]
    windSpeed = my_values[2::3]
    moonPhase = my_values1[1::2]
    time1 = times[2::3]
    score = 0
    w: int = 0
    data = []
    for i in range(len(swellHeight)):
        insert_weather_data = """INSERT INTO heroku_5e2677edc19745f.weather_storm
            (datetime, swellHeight, swellPeriod, windSpeed, moonPhase, score)
            VALUES (%s, %s, %s, %s, %s, %s)"""
        score = 0
        if time[i] != time1[w]:
            pass
        else:
            w += 1

        score = calScore(swellHeight[i], swellPeriod[i], windSpeed[i], moonPhase[w])
        val = (time[i], swellHeight[i], swellPeriod[i], windSpeed[i], moonPhase[w], score)
        data.append(val)
    cursor.executemany(insert_weather_data, data)
    cnx.commit()
    print("record inserted")

    delete_weather_data = ("delete from heroku_5e2677edc19745f.average where datetime >= CURDATE()")
    cursor.execute(delete_weather_data)
    cnx.commit()

    current_day = datetime.datetime.today()
    sql_select_Query = "select datetime, score from heroku_5e2677edc19745f.weather_storm where datetime >= CURDATE()"
    cursor.execute(sql_select_Query)
    records = cursor.fetchall()
    date = []
    values = []
    for row in records:
        date.append(row[0].strftime('%Y-%m-%d'))
        values.append(row[1])

    current = current_day
    Current_Date_Formatted = current.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
    result = 0
    # result = binary_search(date, 0, len(date), Current_Date_Formatted)
    value =[]
    while result != len(date):
        indices = []

        while result < result + 23:
            indices.append(result)
            result += 1
            if result == len(date):
                break

        data = [values[index] for index in indices]
        avg = sum(data) / len(data)
        val = (date[result-23], avg)
        value.append(val)

    insert_weather_data = """INSERT INTO heroku_5e2677edc19745f.average
        (datetime, fscore)
        VALUES (%s, %s)"""
    # val = [Current_Date_Formatted, avg]
    cursor.executemany(insert_weather_data, value)
    cnx.commit()

    # print("--- %s seconds ---" % (time.time() - start_time))

except mysql.connector.Error as error:
    print("Failed to insert record into MySQL table {}".format(error))

finally:
    if (cnx.is_connected()):
        cursor.close()
        cnx.close()
        print("MySQL connection is closed")


