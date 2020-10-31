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

# books will be in the format [[priceOfBuys, sizeOfBUYS], [priceOfSELLS, sizeOfSELLS]]
bondBook = [[], []]
valbzBook = [[], []]
valeBook = [[], []]
gsBook = [[], []]
msBook = [[], []]
wfcBook = [[], []]
xlfBook = [[], []]

bond = []
valbz = []
vale = []
gs = []
ms = []
wfc = []
xlf = []

bondAvg = 0
valbzAvg = 0
valeAvg = 0
gsAvg = 0
msAvg = 0
wfcAvg = 0
xlfAvg = 0

order_id = 0

numberofETFOrder = 0

#valeSum = 0
# valbzBuyAvg = 0
# valbzSellAvg = 0
# valeBuyAvg = 0
# valeSellAvg = 0
# valbzBuSSize = 0
# valbzSellSize = 0
# valeBuySize = 0
# valeSellSize = 0
# valbzBuySum = 0
# valbzSellSum = 0
# valbzBuySum = 0
# valbzSellSize = 0


def mean(arr):
    return sum(arr)//len(arr)

# ~~~~~============== Execution Code ==============~~~~~
def executeOrder(symbol, direction, price, size, exchange): 
    # Direction is BUY or SELL
    global order_id

    if (price): 
        # if price exists. Is buy or sell order
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
    else:
        # price don't exist. Is convert order
        jsonObject = {
            "type": "convert",
            "order_id": order_id,
            "symbol": symbol,
            "dir": direction,
            "size": size
        }
        write_to_exchange(exchange, jsonObject)
        order_id += 1


def executeCancel(id):
    jsonObject = {
        "type": "cancel",
        "order_id": id
    } 
    write_to_exchange(exchange, jsonObject)
    print("Cancelled order ", id)
    
# ~~~~~============== Trading strats ==============~~~~~

# Given a symbol and its (calculated) fairValue,
# the algorithm will fulfill all existing buy/sell orders w.r.t the fairValue input
def executeGenericOrder(symbol, fairValue, exchange, isConvert):
    buyOrders = {"size": 0, "price":0}
    sellOrders = {"size": 0, "price": 100000000000000000}
    bookDict = {
        "BOND": bondBook,
        "VALBZ": valbzBook,
        "VALE": valeBook,
        "GS": gsBook,
        "MS": msBook,
        "WFC": wfcBook,
        "XLF": xlfBook
    }
    targetBook = bookDict[symbol]
    print("Target book is :" , targetBook)
    for order in targetBook[0]: # bond[0] stores the information of BUY prices and sizes from the LATEST BOOK message for BOND
        if order[0] > fairValue:
            sellOrders["size"] += order[1]
            sellOrders["price"] = min(sellOrders["price"], order[0])

    for order in targetBook[1]: # bond[1] stores the information of SELL prices and sizes from the LATEST BOOK message for BOND
        if order[0] < fairValue:
            buyOrders["size"] += order[1]
            buyOrders["price"] = max(buyOrders["price"], order[0])
    
    if (sellOrders["size"] > 0):
        if (isConvert):
            if (symbol == "XLF"):
                if (numberofETFOrder > 0):
                    numberofETFOrder -= 1
                executeOrder(symbol, "SELL", False, 10, exchange)
                return
            executeOrder(symbol, "SELL", False, sellOrders["size"], exchange)
        else:
            executeOrder(symbol, "SELL", sellOrders["price"], sellOrders["size"], exchange)
    if (buyOrders["size"] > 0):
        if (isConvert):
            if (symbol == "XLF"):
                if (numberofETFOrder == 3):
                    return
                numberofETFOrder += 1
                executeOrder(symbol, "BUY", False, 10, exchange)
                return
            executeOrder(symbol, "BUY", False, buyOrders["size"], exchange)
        else:
            executeOrder(symbol, "BUY", buyOrders["price"], buyOrders["size"], exchange) 

# def convertFromVALE(size):
#     global order_id

#     jsonObject = {
#         "type": "convert",
#         "order_id": order_id,
#         "symbol": "VALE",
#         "dir": "BUY",
#         "size": size
#     }
#     write_to_exchange(exchange, jsonObject)
#     print("Convert from VALE ", order_id)
#     order_id += 1

# def convertFromVALBZ(size):
#     global order_id

#     jsonObject = {
#         "type": "convert",
#         "order_id": order_id,
#         "symbol": "VALBZ",
#         "dir": "BUY",
#         "size": size
#     }
#     write_to_exchange(exchange, jsonObject)
#     print("Convert from VALBZ ", order_id)
#     order_id += 1

def getAverage(arr):
    totalPrice = 0
    totalSize = 0
    for entry in arr:
        price = entry[0]
        size = entry[1]
        totalPrice += price * size
        totalSize += size
    return totalPrice / totalSize

# # def executeADRPairStrategy():       
#     global valbzAvg
#     valbzBookBuyAvg = getAverage(valbzBook[0])
#     valbzBookSellAvg = getAverage(valbzBook[1])
#     if (valbzBookBuyAvg >= valbzAvg + 15):
#         executeGenericOrder("VALE", 0, exchange)
#     else

#     fairValue = 
#     executeGenericOrder("VALE", valbzAvg, )     
#     sellOrders = {"size": 0, "price": 1000000000000000} 
#     buyOrders = {"size": 0, "price": 0}
#     for order in valbzBook[0]:
#         if (order[0] >= valbzAvg + 15):
#             sellOrders["size"] += order[1]
#             sellOrders["price"] = min(sellOrders["price"], order[0])
#     for order in valbzBook[1]:
#         if (order[0] <= valbzAvg - 15):
#             buyOrders["size"] += order[1]
#             buyOrders["price"] = max(buyOrders["price"], order[0])
#     if (buyOrders[size] > 0):                
#       executeOrder()
#     if (sellOrders[size] > 0):


# if BUY orders > fairvalue, sell as much as possible
# conversely for SELL orders
def executeBondStrat(exchange):
    executeGenericOrder("BOND", 1000, exchange, False)

    
# Collecting information
# def handleVALBZ(message, exchange):
#     buyArray = message["buy"]
#     sellArray = message["sell"]


def executeXlfStrat(exchange):
    # etcCalculatedFairValue = (3 * bondAvg + 2 * gsAvg + 3 * msAvg + 2 * wfcAvg + 100) // 10 
    bondfair = (bondBook[0][0][0] + bondBook[1][0][0]) / 2
    gsfair = (gsBook[0][0][0] + gsBook[1][0][0]) / 2
    msfair = (msBook[0][0][0] + msBook[1][0][0]) / 2
    wfcfair = (wfcBook[0][0][0] + wfcBook[1][0][0]) / 2
    etcCalculatedFairValue =  (3*bondfair + 2*gsfair + 3*msfair + 2*wfcfair + 100) // 10
    executeGenericOrder("XLF", etcCalculatedFairValue, exchange, False)

# receives a "book" message to see prices
# message format: {"type":"book","symbol":"SYM","buy":[[PRICE,SIZE], ...],"sell":[...]}
def handleBook(message, exchange):
    symbol = message["symbol"]

    buyArray = message["buy"]
    sellArray = message["sell"]

    # Update the corresponding symbolBook to latest from updates from market BOOK message
    if (symbol == "BOND"):
        bondBook[0] = copy.deepcopy(buyArray)
        bondBook[1] = copy.deepcopy(sellArray)
    elif (symbol == "VALBZ"):
        valbzBook[0] = copy.deepcopy(buyArray)
        valbzBook[1] = copy.deepcopy(sellArray)
    elif (symbol == "VALE"):
        valeBook[0] = copy.deepcopy(buyArray)
        valeBook[1] = copy.deepcopy(sellArray)
    elif (symbol == "GS"):
        gsBook[0] = copy.deepcopy(buyArray)
        gsBook[1] = copy.deepcopy(sellArray)
    elif (symbol == "MS"):
        msBook[0] = copy.deepcopy(buyArray)
        msBook[1] = copy.deepcopy(sellArray)
    elif (symbol == "WFC"):
        wfcBook[0] = copy.deepcopy(buyArray)
        wfcBook[1] = copy.deepcopy(sellArray)
    elif (symbol == "XLF"):
        xlfBook[0] = copy.deepcopy(buyArray)
        xlfBook[1] = copy.deepcopy(sellArray)


def execute(exchange):
    try:
        # Perform checks here t determine what order to execute
        # Whether  convert from ADR vie versa
        # TODO executeADRPairStrategy()
        executeXlfStrat(exchange)
        executeBondStrat(exchange) # If no better trades to make
        return
    except Exception as e:
        print("No orders made due to ", e)

    
# ~~~~~============== DATA EXTRACTION CODE ==============~~~

# Read trade message and get current valuation for different symbols
def getCurrentValuation(message):
    symbol = message["symbol"]
    global bondAvg, valbzAvg, valeAvg, gsAvg, msAvg, wfcAvg, xlfAvg
    if symbol == "BOND":
        bond.append(message["price"])
        bondAvg = mean(bond)
    elif symbol == "VALBZ":
        valbz.append(message["price"])
        valbzAvg = mean(valbz)
    elif symbol == "VALE":
        vale.append(message["price"])
        valeAvg = mean(vale)
    elif symbol == "GS":
        gs.append(message["price"])
        gsAvg = mean(gs)
    elif symbol == "MS":
        ms.append(message["price"])
        msAvg = mean(ms)
    elif symbol == "WFC":
        wfc.append(message["price"])
        wfcAvg = mean(wfc)
    elif symbol == "XLF":
        xlf.append(message["price"])
        xlfAvg = mean(xlf)
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
        execute(exchange) # May or may not execute depending certain markers

if __name__ == "__main__":
    main()