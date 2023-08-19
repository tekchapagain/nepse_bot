import os
import telebot
import json
import requests
from functools import lru_cache
from database import DatabaseHandler,insert_data, is_number,select_data_by_chat_id,delete_price_alert


API_KEY = os.getenv('BOT_KEY')
bot  = telebot.TeleBot(token =API_KEY,parse_mode='HTML')

@lru_cache(maxsize=100)  # Cache up to 100 different requests
def fetch_stocks():
    try:
        # Fetch data from a URL
        url = 'https://tekchapagain.github.io/nepse_scrapper/data/date/today.json'

        response = requests.get(url)

        if response.status_code == 200:
            # Load the JSON data from the response content
            data = response.json()
            with open('test.json', 'w') as json_file:
                json.dump(data, json_file)
            return data

    except Exception as e:
        # Handle exceptions
        print(f"An error occurred: {e}")
        return None



def fetch_company(company):
     # Fetch data from a URL
    url = f'https://tekchapagain.github.io/nepse_scrapper/data/company/{company}.json'

    response = requests.get(url)

    if response.status_code == 200:
        # Load the JSON data from the response content
        data = response.json()
        return data
    else:
        # Handle error cases
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

#Fetch data from json
def fetch_json():

    with open('test.json', 'r') as file:
        # Load the JSON data from the file
        data = json.load(file)
        return data

def find_stock_price(code):
    data = fetch_json()
    for entry in data['data']:
        company_code = entry['company']['code']
        if company_code == code:
            ltp = entry['price']['ltp']
            return ltp


@bot.message_handler(commands=['start'])
def start(message):
    username = message.chat.first_name
    text = f"Hello {username} I’m <b>NepseBot</b> &#129302;.\n\n<u><b>What I can do for you?</b></u>\n\n<b>&#8226; Send you Price Updates</b>\nGet price updates on stock symbol. Paste stock symbol and i will give you updates on that.\n\n<b>&#8226;Set Price Alerts</b>"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['help'])
def help(message):
    cid = message.chat.id
    text1 = "<u><b>Note</b></u>\n\n&#8226; To add a price alert for your desired stock follow the below commands.\n\n&#8226; You can add a maximum of 3 symbols to your price alert list.\n\n&#8226; Once you have reached the maximum limit on your list you'll have to delete a watchlist to add any more symbol.\n\n&#8226; If you like this project you can support it on <a href='https://www.buymeacoffee.com/tekchapagain'>BuyMeACoffee.</a>"
    text2 = "<b>List of commands</b>\n\n<b>&#8226; /info stocksymbol </b>\nTo see the symbol price update\n\n<b>&#8226; /pricealert SymbolName target_price </b>\nTo Get the Price Alerts"

    bot.send_message(cid, text1, disable_web_page_preview=True)
    bot.send_message(cid, text2, disable_web_page_preview=True)

@bot.message_handler(commands=['info'])
def handle_show_data(message):
    if len(message.text.split(' '))==2:
        _, stock_symbol = message.text.split(' ')
        user_input = stock_symbol.upper()  # Convert user input to uppercase
        data = fetch_company(user_input)
        date = list(data.keys())[-1]
        price = data[date]['price']
        num_trans = data[date]['numTrans']
        traded_shares = data[date]['tradedShares']
        amount = data[date]['amount']

        formatted_message = (
            f"Update as of {date}\n"
            f"Symbol: {user_input}\n"
            f"Open: {price['open']}\n"
            f"High: {price['max']}\n"
            f"Low: {price['min']}\n"
            f"Close: {price['close']}\n"
            f"Previous Close: {price['prevClose']}\n"
            f"Difference: {price['diff']}\n"
            f"Number of Transactions: {num_trans}\n"
            f"Traded Shares: {traded_shares}\n"
            f"Amount: {amount}"
        )

        bot.send_message(message.chat.id, formatted_message)
    else:
        bot.send_message(message.chat.id, "Please provide symbol after /info")


user_preferences = {}

@bot.message_handler(commands=['watchlist'])
def watchlist(message):
    db = DatabaseHandler()
    db.create_connection()
    cid = message.chat.id
    output = "<b>Watchlists:</b> \n\n"
    results = select_data_by_chat_id(db,cid)
    if results:
        active_output = "Currently Active:\n"
        inactive_output = "Inactive:\n"

        for entry in results:
            if entry['alert_id'] == 0:
                active_output += f"Ticker: {entry['ticker']}, Target Price: {entry['alert_price']}\n"
            else:
                inactive_output += f"Ticker: {entry['ticker']}, Target Price: {entry['alert_price']}\n"

        output += active_output
        if "Inactive:" == inactive_output:
            output += "\n" + inactive_output
        text2 = 'Use /delete command to delete an Alert '
    else:
        output = "You don't have alert setup."
        text2 = 'To set Alert use the /alert command.\n<b>Usage:</b> <code>/alert </code>'

    bot.send_message(cid, output)
    bot.send_message(cid, text2)

@bot.message_handler(commands=['alert'])
def main(message):
    db = DatabaseHandler()
    db.create_connection()
    cid = message.chat.id
    data_for_chat_id = select_data_by_chat_id(db,cid)

    if len(data_for_chat_id) >= 3:
        bot.send_message(cid, f'Hi! <b>{message.chat.first_name}</b> Your /watchlist list is full!\nYou can only add 5 alerts')
        return 0

    if len(message.text.split(' ')) == 1:
        echo = bot.reply_to(message,'Enter the Symbol Name or Enter <b>0</b> to cancel the request\n<b>Example:</b> <i>NBL</i>')
        bot.register_next_step_handler(message=echo, callback=lambda message: get_symbol(message, db))
    else:
        bot.reply_to(message,'Hey %s paste a valid symbol in the chat to get started or press /help :)'%(message.chat.first_name))
    

def get_symbol(message,db):
    cid = message.chat.id
    if len(message.text.split(' ')) == 1:
        stock_symbol = message.text
        user_input = stock_symbol.upper()
        # Assuming you have a function find_stock_price(stock_symbol) to find the current price
        current_price = find_stock_price(user_input)
        user_preferences[cid] = {'stock_symbol': user_input,'current_price': current_price}
        bot.reply_to(message, f'Current Price :{current_price}')
        echo = bot.reply_to(message, 'Set a Price Alert for your Symbol or Enter <b>0</b> to cancel the request\n<b>Example:</b> <i>140.99</i>')
        bot.register_next_step_handler(message=echo, callback=lambda message: get_target_price(message, db))

    else:
        bot.reply_to(message, 'Enter a single valid symbol.')

def get_target_price(message,db):
    cid = message.chat.id
    target_price = message.text
    user_data = user_preferences.get(cid, {})
    stock = user_data.get('stock_symbol')
    price = user_data.get('current_price')
    if is_number(message.text):
        if int(message.text) == 0:
            bot.send_message(cid,"Request cancelled.")
        else:
            try:
                insert_data(db,stock, price, target_price, cid)
            except:
                bot.send_message(cid, 'Can\'t set price alert now. Please try again later')
            else:
                bot.send_message(cid,"<b>Successfully added to /watchlist &#129309;</b>\nYou'll recieve a notfication when your Stock reaches the target price.")
    else:
        inline_msg = 'Please enter a numeric value for the price alert (without the currency symbol) or Enter <b>0</b> to cancel the request'
        echo = bot.reply_to(message, inline_msg)
        bot.register_next_step_handler(message=echo, callback=get_target_price)

@bot.message_handler(commands=['delete'])
def delete(message):
    cid = message.chat.id
    if len(message.text.split(' ')) == 1:
        echo = bot.reply_to(message,'Enter the Symbol Name or Enter <b>0</b> to cancel the request\n<b>Example:</b> <i>NBL</i>')
        bot.register_next_step_handler(message=echo, callback=lambda message: delete_watchlist(message, cid))
    else:
        bot.reply_to(message,'Hey %s paste a valid symbol in the chat to get started or press /help :)'%(message.chat.first_name))
    
def delete_watchlist(message,cid):
    db = DatabaseHandler()
    db.create_connection()
    chat_id_data = select_data_by_chat_id(db,cid)
    unique_tickers = [row['ticker'] for row in chat_id_data]
    if is_number(message.text):
        bot.send_message(cid,"Delete request cancelled.")
    else:
        ticker = message.text.upper()
        if ticker in unique_tickers:
            delete_price_alert(cid,ticker)
            bot.send_message(cid, "Your alert is deleted Successfully!")
        else:
            text = 'Symbol not found in your list.\n To Add alert type command\n<b>Usage:</b> <code>/alert </code>\n'
            bot.send_message(cid, text)

# Handle non-command messages
@bot.message_handler(commands=['live'])
def handle_message(message):
    response = "I'm sorry, I don't understand that command.Please type /help for more details."
    bot.send_message(message.chat.id, response)

# Handle non-command messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    response = "I'm sorry, I don't understand that command.Please type /help for more details."
    bot.send_message(message.chat.id, response)

bot.polling()