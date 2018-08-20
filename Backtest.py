from datetime import datetime
from Algorithm import *


#固定的风险预算策略，股票：40%，债券：40%，期货：20%
def backtest1(assets, start_date, end_date, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=3)
    portfolio_return = []
    weights_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前250天历史数据作预测
        predict_base_start_date = tDaysBackwardOffset(adjust_date, 249)
        return_data = getDailyReturnData(assets, predict_base_start_date, adjust_date)
        #计算协方差矩阵
        covariance_matrix = getCovarianceMatrix(return_data)
        risk_budget = dict()
        risk_budget["DY0001"] = 0.4
        risk_budget["H11001"] = 0.4
        risk_budget["NHCI"] = 0.2
        risk_budget = pd.DataFrame(data=risk_budget, index=[0], columns=assets)

        #优化得资产配比
        weights = getRiskBugetPortfolio(risk_budget, covariance_matrix)
        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        #计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date, "%Y-%m-%d"):
            continue

        return_data = getDailyReturnData(assets, period_start_date, period_end_date)
        period = return_data.index
        for date in period:
            if len(portfolio_return) == 0:
                prev_net_value = 1
            else:
                prev_net_value = portfolio_return[-1][1]
            net_value = .0
            for asset in assets:
                w = weights[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record

#以安信三因子模型动态调整风险预算,再将动态调整后的风险预算输入到风险预算优化器中
def backtest2(assets, start_date, end_date, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=3)
    portfolio_return = []
    weights_record = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, bond=["H11001"])
        risk_budget = getRiskBudget(combined_index)

        #计算资产的协方差矩阵
        invest_assets = risk_budget.columns
        daily_return_data = getDailyReturnData(invest_assets, predict_base_start_date, adjust_date)
        covariance_matrix = getCovarianceMatrix(daily_return_data)

        #优化得资产配比
        weights = getRiskBugetPortfolio(risk_budget, covariance_matrix)

        #本期风险预算为0的资产，配比也为0
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(risk_budget.loc[:, assets])

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        #计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date, "%Y-%m-%d"):
            continue

        return_data = getDailyReturnData(assets, period_start_date, period_end_date)
        period = return_data.index
        for date in period:
            if len(portfolio_return) == 0:
                prev_net_value = 1
            else:
                prev_net_value = portfolio_return[-1][1]
            net_value = .0
            for asset in assets:
                w = weights[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record

#以安信三因子模型得每期各资产的权重
def backtest3(assets, start_date, end_date, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=3)
    portfolio_return = []
    weights_record = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, bond=["H11001"])
        risk_budget = getRiskBudget(combined_index)

        #风险预算转资产配置权重
        weights = dict()
        for asset in risk_budget.columns:
            weights[asset] = risk_budget.at[0, asset]


        #本期风险预算为0的资产，配比也为0
        invest_assets = risk_budget.columns
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(risk_budget.loc[:, assets])

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        #计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date, "%Y-%m-%d"):
            continue

        return_data = getDailyReturnData(assets, period_start_date, period_end_date)
        period = return_data.index
        for date in period:
            if len(portfolio_return) == 0:
                prev_net_value = 1
            else:
                prev_net_value = portfolio_return[-1][1]
            net_value = .0
            for asset in assets:
                w = weights[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record

#ES调整后的安信三因子模型
def backtest4(assets, start_date, end_date, es_target, bond_assets, step, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=step)
    portfolio_return = []
    weights_record = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, bond=bond_assets)
        risk_budget = getRiskBudget(combined_index)

        #风险预算转资产配置权重
        weights = dict()
        for asset in risk_budget.columns:
            weights[asset] = risk_budget.loc[0, asset]


        #本期风险预算为0的资产，配比也为0
        invest_assets = risk_budget.columns
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0

        #ES调整权重
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 11)
        monthly_index_data = getMonthlyIndexData(assets, predict_base_start_date, adjust_date)
        monthly_return_data = getMonthlyReturnData(monthly_index_data)
        es = dict()
        for asset in assets:
            es[asset] = getExpectedShortfall(monthly_return_data.loc[:, asset], 0.95)
        weights = getESAdjustWeight(weights, es_target, es, bond_assets, 1)

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(risk_budget.loc[:, assets])

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        #计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date, "%Y-%m-%d"):
            continue

        return_data = getDailyReturnData(assets, period_start_date, period_end_date)
        period = return_data.index
        for date in period:
            if len(portfolio_return) == 0:
                prev_net_value = 1
            else:
                prev_net_value = portfolio_return[-1][1]
            net_value = .0
            for asset in assets:
                w = weights[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record

#实验思路2：下行风险替换波动率，不采用因子rank，而是用因子值本身加权
def backtest5(assets, start_date, end_date, es_target, bond_assets, step, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=step)
    portfolio_return = []
    weights_record = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex2(assets, predict_base_start_date, adjust_date, bond=bond_assets)
        risk_budget = getRiskBudget(combined_index, sort_direction=False)

        #风险预算转资产配置权重
        weights = dict()
        for asset in risk_budget.columns:
            weights[asset] = risk_budget.loc[0, asset]


        #本期风险预算为0的资产，配比也为0
        invest_assets = risk_budget.columns
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0

        #ES调整权重
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 11)
        monthly_index_data = getMonthlyIndexData(assets, predict_base_start_date, adjust_date)
        monthly_return_data = getMonthlyReturnData(monthly_index_data)
        es = dict()
        for asset in assets:
            es[asset] = getExpectedShortfall(monthly_return_data.loc[:, asset], 0.95)
        weights = getESAdjustWeight(weights, es_target, es, bond_assets, 1)

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(risk_budget.loc[:, assets])

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        #计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date, "%Y-%m-%d"):
            continue

        return_data = getDailyReturnData(assets, period_start_date, period_end_date)
        period = return_data.index
        for date in period:
            if len(portfolio_return) == 0:
                prev_net_value = 1
            else:
                prev_net_value = portfolio_return[-1][1]
            net_value = .0
            for asset in assets:
                w = weights[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record


#ES调整后的安信三因子模型+沪深300择时
def backtest6(assets, start_date, end_date, es_target, bond_assets, step, long_short_flag, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=step)
    portfolio_return = []
    weights_record = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, bond=bond_assets)
        risk_budget = getRiskBudget(combined_index)

        #风险预算转资产配置权重
        weights = dict()
        for asset in risk_budget.columns:
            weights[asset] = risk_budget.loc[0, asset]


        #本期风险预算为0的资产，配比也为0
        invest_assets = risk_budget.columns
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0

        #ES调整权重
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 11)
        monthly_index_data = getMonthlyIndexData(assets, predict_base_start_date, adjust_date)
        monthly_return_data = getMonthlyReturnData(monthly_index_data)
        es = dict()
        for asset in assets:
            es[asset] = getExpectedShortfall(monthly_return_data.loc[:, asset], 0.95)
        weights = getESAdjustWeight(weights, es_target, es, bond_assets, 1)

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(risk_budget.loc[:, assets])

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        #计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date, "%Y-%m-%d"):
            continue

        return_data = getDailyReturnData(assets, period_start_date, period_end_date)
        period = return_data.index
        for date in period:
            if len(portfolio_return) == 0:
                prev_net_value = 1
            else:
                prev_net_value = portfolio_return[-1][1]
            net_value = .0
            flag = long_short_flag.loc[date, "long_short_flag"]
            for asset in assets:
                w = weights[asset]
                if asset == "DY0001":
                    if flag == 1:
                        w = w + weights["H11001"] * 0.5
                    else:
                        w = w * 0.5

                if asset == "H11001":
                    if flag == 0:
                        w = w + weights["DY0001"] * 0.5
                    else:
                        w = w * 0.5
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record