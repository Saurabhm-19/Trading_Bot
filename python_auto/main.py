import time
import logging
import MetaTrader5 as mt5

logging.basicConfig(
    filename="bot_runtime.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)

from mt5_handler import (
    connect_mt5,
    shutdown_mt5
)

from strategy import (
    run_strategy,
    monitor_closed_trades
)

from excel_handler import (
    create_excel
)

# =========================================
# LOGGING SETUP
# =========================================

logger = logging.getLogger("TRADING_BOT")

logger.setLevel(logging.INFO)

# MAIN BOT LOG FILE
file_handler = logging.FileHandler(
    "bot_runtime.log"
)

file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# =========================================
# MAIN FUNCTION
# =========================================

def main():

    print("===================================")
    print("      EMA BREAKOUT BOT STARTED    ")
    print("===================================")

    logger.info("BOT STARTED")

    # =====================================
    # CREATE EXCEL FILE
    # =====================================

    create_excel()

    logger.info("Excel Handler Initialized")

    # =====================================
    # CONNECT MT5
    # =====================================

    connected = connect_mt5()

    if not connected:

        print("MT5 CONNECTION FAILED")

        logger.error("MT5 CONNECTION FAILED")

        return

    print("MT5 CONNECTED")

    logger.info("MT5 CONNECTED SUCCESSFULLY")

    # =====================================
    # MAIN BOT LOOP
    # =====================================

    while True:

        try:

            # RUN STRATEGY
            run_strategy()

            # CHECK CLOSED TRADES
            monitor_closed_trades()

            # LOOP DELAY
            time.sleep(2)

        except KeyboardInterrupt:

            print("BOT STOPPED MANUALLY")

            logger.info("BOT STOPPED MANUALLY")

            shutdown_mt5()

            break

        except Exception as e:

            print("ERROR:", e)

            logger.error(str(e))

            time.sleep(5)

# =========================================
# START BOT
# =========================================

if __name__ == "__main__":

    main()