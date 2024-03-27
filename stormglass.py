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
    #function to calculate the score using graphs I derived
    return score

def binary_search(arr, low, high, x):
    if high >= low:
        mid = (high + low) // 2 #finding the middle index
        if arr[mid] == x: #compare the value in the middle to the value we want to find(x)
            return mid # if found return the middle index
        elif arr[mid] > x: #if the value in the mniddle is greater than x
            return binary_search(arr, low, mid - 1, x) #run the program again but "high" is now "mid -1"
        else:
            return binary_search(arr, mid + 1, high, x) #run the program again but "low" is now "mid+1"
    else:
        return -1 #if not found return -1

response = requests.get(
    'https://api.stormglass.io/v2/weather/point',
    params={
        'lat': 7.873644,
        'lng': 98.414624,
        'params': ','.join(['swellHeight', 'swellPeriod', 'windSpeed']),
    },
    headers={
        'Authorization': 
    }
)
response1 = requests.get(
    'https://api.stormglass.io/v2/astronomy/point',
    params={
        'lat': 7.873644,
        'lng': 98.414624,
    },
    headers={
        'Authorization': 
    }
)

json_data = response.json()
json_data1 = response1.json()


try:
    print("Connecting to mysql database")
    cnx = mysql.connector.connect(host='us-cdbr-east-04.cleardb.com',
                                  user='ba74ba05397a99',
                                  passwd='b48cfd68',
                                  database='heroku_5e2677edc19745f')
    cursor = cnx.cursor()

    delete_weather_data = "delete from heroku_5e2677edc19745f.weather_storm where datetime >= CURDATE()"
    cursor.execute(delete_weather_data)
    cnx.commit()

    my_values = json_extract(response.json(), 'sg') #select data from SG weather station
    time = json_extract(response.json(), 'time') #seperate the datetime from the first request
    my_values1 = json_extract(response1.json(), 'value') #seperate the data from the second request
    times = json_extract(response1.json(), 'time') #seperate the datetime from the second request

    swellHeight = my_values[0::3] #select the 0th position in the list, and every 3 positions after that
    swellPeriod = my_values[1::3] #select the 1st position in the list, and every 3 positions after that
    windSpeed = my_values[2::3] #select the 2nd position in the list, and every 3 positions after that
    moonPhase = my_values1[1::2] #select the 1st position in the list, and every 2 positions after that
    time1 = times[2::3] #select the 2th position in the list, and every 3 positions after that

    score = 0 #declare variable for score
    w: int = 0 #declare variable for index
    data = [] #a list that holds the data to be inserted
    for i in range(len(swellHeight)):
        insert_weather_data = """INSERT INTO heroku_5e2677edc19745f.weather_storm
            (datetime, swellHeight, swellPeriod, windSpeed, moonPhase, score)
            VALUES (%s, %s, %s, %s, %s, %s)"""
        #SQL statement for inserting the retrieved values to corresponding columm in the database
        score = 0
        if time[i] != time1[w]: #if the time in the hourly list is not equal to the time in the daily list
            pass #the index w for moonphase is unchange
        else:
            w += 1 #change the moonphase to the next index

        score = calScore(swellHeight[i], swellPeriod[i], windSpeed[i], moonPhase[w])
        #calculate score for that hour using calScore() function
        val = (time[i], swellHeight[i], swellPeriod[i], windSpeed[i], moonPhase[w], score)
        #hourly values ready to be inserted

        data.append(val) #append the hourly set of data into the data list

    cursor.executemany(insert_weather_data, data)# execute the SQL statment
    cnx.commit()#save the connection
    print("record inserted")


    delete_weather_data = ("delete from heroku_5e2677edc19745f.average where datetime >=SUBDATE(CURDATE(),3)")
    #delete the last 13 days of data in the average table
    cursor.execute(delete_weather_data)
    cnx.commit()

    current_day = datetime.datetime.today() #variable for today's date
    sql_select_Query = "select datetime, score from heroku_5e2677edc19745f.weather_storm where datetime >= SUBDATE(CURDATE(),3)"
    cursor.execute(sql_select_Query) #SQL statement to retrieve the last 13 days of data from the weather_storm table
    records = cursor.fetchall()
    date = []
    values = []
    for row in records:
        date.append(row[0].strftime('%Y-%m-%d')) #seperate the date into this list
        values.append(row[1]) #seperate the score into this list

    current = current_day
    Current_Date_Formatted = current.strftime('%Y-%m-%d')  # format the date to yyyymmdd
    result = 1
    value =[] #list to find average score for the WHOLE day
    while result != len(date): #
        indices = []
        i = result + 24
        while result < i:
            indices.append(result)
            result += 1
            if result == len(date):
                break
        #basically add 24 scores for that day store it in an array, correspond to the date at midnight
        data = [values[index] for index in indices]
        avg = sum(data) / len(data)  # find the average
        val = (date[result - 23], avg)  # date and final score
        value.append(val)  # add to list to be inserted into the table

    insert_weather_data = """INSERT INTO heroku_5e2677edc19745f.average
        (datetime, fscore)
        VALUES (%s, %s)"""

    cursor.executemany(insert_weather_data, value)
    cnx.commit()

except mysql.connector.Error as error:
    print("Failed to insert record into MySQL table {}".format(error))

finally:
    if (cnx.is_connected()):
        cursor.close()
        cnx.close()
        print("MySQL connection is closed")


