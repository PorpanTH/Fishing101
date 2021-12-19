from flask import Flask
from flask_mysqldb import MySQL

app = Flask(__name__)

# app.config['MYSQL_HOST'] = '127.0.0.1'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'Porpan!12345'
# app.config['MYSQL_DB'] = 'weather_schema'
#
# mysql = MySQL(app)
import pymysql

pymysql.install_as_MySQLdb()
import MySQLdb

db = MySQLdb.connect("127.0.0.1", "root", "Porpan!12345", "weather_schema")

cur = db.cursor()
@app.route('/', methods=['GET', 'POST'])
def index():

    cur.execute(''' CREATE TABLE table_name(field1, field2) ''')
    cur.close()
    db.close()
    return 'success'



if __name__ == '__main__':
    app.run(debug=True)