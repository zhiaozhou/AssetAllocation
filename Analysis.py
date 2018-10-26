# -*- coding: utf-8 -*-
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
from Date import generateAdjustDate
import numpy as np
import pandas as pd
import empyrical
import math

def drawValueCurve(df, **kwargs):
    columns = df.columns
    index = list(df.index)

    #生成横坐标日期
    start_date = datetime.datetime.strftime(index[0], "%Y-%m-%d")
    end_date = datetime.datetime.strftime(index[-1], "%Y-%m-%d")
    adjust_dates = generateAdjustDate(start_date, end_date, step=3)
    adjust_dates = adjust_dates[1 :]
    xticks = []
    for adjust_date in adjust_dates:
        xticks.append(datetime.datetime.strptime(adjust_date, "%Y-%m-%d"))

    mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 用来正常显示中文标签
    fig = plt.figure(figsize=(16, 9))

    if "fmt" in kwargs.keys():
        fmt = kwargs["fmt"]

    for x in columns:
        #plt.plot_date(index, df[x].values, "", xdate=True, ydate=False, label=x)
        if "fmt" in kwargs.keys():
            plt.plot_date(index, df[x].values, fmt=fmt[x], xdate=True, ydate=False, label=x)
        else:
            plt.plot_date(index, df[x].values, "-", xdate=True, ydate=False, label=x)

    plt.xticks(xticks)
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

    plt.legend()
    fig.autofmt_xdate()
    if "filename" in kwargs.keys():
        plt.savefig(kwargs["filename"])
    if "show" in kwargs.keys() and kwargs["show"] == True:
        plt.show()
    return plt.gcf()

def getNonCumReturn(return_data):
    n = len(return_data)
    non_cum_return = np.zeros(n)
    for i in range(n):
        if i == 0:
            non_cum_return[i] = return_data.iloc[i, 0] - 1
        else:
            non_cum_return[i] = (return_data.iloc[i, 0] - return_data.iloc[i - 1, 0]) / return_data.iloc[i - 1, 0]

    non_cum_return = pd.Series(non_cum_return, index=return_data.index)
    return non_cum_return

'''
def getAssetReturn(assets, start_date, end_date):
    close_index = getDailyIndexData(assets, start_date, end_date, 'CLOSE_INDEX')
    pre_close_index = getPreCloseIndex(assets, start_date)
    for asset in close_index.columns:
        close_index[asset] = close_index[asset].apply(lambda x: x / pre_close_index.loc[asset, "pre_close_index"])
    return close_index
'''


'''
def getPreCloseIndex(assets, date):
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.111", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    n = len(assets)
    asset_list = "("
    for i in range(n - 1):
        asset_list = asset_list + "'" + assets[i] + "' ,"
    asset_list = asset_list + "'" + assets[n - 1] + "')"

    selectCommand = "SELECT TICKER_SYMBOL, CLOSE_INDEX " \
                    "FROM datayesdb.mkt_idxd " \
                    "where ticker_symbol in " + asset_list + " and trade_date < '" + date + "' " \
                    "order by trade_date desc " \
                    "limit 1;"
    cursor.execute(selectCommand)
    pre_close_index = cursor.fetchall()
    pre_close_index = pd.DataFrame(data=list(pre_close_index), columns=["index", "pre_close_index"])
    pre_close_index.dropna(how="any")
    pre_close_index.set_index("index", inplace=True)

    pre_close_index["pre_close_index"] = pre_close_index["pre_close_index"].astype(np.double)

    db.close()
    return pre_close_index
'''

def portfolioAnalysis(return_data):
    non_cum_return = getNonCumReturn(return_data)
    #计算年化收益：
    annual_return = empyrical.annual_return(non_cum_return, period='daily')
    #计算年化波动率：
    annual_volatility = empyrical.annual_volatility(non_cum_return, period='daily')
    #计算最大回撤
    max_drawdown = empyrical.max_drawdown(non_cum_return)
    #计算夏普比率：
    sharpe_ratio = empyrical.sharpe_ratio(non_cum_return, risk_free=math.pow(1 + 0.03, 1/250) - 1, period='daily')
    #分年统计
    aggr_returns = empyrical.aggregate_returns(non_cum_return, convert_to="yearly")


    print("年化收益：%f" %(annual_return))
    print("年化波动率：%f" %(annual_volatility))
    print("最大回撤：%f" %(max_drawdown))
    print("夏普比率：%f" %(sharpe_ratio))
    print("分年统计收益率：")
    print(aggr_returns)
    data = [annual_return, annual_volatility, max_drawdown, sharpe_ratio]
    return pd.Series(data, index=["年化收益率", "年化波动率", "最大回撤", "夏普比率"])

def indexAnalysis(index_data):
    assets = index_data.columns
    n_asset = len(assets)
    data = np.zeros((4, n_asset))
    for i in range(n_asset):
        data[0][i] = empyrical.annual_return(index_data.iloc[:, i], period='daily')
        data[1][i] = empyrical.annual_volatility(index_data.iloc[:, i], period='daily')
        data[2][i] = empyrical.max_drawdown(index_data.iloc[:, i])
        data[3][i] = empyrical.sharpe_ratio(index_data.iloc[:, i], risk_free=math.pow(1 + 0.03, 1/250) - 1, period='daily')

    return pd.DataFrame(data, index=["年化收益率", "年化波动率", "最大回撤", "夏普比率"], columns=assets)

def plotWeights(assets, weight):
    fig = plt.figure()
    ax = fig.gca()
    index = np.arange(len(assets))
    bar_width = 0.35

    mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei"]  # 用来正常显示中文标签
    plt.ylim(0.0, 1.0)
    ax.bar(index, weight, bar_width, color = 'b', align='center')
    ax.set_ylabel("权重")
    ax.set_xticks(index)
    ax.set_xticklabels(assets)
    fig.tight_layout()
    plt.show()








    