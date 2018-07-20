# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import empyrical
from datetime import datetime
import matplotlib as mpl
import matplotlib.dates as mdates
from Date import *
from Predict import *


def rate_return(df):
    """
    计算年化收益率
    :param df: pandas.DataFrame
    :return: float
    """
    T = len(df)
    rs = df['net_value'].values
    q = (rs[-1] - rs[0]) / rs[0]
    return (1 + q) ** (250.0 / T)


def r_return(df):
    """
    计算年化总风险
    :param df: pandas.DataFrame
    :return: float
    """
    T = len(df)
    rs = df['net_value'].values
    rvar = np.var(rs)
    q = 250.0 / T
    return np.sqrt(rvar * q)


def draw(df, filename):
    """
    画图
    :param df: pandas.DataFrame
    :return: None
    """
    columns = df.columns
    index = df.index
    fig1, ax = plt.subplots()
    xticks = list(range(0, len(index), 10))
    xlabels = [index[i] for i in xticks]
    xticks.append(len(index))
    xlabels.append(index[-1])
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels, rotation=40)
    for x in columns:
        ax.plot(index, df[x].values, "", label=x)
    plt.legend()
    plt.savefig(filename)
    plt.show()

def drawValueCurve(df, filename):
    columns = df.columns
    index = list(df.index)

    start_date = datetime.datetime.strftime(index[0], "%Y-%m-%d")
    end_date = datetime.datetime.strftime(index[-1], "%Y-%m-%d")
    adjust_dates = generateAdjustDate(start_date, end_date, step=3)
    adjust_dates = adjust_dates[1 :]
    xticks = []
    for adjust_date in adjust_dates:
        xticks.append(datetime.datetime.strptime(adjust_date, "%Y-%m-%d"))

    mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 用来正常显示中文标签
    fig = plt.figure()

    for x in columns:
        plt.plot_date(index, df[x].values, "", xdate=True, ydate=False, label=x)

    plt.xticks(xticks)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

    plt.legend()
    fig.autofmt_xdate()
    plt.savefig(filename)
    plt.show()

def getNonCumReturn(return_data):
    n = len(return_data)
    non_cum_return = np.zeros(n)
    for i in range(n):
        if i == 0:
            non_cum_return[i] = return_data.iloc[i, 0] - 1
        else:
            non_cum_return[i] = (return_data.iloc[i, 0] - return_data.iloc[i - 1, 0]) / return_data.iloc[i - 1, 0]

    non_cum_return = pd.Series(non_cum_return)
    return non_cum_return

def getAssetReturn(assets, start_date, end_date):
    close_index = getDailyIndexData(assets, start_date, end_date)
    pre_close_index = getPreCloseIndex(assets, start_date)
    for asset in close_index.columns:
        close_index[asset] = close_index[asset].apply(lambda x: x / pre_close_index.loc[asset, "pre_close_index"])
    return close_index


def getPreCloseIndex(assets, date):
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.111", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    n = len(assets)
    asset_list = "("
    for i in range(n - 1):
        asset_list = asset_list + "'" + assets[i] + "' ,"
    asset_list = asset_list + "'" + assets[n - 1] + "')"

    selectCommand = "SELECT TICKER_SYMBOL, PRE_CLOSE_INDEX " \
                    "FROM datayesdb.mkt_idxd " \
                    "where ticker_symbol in " + asset_list + " and trade_date = '" + date + "';"
    cursor.execute(selectCommand)
    pre_close_index = cursor.fetchall()
    pre_close_index = pd.DataFrame(data=list(pre_close_index), columns=["index", "pre_close_index"])
    pre_close_index.dropna(how="any")
    pre_close_index.set_index("index", inplace=True)

    pre_close_index["pre_close_index"] = pre_close_index["pre_close_index"].astype(np.double)

    db.close()
    return pre_close_index

def portfolioAnalysis(return_data):
    non_cum_return = getNonCumReturn(return_data)
    #计算年化收益：
    annual_return = empyrical.annual_return(non_cum_return, period='daily')
    #计算年化波动率：
    annual_volatility = empyrical.annual_volatility(non_cum_return, period='daily')
    #计算最大回撤
    max_drawdown = empyrical.max_drawdown(non_cum_return)
    #计算夏普比率：
    sharpe_ratio = empyrical.sharpe_ratio(non_cum_return, risk_free=0, period='daily')
    #分年统计
    #aggr_returns = empyrical.aggregate_returns(non_cum_return, convert_to="yearly")

    print("年化收益：%f" %(annual_return))
    print("年化波动率：%f" %(annual_volatility))
    print("最大回撤：%f" %(max_drawdown))
    print("夏普比率：%f" %(sharpe_ratio))
    #print("分年统计收益率：")
    #print(aggr_returns)




    