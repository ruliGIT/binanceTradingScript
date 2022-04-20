import config
import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'ETHUSD'
TRADE_QUANTITY = 0.05

closes = []
in_position = False

# create a new client
client = Client(config.API_KEY, config.API_SECRET, tld='us')

# order validation (python-binance docs)
def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print(f"an exception occured - {e}")
        return False

    return True

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes
    print('received message')
    json_message = json.loads(message)
    pprint.pprint(json_message)

#Since RSI indicator is being used => only want to know the close of each candlestick
    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']

    if is_candle_closed:
        print(f"candle closed at {close}")
        closes.append(float(close))
        print("closes")
        print(closes)

        #talib works on numpy array
        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("all RSIs calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print(f"the current RSI is {last_rsi}.")  

            if last_rsi > RSI_OVERBOUGHT:
                if in_position:
                    print("Overbought! Sell!")
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = False
                else:
                    print("It is overbought, but you don't own any. Nothing to do.")
                

            if last_rsi < RSI_OVERSOLD:
                if in_position:
                    print("It is oversold, but you already own it. Nothing to do.")
                else:
                    print("Oversold! Buy!") 
                    # put binance buy order logic here  
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        in_position = True    

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()