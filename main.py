import ccxt
import pandas as pd
import time
import ta
import os
from datetime import datetime

API_KEY = os.getenv("mx0vglwO1s1a7Nchqd")
SECRET_KEY = os.getenv("d35a5ab19444481c976d0761aa3ddd5e")

exchange = ccxt.mexc({
    'apiKey': os.getenv("mx0vglwO1s1a7Nchqd"),
    'secret': os.getenv("d35a5ab19444481c976d0761aa3ddd5e"),
    'enableRateLimit': True
})
symbol = 'ETH/USDC'
timeframe = '1m'
limit = 200
trade_quantity = 0.03

def fetch_data():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def apply_indicators(df):
    df['ema200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['macd_hist'] = ta.trend.macd_diff(df['close'])
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    return df

def check_signals(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    isBullTrend = last['close'] > last['ema200'] and last['ema50'] > last['ema200']
    isBearTrend = last['close'] < last['ema200'] and last['ema50'] < last['ema200']
    bullMomentum = last['rsi'] > 50 and last['macd_hist'] > 0
    bearMomentum = last['rsi'] < 50 and last['macd_hist'] < 0
    atrBreak = last['close'] > prev['close'] + last['atr'] or last['close'] < prev['close'] - last['atr']

    session_high = df['high'][-1440:].max()
    session_low = df['low'][-1440:].min()
    liquidityBreakoutLong = last['close'] > session_high or last['close'] > prev['high']
    liquidityBreakoutShort = last['close'] < session_low or last['close'] < prev['low']

    longCondition = isBullTrend and bullMomentum and atrBreak and liquidityBreakoutLong
    shortCondition = isBearTrend and bearMomentum and atrBreak and liquidityBreakoutShort

    return longCondition, shortCondition

def place_order(side):
    try:
        order = exchange.create_market_order(symbol, side, trade_quantity)
        print(f"[{datetime.now()}] Placed {side.upper()} order: {order}")
    except Exception as e:
        print(f"[{datetime.now()}] Order Error: {str(e)}")

def run_bot():
    print(f"Starting LuxLite Bot on {symbol} ({timeframe})...")
    while True:
        try:
            df = fetch_data()
            df = apply_indicators(df)
            long_signal, short_signal = check_signals(df)

            if long_signal:
                place_order('buy')
            elif short_signal:
                place_order('sell')
            else:
                print(f"[{datetime.now()}] No signal.")

            time.sleep(60)

        except Exception as e:
            print(f"[{datetime.now()}] Runtime Error: {str(e)}")
            time.sleep(30)

run_bot()
