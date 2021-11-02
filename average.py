import mysql.connector
import datetime


print("Connecting to mysql database")
cnx = mysql.connector.connect(host='127.0.0.1',
                              user='root',
                              passwd='Porpan!12345',
                              database='weather_schema')
cursor = cnx.cursor()

delete_weather_data = ("delete from weather_schema.average  where datetime >= CURDATE()")
cursor.execute(delete_weather_data)
cnx.commit()

current_day=datetime.datetime.today()

for i in range(8):
    sql_select_Query = "select score from weather_schema.weather_storm where datetime BETWEEN %s AND %s"
    current = current_day + datetime.timedelta(days=i)
    Current_Date_Formatted = current.strftime('%Y-%m-%d')  # format the date to ddmmyyyy
    NextDay_Date = current_day + datetime.timedelta(days=i+1)
    NextDay_Date_Formatted = NextDay_Date.strftime('%Y-%m-%d')
    cursor.execute(sql_select_Query, (Current_Date_Formatted, NextDay_Date_Formatted))
    records = cursor.fetchall()
    data = []
    for row in records:
        data.append(row[0])
    avg = sum(data)/len(data)
    # print(avg)
    # print(data)

    insert_weather_data = """INSERT INTO weather_schema.average
        (datetime, fscore)
        VALUES (%s, %s)"""
    val = (Current_Date_Formatted, avg)
    cursor.execute(insert_weather_data, val)
    cnx.commit()

