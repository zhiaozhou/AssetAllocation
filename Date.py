import pymysql
import pandas as pd
from WindPy import *
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY

#查询该日期前n个交易日的日期，不包含date当日
def tDaysBackwardOffset(date, n, **kwargs):
    if n < 1:
        return ""
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()
    if "market" in kwargs.keys():

        market = kwargs["market"]
        '''
        selectCommand = "SELECT CALENDAR_DATE " \
                        "from md_trade_cal " \
                        "where EXCHANGE_CD='" + market + "' and IS_OPEN=1 and CALENDAR_DATE < '" + date + "'" \
                        "order by CALENDAR_DATE desc " \
                        "limit " + str(n - 1) + ",1;"
        '''
        w.start()
        is_trading_day = w.tdayscount(date, date, "TradingCalendar=" + market).Data[0][0]
        if is_trading_day == 1:
            trade_date = w.tdaysoffset(-n, date, "TradingCalendar=" + market).Data
        else:
            trade_date = w.tdaysoffset(-(n - 1), date, "TradingCalendar=" + market).Data
    else:
        selectCommand = "SELECT CALENDAR_DATE " \
                        "from md_trade_cal " \
                        "where EXCHANGE_CD='XSHG' and IS_OPEN=1 and CALENDAR_DATE < '" + date + "'" \
                        "order by CALENDAR_DATE desc " \
                        "limit " + str(n - 1) + ",1;"
        cursor.execute(selectCommand)
        trade_date = cursor.fetchall()
        db.close()

    trade_date = trade_date[0][0].strftime("%Y-%m-%d")
    return trade_date

#查询该日期后n个交易日的日期
def tDaysForwardOffset(date, n):
    if n < 1:
        return ""
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()
    selectCommand = "SELECT CALENDAR_DATE " \
                    "from md_trade_cal " \
                    "where EXCHANGE_CD='XSHG' and IS_OPEN=1 and CALENDAR_DATE > '" + date + "'" \
                    "order by CALENDAR_DATE asc " \
                    "limit " + str(n - 1) + ",1;"
    cursor.execute(selectCommand)
    trade_date = cursor.fetchall()
    trade_date = trade_date[0][0].strftime("%Y-%m-%d")
    db.close()
    return trade_date

#查询该日期所在月份第一个交易日
def tMonthStartDate(date):
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()
    selectCommand = "SELECT MONTH_START_DATE " \
                    "from md_trade_cal " \
                    "where EXCHANGE_CD='XSHG' and CALENDAR_DATE = '" + date + "';"
    cursor.execute(selectCommand)
    month_start_date = cursor.fetchall()
    month_start_date = month_start_date[0][0].strftime("%Y-%m-%d")
    db.close()
    return month_start_date

#查询该日期前一个交易日的日期
def tPrevTradeDate(date):
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()
    selectCommand = "SELECT PREV_TRADE_DATE " \
                    "from md_trade_cal " \
                    "where EXCHANGE_CD='XSHG' and CALENDAR_DATE = '" + date + "';"
    cursor.execute(selectCommand)
    prev_trade_date = cursor.fetchall()
    prev_trade_date = prev_trade_date[0][0].strftime("%Y-%m-%d")
    db.close()
    return prev_trade_date

#适用于A股和港股，不适用于美股
def generateAdjustDate(start_date, end_date, **kwargs):
    adjust_dates = []
    month_start_date = tMonthStartDate(start_date)
    setup_date = tPrevTradeDate(month_start_date)
    adjust_dates.append(setup_date)

    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    market = "XSHG"
    if "market" in kwargs.keys():
        market = kwargs["market"]
    selectCommand = "SELECT distinct(MONTH_END_DATE) " \
                    "from md_trade_cal " \
                    "where EXCHANGE_CD='" + market +"' and IS_OPEN=1 and CALENDAR_DATE >= '" + start_date + "' and CALENDAR_DATE <= '" + end_date + "' and MONTH_END_DATE <= '" + end_date + "';"
    cursor.execute(selectCommand)
    month_end_date = cursor.fetchall()
    month_end_date = pd.DataFrame(data=list(month_end_date), columns=["date"])
    month_end_date.sort_values(by = "date", ascending = True, inplace = True)
    n = len(month_end_date)

    step = 1
    if "step" in kwargs.keys():
        step = kwargs["step"]

    for i in range(step - 1, n, step):
        adjust_dates.append(month_end_date.iloc[i, 0].strftime("%Y-%m-%d"))
    db.close()
    return adjust_dates

#生成美股的调仓日
def generateAdjustDate2(start_date, end_date, **kwargs):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    tmp = datetime(start_date.year, start_date.month, 1)
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    month_start_dates = list(rrule(freq=MONTHLY, dtstart=tmp, until=end_date))
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()
    adjust_dates = []
    market = "SPX"
    if "market" in kwargs.keys():
        market = kwargs["market"]
    for month_start_date in month_start_dates:
        month_start_date = month_start_date.strftime("%Y-%m-%d")
        selectCommand = "SELECT trade_date " + \
                        "FROM datayesdb.mkt_idxd " + \
                        "where ticker_symbol = '" + market + "' and trade_date < '" + month_start_date + "' " + \
                        "order by trade_date desc limit 1;"
        cursor.execute(selectCommand)
        adjust_date = cursor.fetchall()
        adjust_dates.append(adjust_date[0][0].strftime("%Y-%m-%d"))
    db.close();
    return adjust_dates






















def tPrevPeriodStartDate(date, step):
    month_start_date = tMonthStartDate(date)
    prev_period_end_date = tPrevTradeDate(month_start_date)
    prev_period_start_date = month_start_date
    for i in range(step):
        prev_period_start_date = tMonthStartDate(prev_period_end_date)
        prev_period_end_date = tPrevTradeDate(prev_period_start_date)

    return prev_period_start_date













