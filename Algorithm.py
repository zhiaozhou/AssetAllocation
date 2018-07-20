from Predict import *
import empyrical

#安信三因子合成，新因子=动量因子 + 波动率因子 * 0.5 + 相关性因子 * 0.5
def getCombinedIndex(assets, start_date, end_date, **kwargs):
    daily_return_data = getDailyReturnData(assets, start_date, end_date)
    monthly_index_data = getMonthlyIndexData(assets, start_date, end_date)
    monthly_return_data = getMonthlyReturnData(monthly_index_data)

    #计算动量因子
    momentum = getMomentum(monthly_return_data)
    #计算波动率因子
    volatility = getAnnualizedVolatility(daily_return_data)
    #计算相关性因子
    corr_factor = getCorrelationFactor(daily_return_data)

    #计算资产的三因子排名
    momentum_rank = getRank(momentum, False)
    volatility_rank = getRank(volatility, True)
    corr_factor_rank = getRank(corr_factor, True)

    combined_index = momentum_rank + 0.5 * volatility_rank + 0.5 * corr_factor_rank

    #过滤掉动量因子为负的资产
    positive_momentum_asset = []
    for asset in momentum.index:
        if momentum.loc[asset, 0] > 0:
            positive_momentum_asset.append(asset)

    if 'bond' in kwargs.keys():
        bond_assets = kwargs['bond']
        for bond_asset in bond_assets:
            if bond_asset not in positive_momentum_asset:
                positive_momentum_asset.append(bond_asset)

    combined_index = combined_index.loc[positive_momentum_asset]

    return combined_index

#按照安信三因子合成因子计算资产风险预算
def getRiskBudget(combined_index, **kwargs):
    index_rank = getRank(combined_index, True)
    assets = list(index_rank.index)
    N = len(assets)
    sum = 0
    for i in range(1, N + 1):
        sum += i
    risk_budget = dict()

    for asset in assets:
        risk_budget[asset] = (N - index_rank.loc[asset] + 1) / sum

    if "type" in kwargs.keys():
        type = kwargs["type"]
        if type == "dict":
            return risk_budget

    risk_budget = pd.DataFrame(data=risk_budget, index = [0], columns=assets)
    return risk_budget

#ES调整三因子合成因子计算的资产配比，bond代表债券资产，type=0：将ES调整后空出的配比分配到债券资产上，type=1：将ES调整后
#空出的配比分配到所有不需要ES调整的资产上
def getESAdjustWeight(weights, es_target, es, bond_assets, type):
    assets = list(weights.keys())
    weights_copy = weights.copy()
    #需要降低配比的资产
    adjust_assets = []
    #不需要降低配比的资产
    non_adjust_assets = []
    for asset in assets:
        if es[asset] > es_target[asset] and asset not in bond_assets:
            adjust_assets.append(asset)
        elif weights[asset] > 0:
            non_adjust_assets.append(asset)

    sum = 0
    if type == 0:
        for asset in bond_assets:
            if weights[asset] > 0:
                sum += weights[asset]
    else:
        for asset in non_adjust_assets:
            sum += weights[asset]

    for asset in adjust_assets:
        weights[asset] = weights[asset] * es_target[asset] / es[asset]
        spare_weight = weights_copy[asset] - weights[asset]
        if type == 0:
            for asset in bond_assets:
                if weights[asset] > 0:
                    weights[asset] += spare_weight * weights_copy[asset] / sum
        else:
            for asset in non_adjust_assets:
                weights[asset] += spare_weight * weights_copy[asset] / sum

    return weights

















