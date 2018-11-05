
from scipy.stats.mstats import gmean
from Optimizer import *
from Date import *
import empyrical

#取指数日线级别数据，包括收盘价：CLOSE_INDEX，最高价：HIGHEST_INDEX，最低价：LOWEST_INDEX，涨跌幅：CHG_PCT
#mode = 0: 删除none数据， mode = 1: 替换none数据为0
def getDailyIndexData(assets, start_date, end_date, data_type, **kwargs):
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    n = len(assets)
    asset_list = "("
    for i in range(n - 1):
        asset_list = asset_list + "'" + assets[i] + "' ,"

    asset_list = asset_list + "'" + assets[n - 1] + "')"
    selectCommand = "SELECT TICKER_SYMBOL, TRADE_DATE, " + data_type + \
                    " FROM datayesdb.mkt_idxd " \
                    "where ticker_symbol in " + asset_list + " and trade_date >= '" + start_date + "' and trade_date <= '" + end_date + "';"
    cursor.execute(selectCommand)
    index_data = cursor.fetchall()
    index_data = pd.DataFrame(data=list(index_data), columns=["index", "trade_date", data_type])
    index_data["trade_date"] = pd.to_datetime(index_data["trade_date"])
    index_data = index_data.pivot(index="trade_date", columns="index", values=data_type)
    if "mode" not in kwargs.keys():
        index_data = index_data.dropna(how="any")
    else:
        mode = kwargs["mode"]
        if mode == 0:
            index_data = index_data.dropna(how="any")
        else:
            index_data = index_data.fillna(value=0)

    for asset in assets:
        index_data[asset] = index_data[asset].astype(np.double)

    db.close()
    return index_data

#根据日收益率计算资产的净值
def getAssetReturn(assets, start_date, end_date):
    chg_pct = getDailyIndexData(assets, start_date, end_date, "CHG_PCT", mode = 1)
    cum_return = dict()
    for asset in assets:
        cum_return[asset] = empyrical.cum_returns(chg_pct.loc[:, asset], starting_value=1.0)

    cum_return = pd.DataFrame(data=cum_return)
    return cum_return

#获取基金日数据, 包括赋权后净值：ADJ_NAV, 回报率：RETURN_RATE
def getDailyFundData(funds, start_date, end_date, data_type, **kwargs):
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    n = len(funds)
    fund_list = "("
    for i in range(n - 1):
        fund_list = fund_list + "'" + str(funds[i]) + "' ,"

    fund_list = fund_list + "'" + str(funds[n - 1]) + "')"
    selectCommand = "SELECT SECURITY_ID, END_DATE, " + data_type + \
                    " FROM datayesdb.fund_adj_nav " \
                    "where security_id in " + fund_list + " and end_date >= '" + start_date + "' and end_date <= '" + end_date + "';"
    cursor.execute(selectCommand)
    fund_data = cursor.fetchall()
    fund_data = pd.DataFrame(data=list(fund_data), columns=["index", "trade_date", data_type])
    fund_data["trade_date"] = pd.to_datetime(fund_data["trade_date"])
    fund_data = fund_data.pivot(index="trade_date", columns="index", values=data_type)
    if "mode" not in kwargs.keys():
        fund_data = fund_data.dropna(how="any")
    else:
        mode = kwargs["mode"]
        if mode == 0:
            fund_data = fund_data.dropna(how="any")
        else:
            fund_data = fund_data.fillna(value=0)


    for fund in funds:
        fund_data[fund] = fund_data[fund].astype(np.double)

    db.close()
    return fund_data

#取单只货币基金回报率
def getDailyMoneyFundReturn(fund, start_date, end_date, **kwargs):
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()
    selectCommand = "SELECT SECURITY_ID, END_DATE, RETURN_RATE" \
                    " FROM datayesdb.fund_return_rate " \
                    "where security_id = " + str(fund) + " and end_date >= '" + start_date + "' and end_date <= '" + end_date + "';"
    cursor.execute(selectCommand)
    fund_data = cursor.fetchall()
    fund_data = pd.DataFrame(data=list(fund_data), columns=["index", "trade_date", "return_rate"])
    fund_data["trade_date"] = pd.to_datetime(fund_data["trade_date"])
    fund_data = fund_data.pivot(index="trade_date", columns="index", values="return_rate")
    if "mode" not in kwargs.keys():
        fund_data = fund_data.dropna(how="any")
    else:
        mode = kwargs["mode"]
        if mode == 0:
            fund_data = fund_data.dropna(how="any")
        else:
            fund_data = fund_data.fillna(value=0)
    fund_data[fund] = fund_data[fund].astype(np.double)
    db.close()
    return fund_data

#取指数月收盘价，取出的月收盘价包括start_date前一个月的收盘价
def getMonthlyIndexData(assets, start_date, end_date):
    month_end_dates = generateAdjustDate(start_date, end_date)
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    risk_assets = assets.copy()
    if "CASH" in risk_assets:
        risk_assets.remove("CASH")

    n_asset = len(risk_assets)
    asset_list = "("
    for i in range(n_asset - 1):
        asset_list = asset_list + "'" + risk_assets[i] + "' ,"
    asset_list = asset_list + "'" + risk_assets[n_asset - 1] + "')"

    n_month = len(month_end_dates)
    month_end_date_list = "("
    for i in range(n_month - 1):
        month_end_date_list = month_end_date_list + "'" + month_end_dates[i] + "' ,"
    month_end_date_list = month_end_date_list + "'" + month_end_dates[n_month - 1] + "')"

    selectCommand = "SELECT TICKER_SYMBOL, TRADE_DATE, CLOSE_INDEX " \
                    "FROM datayesdb.mkt_idxd " \
                    "where ticker_symbol in " + asset_list + " and trade_date in " + month_end_date_list + ";"

    cursor.execute(selectCommand)
    index_data = cursor.fetchall()
    index_data = pd.DataFrame(data=list(index_data), columns=["index", "trade_date", "close_index"])
    index_data = index_data.pivot(index="trade_date", columns="index", values="close_index")
    index_data = index_data.dropna(how="any")

    for asset in risk_assets:
        index_data[asset] = index_data[asset].astype(np.double)

    db.close()
    return index_data

def getMonthlyIndexData2(assets, month_end_dates):
    # 连接通联mysql数据库
    db = pymysql.connect("172.16.125.32", "reader", "reader", "datayesdb", 3313)
    cursor = db.cursor()

    risk_assets = assets.copy()
    if "CASH" in risk_assets:
        risk_assets.remove("CASH")

    n_asset = len(risk_assets)
    asset_list = "("
    for i in range(n_asset - 1):
        asset_list = asset_list + "'" + risk_assets[i] + "' ,"
    asset_list = asset_list + "'" + risk_assets[n_asset - 1] + "')"

    n_month = len(month_end_dates)
    month_end_date_list = "("
    for i in range(n_month - 1):
        month_end_date_list = month_end_date_list + "'" + month_end_dates[i] + "' ,"
    month_end_date_list = month_end_date_list + "'" + month_end_dates[n_month - 1] + "')"

    selectCommand = "SELECT TICKER_SYMBOL, TRADE_DATE, CLOSE_INDEX " \
                    "FROM datayesdb.mkt_idxd " \
                    "where ticker_symbol in " + asset_list + " and trade_date in " + month_end_date_list + ";"

    cursor.execute(selectCommand)
    index_data = cursor.fetchall()
    index_data = pd.DataFrame(data=list(index_data), columns=["index", "trade_date", "close_index"])
    index_data = index_data.pivot(index="trade_date", columns="index", values="close_index")
    index_data = index_data.dropna(how="any")

    for asset in risk_assets:
        index_data[asset] = index_data[asset].astype(np.double)

    db.close()
    return index_data

#取指数月涨跌幅
def getMonthlyReturnData(index_data):
    assets = index_data.columns
    month_end_dates = index_data.index
    n_asset = len(assets)
    n_month = len(month_end_dates)
    monthly_return_data = np.zeros((n_month - 1, n_asset), dtype=float)
    for i in range(n_asset):
        for j in range(1, n_month):
            prev_month_close = index_data.iat[j - 1, i]
            month_close = index_data.iat[j, i]
            monthly_return_data[j - 1, i] = (month_close - prev_month_close) / prev_month_close

    monthly_return_data = pd.DataFrame(data=monthly_return_data, index=month_end_dates[1:], columns=assets)
    return monthly_return_data

#计算年化收益率
def getExpectedReturn(return_data, **kwargs):
    freq = 'Day'
    if "freq" in kwargs.keys():
        freq = kwargs["freq"]

    if freq == 'Day':
        expected_return = pd.DataFrame(dict(zip(return_data.columns, gmean(return_data + 1.) **250 - 1.)), index=[0], columns=return_data.columns)
    elif freq == 'Week':
        expected_return = pd.DataFrame(dict(zip(return_data.columns, gmean(return_data + 1.) ** 52 - 1.)), index=[0], columns=return_data.columns)
    return expected_return

#计算年化协方差矩阵
def getCovarianceMatrix(return_data, **kwargs):
    freq = 'Day'
    if "freq" in kwargs.keys():
        freq = kwargs["freq"]

    if freq == 'Day':
        covariance_matrix = return_data.cov() * 250.
    elif freq == 'Week':
        covariance_matrix = return_data.cov() * 52.
    return covariance_matrix

#年化波动率
def getAnnualizedVolatility(return_data):
    annualized_volatility = pd.DataFrame(return_data.std() * np.sqrt(250))
    return annualized_volatility

#KAMA预测收益率,对指数涨跌幅用KAMA
def getKAMAExpectedReturn(return_data):
    expected_return = dict()
    assets = list(return_data.columns)
    risk_assets = assets.copy()

    if "CASH" in assets:
        risk_assets.remove("CASH")

    for asset in risk_assets:
        chg_pct = list(return_data.loc[:, asset])
        kama_chg_pct = getKAMA(chg_pct)
        expected_return[asset] = kama_chg_pct[-1] * 250
    expected_return = pd.DataFrame(data=expected_return, index=[0], columns=risk_assets)

    if "CASH" in assets:
        expected_return["CASH"] = 0.03

    return expected_return

#KAMA预测收益率,对指数收盘价用KAMA
def getKAMAExpectedReturn2(index_data):
    expected_return = dict()
    assets = list(index_data.columns)
    risk_assets = assets.copy()

    if "CASH" in assets:
        risk_assets.remove("CASH")

    for asset in risk_assets:
        close_index = list(index_data.loc[:, asset])
        kama_close_index = getKAMA(close_index)
        expected_return[asset] = ((kama_close_index[-1] - kama_close_index[0]) / kama_close_index[0]) * 250 / len(kama_close_index)

    expected_return = pd.DataFrame(data=expected_return, index=[0], columns=risk_assets)

    if "CASH" in assets:
        expected_return["CASH"] = 0.03

    return expected_return

#计算KAMA
def getKAMA(data, **kwargs):
    #设置KAMA参数
    n = 10
    m1 = 5
    m2 = 60

    if 'n' in kwargs.keys():
        n = kwargs['n']

    if 'm1' in kwargs.keys():
        m1 = kwargs['m1']

    if 'm2' in kwargs.keys():
        m2 = kwargs['m2']

    KAMA = data[0 : n]

    for i in range(n, len(data)):
        window = data[i - n + 1 : i + 1]
        direction = window[-1] - window[0]
        volatility = 0
        for j in range(1, n):
            volatility = volatility + abs(window[j] - window[j - 1])
        ER = direction / volatility
        c = (ER * (2 / (m1 + 1) - 2 / (m2 + 1)) + 2 / (m2 + 1)) ** 2
        r = KAMA[-1] + c * (data[i] - KAMA[-1])
        KAMA.append(r)

    '''
    plt.plot(data, 'g-')
    plt.plot(KAMA, 'r-')
    plt.show()
    '''




    return KAMA

#Bayes-Stein预测收益率
#注意：用Bayes-Stein模型预测时，要排除现金资产
def getBayesSteinExpectedReturn(return_data):
    covariance_matrix = getCovarianceMatrix(return_data)
    covariance_matrix_ = np.matrix(covariance_matrix.values)
    try:
        covariance_matrix_I = covariance_matrix_.I
    except:
        print("协方差矩阵为不可逆矩阵，无法求逆")
        return pd.DataFrame()

    N = return_data.shape[1]
    T = return_data.shape[0]
    r_ml = getExpectedReturn(return_data)
    r_ml_ = np.matrix(r_ml.values)
    weight = getMinimumRiskPortfolio(r_ml, covariance_matrix)
    
    #计算最小方差组合的预期收益
    r_minvariance = .0
    assets = list(return_data.columns)
    n_asset = len(assets)
    for asset in assets:
        r_minvariance += r_ml.loc[0, asset] * weight[asset]

    I = np.matrix(np.ones(n_asset))
    r_temp = r_ml_ - r_minvariance * I
    w = (N + 2) / (N + 2 + np.dot(r_temp, np.dot(T * covariance_matrix_I, r_temp.T)))
    r_bs = (1 - w) * r_ml_ + w * r_minvariance * I
    expected_return = pd.DataFrame(dict(zip(assets, r_bs.tolist()[0])), index=[0], columns=assets)
    return expected_return

#计算动量因子(均值定义)
def getMomentum(return_data):
    momentum = pd.DataFrame(return_data.mean(axis=0))
    return momentum

#计算相关性因子
def getCorrelationFactor(return_data):
    corr_matrix = return_data.corr()
    corr_factor = corr_matrix.apply(lambda x: x.sum() - 1, axis=1)
    corr_factor = pd.DataFrame(data=corr_factor)
    return corr_factor

#计算排名， sort_direction = True, 按由小到大的顺序排，=False,按由大到小的顺序排
def getRank(data, sort_direction):
    rank = data.rank(ascending=sort_direction)
    return rank

#计算预期损失
def getExpectedShortfall(return_data, alpha):
    var = np.percentile(return_data, 100 * (1 - alpha))
    es = np.nanmean(return_data[return_data < var])
    if es > 0:
        return 0
    else:
        return -es














