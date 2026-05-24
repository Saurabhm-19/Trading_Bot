import pandas as pd
from openpyxl import load_workbook
from datetime import datetime
from config import EXCEL_FILE

def create_excel():

    try:
        load_workbook(EXCEL_FILE)

    except:
        df = pd.DataFrame(columns=[
            "Trade Number",
            "Symbol",
            "Lot Size",
            "Trade Direction",
            "Entry Price",
            "Stop Loss",
            "Take Profit",
            "Result",
            "Trade Time",
            "Repeat Count"
        ])

        df.to_excel(EXCEL_FILE, index=False)

def add_trade(data):

    df = pd.read_excel(EXCEL_FILE)

    trade_number = len(df) + 1

    new_row = {
        "Trade Number": trade_number,
        "Symbol": data["symbol"],
        "Lot Size": data["lot"],
        "Trade Direction": data["direction"],
        "Entry Price": data["entry"],
        "Stop Loss": data["sl"],
        "Take Profit": data["tp"],
        "Result": "",
        "Trade Time": datetime.now().strftime("%H:%M:%S"),
        "Repeat Count": data["repeat"]
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_excel(EXCEL_FILE, index=False)

    return trade_number

def update_result(trade_number, result):

    df = pd.read_excel(EXCEL_FILE)

    df.loc[df["Trade Number"] == trade_number, "Result"] = result

    df.to_excel(EXCEL_FILE, index=False)