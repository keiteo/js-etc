#!/usr/bin/python

# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py; sleep 1; done

from __future__ import print_function

import sys
import socket
import json

# ~~~~~============== CONFIGURATION  ==============~~~~~
# replace REPLACEME with your team name!
team_name="YOLOLADS"
# This variable dictates whether or not the bot is connecting to the prod
# or test exchange. Be careful with this switch!
test_mode = sys.argv[1] == "dev"

# This setting changes which test exchange is connected to.
# 0 is prod-like
# 1 is slower
# 2 is empty
test_exchange_index=0
prod_exchange_hostname="production"

port=25000 + (test_exchange_index if test_mode else 0)
exchange_hostname = "test-exch-" + team_name if test_mode else prod_exchange_hostname

# ~~~~~============== NETWORKING CODE ==============~~~~~
def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((exchange_hostname, port))
    return s.makefile('rw', 1)

def write_to_exchange(exchange, obj):
    json.dump(obj, exchange)
    exchange.write("\n")

def read_from_exchange(exchange):
    return json.loads(exchange.readline())

# ~~~~~============== SYMBOLS TRACKER ==============~~~
bond = []
valbz = []
vale = []
gs = []
ms = []
wfc = []
xlf = []
order_id = 0

# ~~~~~============== Execution Code ==============~~~~~
def executeOrder(symbol, direction, price, size, exchange): # Direction is BUY or SELL
    global order_id
    jsonObject = {
        "type": "add",
        "order_id": order_id,
        "symbol": symbol,
        "dir": direction,
        "price": price,
        "size": size
    }
    print("JSON OBJECT IS ", jsonObject)
    write_to_exchange(exchange, jsonObject) 
    order_id += 1
    # TODO handle accept and reject

def executeConvert(symbol, direction, size):
    global order_id
    
    jsonObject = {
        "type": "convert",
        "order_id": order_id,
        "symbol" : symbol,
        "dir": direction,
        "size": size
    }
    write_to_exchange(exchange, jsonObject)
    print("Convert for order ", order_id)
    order_id += 1
    
def executeCancel(id):
    jsonObject = {
        "type": "cancel",
        "order_id": id
    } 
    write_to_exchange(exchange, jsonObject)
    print("Cancelled order ", id)
    
# ~~~~~============== Trading strats ==============~~~~~

# if BUY orders > fairvalue, sell as much as possible
# conversely for SELL orders
def bondStrat1(message, exchange):
    fairValue = 1000
    buyArray = message["buy"]
    sellArray = message["sell"]
    buyOrders = {"size": 0, "price":0}
    sellOrders = {"size": 0, "price": 100000000000000000}
    for order in buyArray:
        if order[0] > fairValue:
            sellOrders["size"] += order[1]
            sellOrders["price"] = min(sellOrders["price"], order[0])

    for order in sellArray:
        if order[0] < fairValue:
            buyOrders["size"] += order[1]
            buyOrders["price"] = max(sellOrders["price"], order[0])
    
    # buyOrders.size == 0 XOR sellOrders.size (should be)
    if (sellOrders["size"] > 0):
        executeOrder("BOND", "SELL", sellOrders["price"], sellOrders["size"], exchange)
    if (buyOrders["size"] > 0):
        executeOrder("BOND", "BUY", buyOrders["price"], buyOrders["size"], exchange)

def handleBonds(message, exchange):
    bondStrat1(message, exchange)
    
    

# receives a "book" message to see prices
# message format: {"type":"book","symbol":"SYM","buy":[[PRICE,SIZE], ...],"sell":[...]}
def handleBook(message, exchange):
    if (message["symbol"] == "BOND"):
        handleBonds(message, exchange)
    elif (message["symbol"] =="VALBZ"):
        return
    elif (message["symbol"] =="VALE"):
        return
    elif (message["symbol"] =="GS"):
        return
    elif (message["symbol"] =="MS"):
        return
    elif (message["symbol"] =="WFC"):
        return
    elif (message["symbol"] =="XLF"):
        return

# ~~~~~============== DATA EXTRACTION CODE ==============~~~

# Read trade message and get current valuation for different symbols
def getCurrentValuation(message):
    symbol = message["symbol"]
    if symbol == "BOND":
        bond.append(message["price"])
    elif symbol == "VALBZ":
        valbz.append(message["price"])
    elif symbol == "VALE":
        vale.append(message["price"])
    elif symbol == "GS":
        gs.append(message["price"])
    elif symbol == "MS":
        ms.append(message["price"])
    elif symbol == "WFC":
        wfc.append(message["price"])
    elif symbol == "XLF":
        xlf.append(message["price"])
    else:
        print("Unknown symbol while getting current valuation")

# Extract market data from message
def handleMessage(message, exchange):
    type = message["type"]
    
    if type == "book":
        handleBook(message, exchange)
    elif type == "trade":
        getCurrentValuation(message)
    elif type == "ack":
        print("ACK: ", message)
    elif type == "reject":
        print(message)
    else:
        print("Other message: ", message)

        
# ~~~~~============== MAIN LOOP ==============~~~~~

def main():
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
        if(message["type"] == "close"):
            print("The round has ended")
            break
        
        handleMessage(message, exchange)

if __name__ == "__main__":
    main()