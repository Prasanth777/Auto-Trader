# Auto-Trader
Auto Trader is a Algo trading bot which automates all the process involved in Intra-day trading.

Running Auto_Trader.py would show a URL. Open the URL in a browser and get the request token. Paste the request token in the prompt. It would start a ticker for Infy by default and stores it in a mysql database.

Default Mysql database details:
Database Name - algo
Table Name - Infy
Columns - date,last_price

Strategy:
Places a buy order when open equal to low or a sell order when open equal to high in a minute ohlc candle
