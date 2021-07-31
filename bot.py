#!/usr/bin/python
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json
import copy
from collections import defaultdict, deque

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name = "kmjfcoderz"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = True

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index = 0
prod_exchange_hostname = "production"

port = 25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile("rw", 1)


def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")


def read_from_exchange(exchange):
    return json.loads(exchange.readline())

# ~~~~~============== Symbol and Helper ==============~~~~~

RISK_LIMITS = {
    'BOND': 100,
    'VALBZ': 10,
    'VALE': 10,
    'GS': 100,
    'MS': 100,
    'WFC': 100,
    'XLF': 100
}

BOND_FAIR_VALUE=1000

# Keeps track of 
# Bond = {order_ID : (bidding_price, asking_price)}

basket = {"BOND": 3, "GS": 2, "MS": 3, "WFC": 2}

# Symbol tracker (how many shares currently owned by the bot)
global positions
positions = {'BOND': 0, 'VALBZ': 0, 'VALE': 0, 'GS': 0, 'MS': 0, 'WFC': 0, 'XLF': 0}

global number_orders 
number_orders = {'BUY':0, 'SELL':0}

order_id=0

# books: Dict[str, Book] = keydefaultdict(lambda sym: Book(sym, [], [], []))
# store bid and ask price 
bondBook = [[], []]
valbzBook = [[], []]
valeBook = [[], []]
gsBook = [[], []]
msBook = [[], []]
wfcBook = [[], []]
xlfBook = [[], []]

# security market price
market_price = {
    'BOND': (0,0), 
    'VALBZ': (0,0), 
    'VALE': (0,0), 
    'GS': (0,0), 
    'MS': (0,0), 
    'WFC': (0,0),
    'XLF': (0,0)}

# Store order that is issued from marketplace bot  
bond = []
valbz = []
vale = []
gs = []
ms = []
wfc = []
xlf = []    

# Store current book 
book = {} 

def fair_value (Bid_price, Ask_price):
    return(( Bid_price + Ask_price) / 2)


# Places Order
def place_order(exchange, symbol, order_dir, price, size, order_id):

    
    order_dict={
        "type": "add",
        "order_id":order_id,
        "symbol": symbol,
        "dir": order_dir,
        "price": price,
        "size": size
    }

    print("Placed "+ order_dir + " Order", order_dict)
    write_to_exchange(exchange,order_dict) 
    #order_id+=1


def update_position(info):
    print("position updated  ==============~~~~~ \n", info)


    symbol = info["symbol"]
    direction = info["dir"]
    
    value = positions[symbol]
    
    if direction == "BUY":
        value += info["size"]
    
    elif direction == "SELL":
        value -= info["size"]

    #updates new values  
    positions["symbol"] = value

# This function processes client messages and call corresponding functions
def process_message(message):
    print("message coming in  ==============~~~~~ \n", message)
    if message["type"] == "close":
        print("The round has ended")
        return
        
    elif message["type"] == "book":
        print('Calling Book')
        type_book(message)

    # elif message["type"] == "trade":
    #     fair_value(message)
        
    elif message["type"] == "ack":
        print("ACK: ", message)
        return

    elif message["type"] == "reject":
        print("REJECT: ", message)
        return
        
    elif message["type"] == "fill":
        update_position(message)
        return 
    else:
        print("Other message: ", message)
        return 

def type_book(message):
    symbol = message["symbol"]

    buyArray = message["buy"]
    sellArray = message["sell"]

    # Update the corresponding symbolBook to latest from updates from market BOOK message
    if symbol == "BOND":
        bondBook[0] = copy.deepcopy(buyArray)
        bondBook[1] = copy.deepcopy(sellArray)
    elif symbol == "VALBZ":
        valbzBook[0] = copy.deepcopy(buyArray)
        valbzBook[1] = copy.deepcopy(sellArray)
    elif symbol == "VALE":
        valeBook[0] = copy.deepcopy(buyArray)
        valeBook[1] = copy.deepcopy(sellArray)
    elif symbol == "GS":
        gsBook[0] = copy.deepcopy(buyArray)
        gsBook[1] = copy.deepcopy(sellArray)
    elif symbol == "MS":
        msBook[0] = copy.deepcopy(buyArray)
        msBook[1] = copy.deepcopy(sellArray)
    elif symbol == "WFC":
        wfcBook[0] = copy.deepcopy(buyArray)
        wfcBook[1] = copy.deepcopy(sellArray)
    elif symbol == "XLF":
        xlfBook[0] = copy.deepcopy(buyArray)
        xlfBook[1] = copy.deepcopy(sellArray)


def calculate_XLF(gs_fv, ms_fv, wfc_fv):
    xlf_10_shares_cost = 3*BOND_FAIR_VALUE + 2*gs_fv+3*ms_fv+2*wfc_fv
    xlf_fair_value = xlf_10_shares_cost/10
    return xlf_fair_value

#def execute():
def penny_pinching(book_list, symbol, exchange, order_id):
    print("Book List", book_list)
    
    max_bid = book_list[0][0][0]
    min_ask = book_list[1][0][0]

    print('What is the current max', max_bid,' and min', min_ask)
    print("What are the current shares we have ", positions)
    print("Current number of orders", number_orders)
    
    fair_val=0

    if symbol=="BOND":
        fair_val = 1000
    else:
        fair_val = fair_value(max_bid, min_ask)
        print("Calculated Fair Value: ", fair_val)
    

    if (max_bid < fair_val) and positions[symbol]+3<RISK_LIMITS[symbol]:
        print("Placing Buy order\n")
        place_order(exchange, symbol, "BUY", max_bid, 3, order_id)
    if (min_ask > fair_val) and positions[symbol]-1>(-1*RISK_LIMITS[symbol]):
        print("Placing Sell order\n")
        place_order(exchange, symbol, "SELL",min_ask, 1, order_id)
    
    

# ~~~~~============== MAIN LOOP ==============~~~~~
def main():
    
    order_id=0
    exchange = connect()
    write_to_exchange(exchange, {"type": "hello", "team": team_name.upper()})
    hello_from_exchange = read_from_exchange(exchange)
    # A common mistake people make is to call write_to_exchange() > 1
    # time for every read_from_exchange() response.
    # Since many write messages generate marketdata, this will cause an
    # exponential explosion in pending messages. Please, don't do that!
    print("The exchange replied:", hello_from_exchange, file=sys.stderr)

    while True:
        message = read_from_exchange(exchange)
        print("The exchange replied", message, file=sys.stderr)  
        process_message(message)
    
        if any(bondBook):
            penny_pinching(bondBook,"BOND",exchange,order_id)

        order_id+=1
    
    

if __name__ == "__main__":
    main()
