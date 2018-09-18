from Algorithm import *
from Timing import *


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
    #weights_record_daily = pd.DataFrame()
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
            weights_tmp = weights.copy()
            for asset in assets:
                w = weights[asset]
                if asset == "DY0001":
                    if flag == 1:
                        w = w + weights["H11001"] * 0.5
                    else:
                        w = w * 0.5
                    weights_tmp["DY0001"] = w

                if asset == "H11001":
                    if flag == 0:
                        w = w + weights["DY0001"] * 0.5
                    else:
                        w = w * 0.5
                    weights_tmp["H11001"] = w
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])
            #weights_record_daily = weights_record_daily.append(pd.DataFrame(data=weights_tmp, index=[date], columns=assets))

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    '''
    trade_dates = list(weights_record_daily.index)
    long_short_flag = long_short_flag.loc[trade_dates, :]
    long_short_decision_dates = findLongShortDecisionDay(long_short_flag)
    long_short_effect_dates = []
    for date in long_short_decision_dates:
        i = trade_dates.index(date)
        long_short_effect_dates.append(trade_dates[i + 1])

    for i in range(len(long_short_decision_dates)):
        long_short_decision_dates[i] = long_short_decision_dates[i].strftime("%Y-%m-%d")

    long_short_adjust_weights = pd.DataFrame(data = weights_record_daily.loc[long_short_effect_dates, :].values,
                                             index=long_short_decision_dates, columns=assets)
    '''

    '''
    adjust_dates = adjust_dates + long_short_decision_date
    adjust_dates = list(set(adjust_dates))
    adjust_dates.sort()
    '''

    '''
    weights_record2 = weights_record.append(long_short_adjust_weights)
    weights_record2.sort_index(inplace=True)
    '''

    return portfolio_return, weights_record, risk_budget_record


#ES调整后的安信三因子模型+沪深300择时
def aggresiveStrategy(assets, start_date, end_date, factor_weight, es_target, asset_weight_cap, bond_assets, step, long_short_flag, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=step)
    portfolio_return = []
    weights_record = pd.DataFrame()
    weights_record_daily = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, factor_weight, bond=bond_assets)
        risk_budget = getRiskBudget(combined_index, type="dict")

        #风险预算转资产配置权重
        weights = risk_budget.copy()

        #本期风险预算为0的资产，配比也为0
        invest_assets = list(risk_budget.keys())
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0


        # ES调整权重
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 11)
        monthly_index_data = getMonthlyIndexData(assets, predict_base_start_date, adjust_date)
        monthly_return_data = getMonthlyReturnData(monthly_index_data)
        es = dict()
        for asset in assets:
            es[asset] = getExpectedShortfall(monthly_return_data.loc[:, asset], 0.95)
        weights = getESAdjustWeight(weights, es_target, es, bond_assets, 1)
        risk_budget = weights.copy()


        #如果债券的配比超过了上限，超过上限的部分按比例分配到其他非债券资产
        weights_copy = weights.copy()
        equity_assets = [asset for asset in assets if asset not in bond_assets]
        equity_weight_sum = 0
        for equity_asset in equity_assets:
            equity_weight_sum += weights[equity_asset]

        if equity_weight_sum != 0:
            for bond_asset in bond_assets:
                if weights[bond_asset] > asset_weight_cap[bond_asset]:
                    spare_weight = weights[bond_asset] - asset_weight_cap[bond_asset]
                    weights[bond_asset] = asset_weight_cap[bond_asset]
                    for equity_asset in equity_assets:
                        weights[equity_asset] += spare_weight * weights_copy[equity_asset] / equity_weight_sum

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(pd.DataFrame(risk_budget, index=[0], columns=assets))

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

            #根据多空标志调整A股比例，看多A股的话，将债券的配比全部加到A股上，看空A股的话，把A股的占比全部加到其他权益类
            #资产上
            weights_daily = weights.copy()
            if flag == 1:
                total_bond_weight = 0
                for bond_asset in bond_assets:
                    total_bond_weight += weights[bond_asset]
                    weights_daily[bond_asset] = 0
                weights_daily["DY0001"] += total_bond_weight
            else:
                if weights["DY0001"] > 0:
                    spare_weight = weights["DY0001"]
                    weights_daily["DY0001"] = 0
                    equity_assets = [asset for asset in assets if asset not in bond_assets and asset != "DY0001"]
                    equity_weight_sum = 0
                    for equity_asset in equity_assets:
                        equity_weight_sum += weights[equity_asset]
                    if equity_weight_sum > 0:
                        for equity_asset in equity_assets:
                            weights_daily[equity_asset] += spare_weight * weights[equity_asset] / equity_weight_sum
                    #如果其他权益类资产的初始权重均为0，则将A股的权重按比例分配到债券资产上
                    else:
                        total_bond_weight = 0
                        for bond_asset in bond_assets:
                            total_bond_weight += weights[bond_asset]
                        for bond_asset in bond_assets:
                            weights_daily[bond_asset] += spare_weight * weights[bond_asset] / total_bond_weight

            for asset in assets:
                w = weights_daily[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])
            weights_record_daily = weights_record_daily.append(pd.DataFrame(data=weights_daily, index=[date], columns=assets))

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record, weights_record_daily

def neutralStrategy(assets, start_date, end_date, factor_weight, es_target, bond_assets, step, long_short_flag, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=step)
    portfolio_return = []
    weights_record = pd.DataFrame()
    weights_record_daily = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        #取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, factor_weight, bond=bond_assets)
        risk_budget = getRiskBudget(combined_index, type="dict")

        #风险预算转资产配置权重
        weights = risk_budget.copy()

        #本期风险预算为0的资产，配比也为0
        invest_assets = list(risk_budget.keys())
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0


        # ES调整权重
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 11)
        monthly_index_data = getMonthlyIndexData(assets, predict_base_start_date, adjust_date)
        monthly_return_data = getMonthlyReturnData(monthly_index_data)
        es = dict()
        for asset in assets:
            es[asset] = getExpectedShortfall(monthly_return_data.loc[:, asset], 0.95)
        weights = getESAdjustWeight(weights, es_target, es, bond_assets, 1)
        risk_budget = weights.copy()

        #记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index = [0], columns=assets))
        risk_budget_record = risk_budget_record.append(pd.DataFrame(risk_budget, index=[0], columns=assets))

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

            #根据多空标志调整A股比例，看多A股的话，将债券的一半配比加到A股上，看空A股的话，把A股的占比全部加到债券资产上
            weights_daily = weights.copy()
            if flag == 1:
                total_bond_weight = 0
                for bond_asset in bond_assets:
                    total_bond_weight += weights[bond_asset]
                    weights_daily[bond_asset] = 0.5 * weights[bond_asset]
                weights_daily["DY0001"] += total_bond_weight * 0.5
            else:
                if weights["DY0001"] > 0:
                    spare_weight = weights["DY0001"]
                    weights_daily["DY0001"] = 0
                    total_bond_weight = 0
                    for bond_asset in bond_assets:
                        total_bond_weight += weights[bond_asset]
                    for bond_asset in bond_assets:
                        weights_daily[bond_asset] += spare_weight * weights[bond_asset] / total_bond_weight

            for asset in assets:
                w = weights_daily[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])
            weights_record_daily = weights_record_daily.append(pd.DataFrame(data=weights_daily, index=[date], columns=assets))

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record, weights_record_daily

def conservativeStrategy(assets, start_date, end_date, factor_weight, es_target, asset_weight_cap, bond_assets, step, long_short_flag, **kwargs):
    adjust_dates = generateAdjustDate(start_date, end_date, step=step)
    portfolio_return = []
    weights_record = pd.DataFrame()
    weights_record_daily = pd.DataFrame()
    risk_budget_record = pd.DataFrame()

    n = len(adjust_dates)
    for i in range(n):
        adjust_date = adjust_dates[i]
        # 取前6个月数据计算风险预算
        predict_base_start_date = tPrevPeriodStartDate(adjust_date, 5)
        combined_index = getCombinedIndex(assets, predict_base_start_date, adjust_date, factor_weight, bond=bond_assets)
        risk_budget = getRiskBudget(combined_index, type="dict")

        invest_assets = list(risk_budget.keys())

        if len(invest_assets) == 1:
            weights = dict()
            weights[invest_assets[0]] = 1.0
        else:
            # ES调整权重
            predict_base_start_date = tPrevPeriodStartDate(adjust_date, 11)
            monthly_index_data = getMonthlyIndexData(invest_assets, predict_base_start_date, adjust_date)
            monthly_return_data = getMonthlyReturnData(monthly_index_data)
            es = dict()
            for asset in invest_assets:
                es[asset] = getExpectedShortfall(monthly_return_data.loc[:, asset], 0.95)
            risk_budget = getESAdjustWeight(risk_budget, es_target, es, bond_assets, 1)
            risk_budget = pd.DataFrame(data=risk_budget, index = [0], columns=invest_assets)

            daily_return_data = getDailyIndexData(invest_assets, predict_base_start_date, adjust_date, "CHG_PCT")
            daily_return_data = daily_return_data.ix[:, invest_assets]
            covariance_matrix = getCovarianceMatrix(daily_return_data)
            bnds = []
            for asset in invest_assets:
                if asset in asset_weight_cap.keys():
                    bnds.append((0.0, asset_weight_cap[asset]))
                else:
                    bnds.append((0.0, 1.0))
            bnds = tuple(bnds)

            weights = getRiskBugetPortfolio(risk_budget, covariance_matrix, bnds=bnds)

        # 本期风险预算为0的资产，配比也为0
        for asset in assets:
            if asset not in invest_assets:
                weights[asset] = 0
                risk_budget[asset] = 0

        # 记录资产配比
        weights_record = weights_record.append(pd.DataFrame(weights, index=[0], columns=assets))
        risk_budget_record = risk_budget_record.append(pd.DataFrame(risk_budget, index=[0], columns=assets))

        print(adjust_date + "日终计算的下一期资产配置:")
        print(weights)

        # 计算组合净值
        if i == 0:
            period_start_date = start_date
            period_end_date = adjust_dates[i + 1]
        elif i == n - 1:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = end_date
        else:
            period_start_date = tDaysForwardOffset(adjust_date, 1)
            period_end_date = adjust_dates[i + 1]

        if datetime.datetime.strptime(period_start_date, "%Y-%m-%d") > datetime.datetime.strptime(period_end_date,
                                                                                                  "%Y-%m-%d"):
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

            # 根据多空标志调整A股比例，看空A股的话，把A股的占比全部加到债券资产上
            weights_daily = weights.copy()
            if flag == 0:
                if weights["DY0001"] > 0:
                    spare_weight = weights["DY0001"]
                    weights_daily["DY0001"] = 0
                    total_bond_weight = 0
                    for bond_asset in bond_assets:
                        total_bond_weight += weights[bond_asset]
                    for bond_asset in bond_assets:
                        weights_daily[bond_asset] += spare_weight * weights[bond_asset] / total_bond_weight

            for asset in assets:
                w = weights_daily[asset]
                chg_pct = return_data.loc[date, asset]
                net_value = net_value + prev_net_value * w * (1 + chg_pct)
            portfolio_return.append([date, net_value])
            weights_record_daily = weights_record_daily.append(
                pd.DataFrame(data=weights_daily, index=[date], columns=assets))

    portfolio_return = pd.DataFrame(data=portfolio_return, columns=["date", "portfolio"])
    portfolio_return.set_index("date", inplace=True)

    weights_record["adjust_date"] = adjust_dates
    weights_record.set_index("adjust_date", inplace=True)

    risk_budget_record["adjust_date"] = adjust_dates
    risk_budget_record.set_index("adjust_date", inplace=True)

    return portfolio_return, weights_record, risk_budget_record, weights_record_daily








