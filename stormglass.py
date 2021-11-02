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


try:
    print("Connecting to mysql database")
    cnx = mysql.connector.connect(host='127.0.0.1',
                                  user='root',
                                  passwd='Porpan!12345',
                                  database='weather_schema')
    cursor = cnx.cursor()

    delete_weather_data = "delete from weather_schema.weather_storm where datetime >= CURDATE()"
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
    for i in range(len(swellHeight)):
        insert_weather_data = """INSERT INTO weather_schema.weather_storm
            (datetime, swellHeight, swellPeriod, windSpeed, moonPhase, score)
            VALUES (%s, %s, %s, %s, %s, %s)"""
        score = 0
        if time[i] != time1[w]:
            pass
        else:
            w += 1

        score = calScore(swellHeight[i], swellPeriod[i], windSpeed[i], moonPhase[w])
        val = (time[i], swellHeight[i], swellPeriod[i], windSpeed[i], moonPhase[w], score)
        cursor.execute(insert_weather_data, val)
        cnx.commit()
    print("record inserted")

    delete_weather_data = ("delete from weather_schema.average  where datetime >= CURDATE()")
    cursor.execute(delete_weather_data)
    cnx.commit()

    current_day = datetime.datetime.today()

    for i in range(10):
        sql_select_Query = "select score from weather_schema.weather_storm where datetime BETWEEN %s AND %s"
        current = current_day + datetime.timedelta(days=i)
        Current_Date_Formatted = current.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
        NextDay_Date = current_day + datetime.timedelta(days=i + 1)
        NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')
        cursor.execute(sql_select_Query, (Current_Date_Formatted, NextDay_Date_Formatted))
        records = cursor.fetchall()
        data = []
        for row in records:
            data.append(row[0])
        avg = sum(data) / len(data)
        # print(avg)
        # print(data)

        insert_weather_data = """INSERT INTO weather_schema.average
            (datetime, fscore)
            VALUES (%s, %s)"""
        val = (Current_Date_Formatted, avg)
        cursor.execute(insert_weather_data, val)
        cnx.commit()

    print("Connecting to mysql database")
    cnx = mysql.connector.connect(host='127.0.0.1',
                                  user='root',
                                  passwd='Porpan!12345',
                                  database='weather_schema')
    cursor = cnx.cursor()

    delete_weather_data = ("delete from weather_schema.average  where datetime >= CURDATE()")
    cursor.execute(delete_weather_data)
    cnx.commit()

    current_day = datetime.datetime.today()

    for i in range(10):
        sql_select_Query = "select score from weather_schema.weather_storm where datetime BETWEEN %s AND %s"
        current = current_day + datetime.timedelta(days=i)
        Current_Date_Formatted = current.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
        NextDay_Date = current_day + datetime.timedelta(days=i + 1)
        NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')
        cursor.execute(sql_select_Query, (Current_Date_Formatted, NextDay_Date_Formatted))
        records = cursor.fetchall()
        data = []
        for row in records:
            data.append(row[0])
        avg = sum(data) / len(data)
        # print(avg)
        # print(data)

        insert_weather_data = """INSERT INTO weather_schema.average
            (datetime, fscore)
            VALUES (%s, %s)"""
        val = (Current_Date_Formatted, avg)
        cursor.execute(insert_weather_data, val)
        cnx.commit()




except mysql.connector.Error as error:
    print("Failed to insert record into MySQL table {}".format(error))

finally:
    if (cnx.is_connected()):
        cursor.close()
        cnx.close()
        print("MySQL connection is closed")


