import MetaTrader5 as mt5
from logger import logger
from config import MAGIC_NUMBER

def connect_mt5():
    if not mt5.initialize():
        logger.error("MT5 Initialization Failed")
        return False

    logger.info("MT5 Connected Successfully")
    return True

def shutdown_mt5():
    mt5.shutdown()

def get_candles(symbol, timeframe, count=100):

    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5
    }

    rates = mt5.copy_rates_from_pos(symbol, tf_map[timeframe], 0, count)
    return rates

def place_order(symbol, lot, order_type, sl, tp):

    tick = mt5.symbol_info_tick(symbol)

    if order_type == "BUY":
        price = tick.ask
        mt5_type = mt5.ORDER_TYPE_BUY
    else:
        price = tick.bid
        mt5_type = mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": MAGIC_NUMBER,
        "comment": "EMA Breakout Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    return result

def has_open_trade(symbol):

    positions = mt5.positions_get(symbol=symbol)

    if positions and len(positions) > 0:
        return True

    return False