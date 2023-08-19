import os
import requests
import pymysql
from pymysql import MySQLError
import json
from deta import Deta

# Your bot's API token
bot_token = os.getenv('BOT_KEY')
db_key = "os.getenv('DB_KEY')"
# Initialize
deta = Deta(db_key)
# This how to connect to or create a database.
drive = deta.Drive("Daily_Data")

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

def fetch_stocks():
    # Fetch data from a URL
    url = 'https://nepsedaily-1-y2743627.deta.app/today'

    response = requests.get(url)

    if response.status_code == 200:
        # Load the JSON data from the response content
        data = response.json()
        with open('test.json', 'w') as json_file:
            json.dump(data, json_file)
        return data
    else:
        # Handle error cases
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

def find_stock_price(code):

    with open('test.json', 'r') as file:
        # Load the JSON data from the file
        data = json.load(file)
    for entry in data['data']:
        company_code = entry['company']['code']
        if company_code == code:
            closing_price = entry['price']['ltp']
            return closing_price

# Send a message using the Telegram Bot API
def send_telegram_message(chat_id, message_text):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {'chat_id': chat_id, 'text': message_text}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        print(f'Message sent to chat_id {chat_id}: {message_text}')
    else:
        print(f'Error sending message to chat_id {chat_id}: {response.status_code} - {response.text}')


try:
    fetch_stocks()
    cursor = connection.cursor()
    # Query the database to get rows where target price is reached
    query1 = "SELECT DISTINCT ticker FROM pricealert"
    query2 = "SELECT chat_id, ticker,alert_price,observable_price,price_difference,alert_id FROM pricealert"
    cursor.execute(query1)
    print('Connected to the MySQL database')
    unique_tickers = [row['ticker'] for row in cursor.fetchall()]
    for ticker in unique_tickers:
        closing_price = find_stock_price(ticker)  # Call your find_stock_price function here
        print(closing_price,ticker)
        # Update observable_price in the database
        update_query = "UPDATE pricealert SET observable_price = %s WHERE ticker = %s"
        cursor.execute(update_query, (closing_price, ticker))
        connection.commit()
    cursor.execute(query2)
    rows = cursor.fetchall()
    for row in rows:
        if row['price_difference'] <=0 and row['alert_id'] ==0:
            if row['observable_price'] <= row['alert_price']:
                # Send message when price_difference is non-negative
                message_text = f'Alert: {ticker} has dropped below the alert price. Current Price: row[\'observable_price\']'
                send_telegram_message(row['chat_id'], message_text)
                # Update alerted status
                update_alerted_query = "UPDATE pricealert SET alert_id = 1 WHERE chat_id = %s AND ticker = %s"
                cursor.execute(update_alerted_query, (row['chat_id'], ticker))
                connection.commit()
            else:
                pass
        elif row['price_difference'] >=0 and row['alert_id'] ==0:
            if row['observable_price']>= row['alert_price']:
                # Send message when price_difference is non-positive
                message_text = f'Alert: {ticker} has reached or exceeded the alert price. Current Price: row[\'observable_price\']'
                send_telegram_message(row['chat_id'], message_text)
                update_alerted_query = "UPDATE pricealert SET alert_id = 1 WHERE chat_id = %s AND ticker = %s"
                cursor.execute(update_alerted_query, (row['chat_id'], ticker))
                connection.commit()
            else:
                pass
except MySQLError as e:
    print(f'Error connecting to the database: {e}')
finally:
    cursor.close()
    connection.close()
    print('Database connection closed')