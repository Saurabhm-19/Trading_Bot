# import pandas as pd

# def calculate_ema(df):

#     df["EMA9"] = df["close"].ewm(span=9, adjust=False).mean()

#     return df

# def check_signal(df):

#     last = df.iloc[-2]
#     current = df.iloc[-1]

#     signal = None

#     # BUY CONDITION
#     if (
#         last["close"] > last["open"]
#         and last["close"] > last["EMA9"]
#         and current["high"] > last["high"]
#     ):

#         entry = current["high"]
#         sl = last["low"]

#         risk = entry - sl
#         tp = entry + (risk * 0.5)

#         signal = {
#             "type": "BUY",
#             "entry": entry,
#             "sl": sl,
#             "tp": tp
#         }

#     # SELL CONDITION
#     elif (
#         last["close"] < last["open"]
#         and last["close"] < last["EMA9"]
#         and current["low"] < last["low"]
#     ):

#         entry = current["low"]
#         sl = last["high"]

#         risk = sl - entry
#         tp = entry - (risk * 0.5)

#         signal = {
#             "type": "SELL",
#             "entry": entry,
#             "sl": sl,
#             "tp": tp
#         }

#     return signal
# This all above is 1st working strategy


#??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????


# =========================
# CONFIGURATION
# =========================

# SYMBOL = "BTCUSDm"
# TIMEFRAME = mt5.TIMEFRAME_M5
# LOT_SIZE = 0.01
# MAGIC_NUMBER = 90920
# DEVIATION = 20
# RISK_REWARD = 0.5
# MAX_OPEN_TRADES = 1
# SCAN_BARS = 100

import MetaTrader5 as mt5
import pandas as pd
import logging
import time
from datetime import datetime



last_candle_time = None

from risk_manager import (
    calculate_lot_size,
    calculate_buy_tp,
    calculate_sell_tp,
    process_closed_trade
)

# =========================================
# CONFIGURATION
# =========================================

SYMBOL = "BTCUSDm"
TIMEFRAME = mt5.TIMEFRAME_M5

MAGIC_NUMBER = 90920
DEVIATION = 20

MAX_OPEN_TRADES = 1
SCAN_BARS = 100

# =========================================
# LOGGING
# =========================================

logging.basicConfig(
    filename="trading_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =========================================
# MT5 CONNECTION
# =========================================

if not mt5.initialize():

    print("MT5 initialization failed")
    quit()

print("MT5 Connected")

# =========================================
# GET MARKET DATA
# =========================================

def get_data(symbol, timeframe, bars=SCAN_BARS):

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        bars
    )

    if rates is None:
        return None

    df = pd.DataFrame(rates)

    df['time'] = pd.to_datetime(
        df['time'],
        unit='s'
    )

    # EMA 9
    df['ema9'] = df['close'].ewm(
        span=9,
        adjust=False
    ).mean()

    # EMA 20
    df['ema20'] = df['close'].ewm(
        span=20,
        adjust=False
    ).mean()

    return df

# =========================================
# MARKET TREND
# =========================================

def market_trend(row):

    close = row['close']
    ema9 = row['ema9']
    ema20 = row['ema20']

    if (
        close > ema9
        and
        close > ema20
        and
        ema9 > ema20
    ):
        return "bullish"

    elif (
        close < ema9
        and
        close < ema20
        and
        ema9 < ema20
    ):
        return "bearish"

    else:
        return "sideways"

# =========================================
# BUY ALERT CANDLE
# =========================================

def is_buy_alert(df, i):

    row = df.iloc[i]
    prev = df.iloc[i - 1]

    green = row['close'] > row['open']

    if not green:
        return False

    ema9 = row['ema9']
    ema20 = row['ema20']

    # EMA CROSS
    cond1 = (
        (
            prev['close'] < prev['ema9']
            and
            row['close'] > ema9
        )
        or
        (
            prev['close'] < prev['ema20']
            and
            row['close'] > ema20
        )
    )

    # RETRACEMENT TOUCH
    cond2 = (
        (
            row['low'] <= ema9 <= row['high']
        )
        or
        (
            row['low'] <= ema20 <= row['high']
        )
    )

    # BOTH EMA INTERCEPT
    cond3 = (
        (
            row['low'] <= ema9 <= row['high']
        )
        and
        (
            row['low'] <= ema20 <= row['high']
        )
    )

    return cond1 or cond2 or cond3

# =========================================
# SELL ALERT CANDLE
# =========================================

def is_sell_alert(df, i):

    row = df.iloc[i]
    prev = df.iloc[i - 1]

    red = row['close'] < row['open']

    if not red:
        return False

    ema9 = row['ema9']
    ema20 = row['ema20']

    # EMA CROSS
    cond1 = (
        (
            prev['close'] > prev['ema9']
            and
            row['close'] < ema9
        )
        or
        (
            prev['close'] > prev['ema20']
            and
            row['close'] < ema20
        )
    )

    # RETRACEMENT TOUCH
    cond2 = (
        (
            row['low'] <= ema9 <= row['high']
        )
        or
        (
            row['low'] <= ema20 <= row['high']
        )
    )

    # BOTH EMA INTERCEPT
    cond3 = (
        (
            row['low'] <= ema9 <= row['high']
        )
        and
        (
            row['low'] <= ema20 <= row['high']
        )
    )

    return cond1 or cond2 or cond3

# =========================================
# COUNT BOT POSITIONS ONLY
# =========================================

def count_bot_positions():

    positions = mt5.positions_get()

    if positions is None:
        return 0

    count = 0

    for pos in positions:

        # ONLY THIS BOT
        if pos.magic != MAGIC_NUMBER:
            continue

        # ONLY THIS SYMBOL
        if pos.symbol != SYMBOL:
            continue

        count += 1

    return count

# =========================================
# PLACE BUY ORDER
# =========================================

def place_buy(entry, sl):

    lot_size = calculate_lot_size(
        SYMBOL,
        entry,
        sl
    )

    tp = calculate_buy_tp(
        SYMBOL,
        entry,
        sl,
        lot_size
    )

    request = {

        "action": mt5.TRADE_ACTION_DEAL,

        "symbol": SYMBOL,

        "volume": lot_size,

        "type": mt5.ORDER_TYPE_BUY,

        "price": entry,

        "sl": sl,

        "tp": tp,

        "deviation": DEVIATION,

        "magic": MAGIC_NUMBER,

        "comment": "EMA_BREAKOUT_BUY",

        "type_time": mt5.ORDER_TIME_GTC,

        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    print("BUY ORDER:", result)

    logging.info(f"BUY ORDER: {result}")

    return result

# =========================================
# PLACE SELL ORDER
# =========================================

def place_sell(entry, sl):

    lot_size = calculate_lot_size(
        SYMBOL,
        entry,
        sl
    )

    tp = calculate_sell_tp(
        SYMBOL,
        entry,
        sl,
        lot_size
    )

    request = {

        "action": mt5.TRADE_ACTION_DEAL,

        "symbol": SYMBOL,

        "volume": lot_size,

        "type": mt5.ORDER_TYPE_SELL,

        "price": entry,

        "sl": sl,

        "tp": tp,

        "deviation": DEVIATION,

        "magic": MAGIC_NUMBER,

        "comment": "EMA_BREAKOUT_SELL",

        "type_time": mt5.ORDER_TIME_GTC,

        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    print("SELL ORDER:", result)

    logging.info(f"SELL ORDER: {result}")

    return result

# =========================================
# MONITOR CLOSED TRADES
# =========================================

processed_deals = set()
BOT_START_TIME = datetime.now()

def monitor_closed_trades():

    from datetime import datetime, timedelta

    start = BOT_START_TIME
    end = datetime.now()

    deals = mt5.history_deals_get(start, end)

    if deals is None:
        return

    for deal in deals:

        # ONLY BOT TRADES
        if deal.magic != MAGIC_NUMBER:
            continue

        # ONLY CLOSED DEALS
        if deal.entry != mt5.DEAL_ENTRY_OUT:
            continue

        # PREVENT DUPLICATES
        if deal.ticket in processed_deals:
            continue

        processed_deals.add(deal.ticket)

        # WIN / LOSS
        if deal.profit > 0:

            print("TRADE RESULT: WIN")

            logging.info("TRADE RESULT: WIN")

            process_closed_trade("W")

        else:

            print("TRADE RESULT: LOSS")

            logging.info("TRADE RESULT: LOSS")

            process_closed_trade("L")

# =========================================
# MAIN STRATEGY
# =========================================

def run_strategy():

    df = get_data(
        SYMBOL,
        TIMEFRAME
    )

    if df is None:
        return

    current = df.iloc[-1]
    
    global last_candle_time

    current_candle_time = current['time']

    if current_candle_time == last_candle_time:
        return

    last_candle_time = current_candle_time

    trend = market_trend(current)
    
    print(f"TREND: {trend}")

    symbol_info = mt5.symbol_info(
        SYMBOL
    )

    spread = symbol_info.spread
    point = symbol_info.point

    # ONLY 1 BOT TRADE
    if count_bot_positions() >= MAX_OPEN_TRADES:
        return

    # =====================================
    # BUY LOGIC
    # =====================================

    if trend == "bullish":

        for i in range(
            len(df) - 4,
            len(df) - 2
        ):

            if is_buy_alert(df, i):

                alert_high = df.iloc[i]['high']
                alert_low = df.iloc[i]['low']

                candle1 = df.iloc[i + 1]
                candle2 = df.iloc[i + 2]

                breakout = (

                    candle1['high'] > alert_high

                    or

                    candle2['high'] > alert_high
                )
                print("BUY ALERT FOUND")
                if breakout:

                    tick = mt5.symbol_info_tick(
                        SYMBOL
                    )

                    entry = tick.ask

                    
                    if "XAU" in SYMBOL:
                        extra_buffer = 2 * point * 10

                    elif "BTC" in SYMBOL or "ETH" in SYMBOL:
                        extra_buffer = 2 * point

                    else:
                        extra_buffer = 2 * point

                    sl = (
                        alert_low
                        -
                        (spread * point)
                        -
                        extra_buffer
                    )

                    result = place_buy(
                        entry,
                        sl
                    )
                    print("BREAKOUT CONFIRMED")
                    if result.retcode == mt5.TRADE_RETCODE_DONE:

                        print("BUY TRADE OPENED")

                    return

    # =====================================
    # SELL LOGIC
    # =====================================

    elif trend == "bearish":

        for i in range(
            len(df) - 4,
            len(df) - 2
        ):

            if is_sell_alert(df, i):

                alert_high = df.iloc[i]['high']
                alert_low = df.iloc[i]['low']

                candle1 = df.iloc[i + 1]
                candle2 = df.iloc[i + 2]

                breakout = (

                    candle1['low'] < alert_low

                    or

                    candle2['low'] < alert_low
                )

                print("SELL ALERT FOUND")
                if breakout:

                    tick = mt5.symbol_info_tick(
                        SYMBOL
                    )

                    entry = tick.bid

                    # dynamic extra margin

                    if "XAU" in SYMBOL:
                        extra_buffer = 2 * point * 10

                    elif "BTC" in SYMBOL or "ETH" in SYMBOL:
                        extra_buffer = 2 * point

                    else:
                        extra_buffer = 2 * point

                    sl = (
                        alert_high
                        +
                        (spread * point)
                        +
                        extra_buffer
                    )

                    result = place_sell(
                        entry,
                        sl
                    )
                    print("BREAKDOWN CONFIRMED")
                    if result.retcode == mt5.TRADE_RETCODE_DONE:

                        print("SELL TRADE OPENED")

                    return

# =========================================
# BOT LOOP
# =========================================

print("BOT STARTED")

while True:

    try:

        run_strategy()

        monitor_closed_trades()

        time.sleep(2)

    except Exception as e:

        print("ERROR:", e)

        logging.error(e)

        time.sleep(5)