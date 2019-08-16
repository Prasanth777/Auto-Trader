# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 01:37:33 2019

@author: prasa
"""
#!/usr/bin/env python3

 #Headers and imports
from kiteconnect import KiteTicker
import logging
from datetime import datetime
import pandas as pd
import time
import schedule
import pymysql
from kiteconnect import KiteConnect

#Ticker Requirements
insert_into_table='insert into Infy(last_price,date) values(%(last_price)s,%(date)s)'
akey=open("C:/Users/prasa/OneDrive/Documents/Auto Traders/api_key.txt","r").read()
kite = KiteConnect(api_key=akey)
skey="07u6cux0e4rw3itxn3j0qm5292k8ngfu"
access_token = open("C:/Users/prasa/OneDrive/Documents/Auto Traders/access_token.txt","r").read()
kws = KiteTicker(akey,access_token)
tokens=[408065]

#Login Module
def login():
    print(kite.login_url())
    rq_token = input("Enter your Request Token here: ")
    tata = kite.generate_session(rq_token, api_secret=skey)
    print(tata) 
    kite.set_access_token(tata["access_token"])
    print(tata["access_token"])
    d = tata["access_token"]
    at = open("access_token.txt","w")
    at.write(d)
    at.close()

#Write ticks to sql db
def insert_ticks(ticks):
    db=pymysql.connect(host='localhost',user='root',password='',database='algo')
    c=db.cursor()
    for Infy in ticks:
        c.execute(insert_into_table,{'last_price':Infy['last_price'],
                                    'date':Infy['timestamp']})
    c.close()
    try:
        db.commit()
    except Exception:
         db.rollback()
    finally:
        db.close()
        
#Logging details
LOG_FILENAME=datetime.now().strftime('Infy_log_%d_%m_%Y.log')
logging.basicConfig(level=logging.INFO,filename=LOG_FILENAME, 
                    format='%(levelname)s %(asctime)s - %(message)s', 
                    filemode='a')
logger=logging.getLogger() 

#Ticker Function Callbacks
def on_ticks(ws, ticks):
    insert_ticks(ticks)
#    print(ticks)
def on_connect(ws, response):
    logging.info("Successfully connected. Response: {}".format(response))
    ws.subscribe(tokens)
    print("Connected")
    ws.set_mode(ws.MODE_FULL,[408065])
    logging.info("Subscribe to tokens in Full mode: {}".format(tokens))
def on_reconnect(ws,attempts_count):
    ws.resubscribe()
    ws.set_mode(ws.MODE_FULL,tokens)
    logging.warning("Reconnecting: {}".format(attempts_count))
def on_error(ws, code, reason):
    print("Error")
    logging.error("Connection error: {code} - {reason}".format(code=code, reason=reason))
def on_close(ws, code, reason):
    print("Close")
    logging.warning("Connection closed: {code} - {reason}".format(code=code, reason=reason))
def on_noreconnect(ws):
    logging.error("Reconnect failed.") 
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close
kws.on_error = on_error
kws.on_reconnect = on_reconnect
kws.on_noreconnect = on_noreconnect

#Convert ticker to minute wise candle
def resample():
    try:
        db=pymysql.connect(host='localhost',user='root',password='',database='algo')
        data=pd.read_sql('select distinct * from infy where date > CURDATE() order by date asc',con=db,parse_dates=True)
    except Exception as e:
        db.close()
        logging.warning("Exeption while reading from sql database:{}".format(str(e)))
        print("Interface Error in pymysql:{}".format(str(e)))
        
    data=data.set_index(['date'])
    ticks=data.loc[:,['last_price']]
    data=ticks['last_price'].resample('1min').ohlc().dropna()
#    data['close']=(data['open']+data['high']+data['close']+data['low'])/4
#    data['open']=(data['open']+data['close'])/2
#    data['high']=data.max(axis=1)
#    data['low']=data.min(axis=1)
#    dataset_test = data.iloc[:,[4,3]]
    return data

#Order placing and strategy module
def order():
    print("Checking for order placement\n")
    dataset_test=resample()
    b_price=0
    if dataset_test.iloc[-1,0] == dataset_test.iloc[-1,2]:
        b_price=dataset_test.iloc[-1,0]
        try:
            order_id = kite.place_order(variety=kite.VARIETY_BO, exchange=kite.EXCHANGE_NSE, tradingsymbol="INFY", transaction_type=kite.TRANSACTION_TYPE_BUY, quantity=10, product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_LIMIT, price=b_price+1, validity=None, disclosed_quantity=None, trigger_price=None, squareoff=1, stoploss=1, trailing_stoploss=0, tag=None)
            logging.info("Order placed. ID is: {}".format(order_id))
            print("Buy Order Placed Row:\n",dataset_test.iloc[-1,:],"\nOrder ID:", order_id)
        except Exception as e:
            logging.warning("Buy Order placement failed:{}".format(str(e)))
    s_price=0       
    if dataset_test.iloc[-1,0] == dataset_test.iloc[-1,1]:
        s_price=dataset_test.iloc[-1,0]
        try:
            order_id = kite.place_order(variety=kite.VARIETY_BO, exchange=kite.EXCHANGE_NSE, tradingsymbol="INFY", transaction_type=kite.TRANSACTION_TYPE_SELL, quantity=10, product=kite.PRODUCT_MIS, order_type=kite.ORDER_TYPE_LIMIT, price=s_price-1, validity=None, disclosed_quantity=None, trigger_price=None, squareoff=1, stoploss=1, trailing_stoploss=0, tag=None)
            logging.info("Order placed. ID is: {}".format(order_id))
            print("Sell Order Placed Row:",dataset_test.iloc[-1,:]," Order ID:", order_id)
        except Exception as e:
            logging.warning("Sell Order placement failed:{}".format(str(e)))
    
#Main Function        
def main():
    try:
        login()
        kws.connect(threaded=True)
    except Exception as e:
        kws.close()
        logging.warning("Exeption while connecting to kite ticker :",str(e))
        print("Connection Closed")
    schedule.every().minutes.at(":00").do(order)
    while True:
        schedule.run_pending()
        time.sleep(1)
        
if __name__ == "__main__":
    main()
    