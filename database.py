import os
from dotenv import load_dotenv
import pymysql
from pymysql import MySQLError
import datetime

# Load variables from .env file
load_dotenv()

connection = pymysql.connect(
    charset=os.getenv("charset"),
    connect_timeout=int(os.getenv("connect_timeout")),
    cursorclass=pymysql.cursors.DictCursor,
    db=os.getenv("db"),
    host=os.getenv("host"),
    password=os.getenv("password"),
    read_timeout=int(os.getenv("read_timeout")),
    port=int(os.getenv("port")),
    user=os.getenv("user"),
    write_timeout=int(os.getenv("write_timeout")),
)

class DatabaseHandler:
    def __init__(self):
        self.connection = None

    def create_connection(self):
        self.connection = connection

    def close_connection(self):
        if self.connection:
            self.connection.close()

def select_data_by_chat_id(db,chat_id):
    try:
        with db.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT * FROM pricealert WHERE chat_id = %s"
            cursor.execute(query, (chat_id,))
            results = cursor.fetchall()
    except MySQLError as e:
        return f"An error occurred while selecting data: {e}"
        results = []
    return results

def delete_price_alert(alert_id, ticker):
    db = DatabaseHandler()
    try:
        db.create_connection()
        with db.connection.cursor() as cursor:
            query = "DELETE FROM pricealert WHERE chat_id = %s AND ticker = %s"
            affected_rows = cursor.execute(query, (alert_id, ticker))
            db.connection.commit()
            return affected_rows > 0
    except MySQLError as e:
        print(f"An error occurred while deleting the alert: {e}")
        db.connection.rollback()
        return False

def insert_data(db,ticker, create_price, alert_price, chat_id):
    try:
        with db.connection.cursor() as cursor:
            query = "INSERT INTO pricealert (ticker, create_price, alert_price, created_at, chat_id,observable_price, alert_id) VALUES (%s, %s, %s, %s, %s,%s, %s)"
            current_time = datetime.datetime.now()
            values = (ticker, create_price, alert_price, current_time, chat_id,create_price,0)
            cursor.execute(query, values)
            db.connection.commit()
    except MySQLError as e:
        print(f"An error occurred while inserting data: {e}")
        db.connection.rollback()

def is_number(s):
    try:
        float(s)  # for int, long and float
    except ValueError:
        return False

    return True