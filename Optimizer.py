import numpy as np
import pandas as pd
import seaborn
from cvxopt import matrix, solvers
from scipy.optimize import minimize
from matplotlib import pyplot as plt
import math

#计算最大效用组合，目标函数：期望年化收益率 - 风险厌恶系数 * 期望年化方差
def getMaximumUtilityPortfolio(expected_return, covariance_matrix, risk_aversion, **kwargs):
    assets = expected_return.columns
    covariance_matrix_ = matrix(covariance_matrix.values)
    expected_return_ = matrix(expected_return.values)
    P = risk_aversion * covariance_matrix_
    q = matrix(-expected_return_.T)

    n_asset = len(assets)

    if 'G' in kwargs.keys():
        G = kwargs['G']
    else:
        G = matrix(np.diag(-1 * np.ones(n_asset)))

    if 'h' in kwargs.keys():
        h = kwargs['h']
    else:
        h = matrix(.0, (n_asset, 1))

    #设置满仓条件
    A = matrix(np.ones(n_asset)).T
    b = matrix([1.0])
    solvers.options['show_progress'] = False
    try:
        sol = solvers.qp(P, q, G, h, A, b)
    except:
        print("Warning: cannot get optimal solution!")
        return
    weights = sol['x']

    #计算优化组合的预期收益率
    expected_return_portfolio = np.dot(expected_return_, weights)
    expected_total_risk = np.sqrt(np.dot(np.dot(weights.T, covariance_matrix_), weights))

    print("最优组合预期收益率：%f" %(expected_return_portfolio))
    print("最优组合预期总风险：%f" %(expected_total_risk))

    weights = dict(zip(assets, weights))

    return weights

#计算有效前沿
def getEfficientFrontier(expected_return, covariance_matrix, n_samples, **kwargs):
    assets = expected_return.columns
    n_asset = len(assets)
    if n_asset < 2:
        raise ValueError("There must be at least 2 assets to calculate the efficient frontier!")

    covariance_matrix_ = matrix(covariance_matrix.values)
    expected_return_ = matrix(expected_return.values)
    risks = []
    returns = []
    weights = []
    for level_return in np.linspace(min(expected_return_), max(expected_return_), n_samples):
        P = covariance_matrix_
        q = matrix(np.zeros(n_asset))

        if 'G' in kwargs.keys():
            G = kwargs['G']
        else:
            G = matrix(np.diag(-1 * np.ones(n_asset)))

        if 'h' in kwargs.keys():
            h = kwargs['h']
        else:
            h = matrix(.0, (n_asset, 1))

        A = matrix(np.row_stack((np.ones(n_asset), expected_return_)))
        b = matrix([1.0, level_return])
        solvers.options['show_progress'] = False
        sol = solvers.qp(P, q, G, h, A, b)
        risks.append(np.sqrt(sol['primal objective']))
        returns.append(level_return)
        weights.append(dict(zip(assets, list(sol['x'].T))))

    efficient_frontier = {"returns": returns,
                          "risks" : risks,
                          "weights" : weights}
    efficient_frontier = pd.DataFrame(efficient_frontier)
    return efficient_frontier

#画有效前沿
def drawEfficientFrontier(efficient_frontier):
    fig = plt.figure(figsize = (7, 4))
    ax = fig.add_subplot(111)
    ax.plot(efficient_frontier['risks'], efficient_frontier['returns'])
    ax.set_title('Efficient Frontier', fontsize = 14)
    ax.set_xlabel('Risk', fontsize = 12)
    ax.set_ylabel('Expected Return', fontsize = 12)
    ax.tick_params(labelsize = 12)
    plt.show()

#计算最大夏普比率组合
def getMaximumSharpePortfolio(efficient_frontier, risk_free_rate):
    n = len(efficient_frontier)
    i = max(range(n), key = lambda x : (efficient_frontier.at[x, "returns"] - risk_free_rate) / efficient_frontier.at[x, "risks"])
    expected_return_portfolio = efficient_frontier.at[i, "returns"]
    expected_total_risk = efficient_frontier.at[i, "risks"]
    weights = efficient_frontier.at[i, "weights"]

    print("最优组合预期收益率：%f" % (expected_return_portfolio))
    print("最优组合预期总风险：%f" % (expected_total_risk))

    return weights

#取一定风险下，最大预期收益率组合
def getMaximumExpectedReturnPortfolio(efficient_frontier, risk_tolerance):
    n = len(efficient_frontier)
    expected_return_portfolio = 0
    expected_total_risk = 0
    weights = dict()
    for i in range(n):
        if efficient_frontier.at[i, "risks"] <= risk_tolerance:
            expected_return = efficient_frontier.at[i, "returns"]
            if expected_return > expected_return_portfolio:
                expected_return_portfolio = expected_return
                expected_total_risk = efficient_frontier.at[i, "risks"]
                weights = efficient_frontier.at[i, "weights"]

    print("最优组合预期收益率：%f" % (expected_return_portfolio))
    print("最优组合预期总风险：%f" % (expected_total_risk))
    return weights


#夏普比率择时模型
def getSharpeTimingPortfolio(expected_return, annualized_volatility, risk_free_rate, sigma):
    assets = list(expected_return.columns)
    n_asset = len(assets)
    sharpe = []
    sum = 0
    for asset in assets:
        r = expected_return.at[0, asset]
        v = annualized_volatility.at[0, asset]
        #现金的夏普比率为0
        if v < 0.0000000001:
            s = 0
        else:
            s = math.pow((r - risk_free_rate) / v, sigma)
            s = max([s, 0])
        sharpe.append(s)
        sum += s

    if sum < 0.0000000001:
        #如果所有除现金外的大类资产夏普比率均小于0，则清仓全部配现金
        weights = dict(zip(assets, np.zeros(n_asset)))
        if "CASH" in assets:
            weights["CASH"] = 1.0
    else:
        weights = dict(zip(assets, [s / sum for s in sharpe]))
    return weights

#计算最小方差组合
def getMinimumRiskPortfolio(expected_return, covariance_matrix, **kwargs):
    assets = list(expected_return.columns)
    n_asset = len(assets)
    if n_asset < 2:
        weights = np.array([1.])
        weights_dict = {assets[0], weights}
    elif "CASH" in assets:
        weights = [0] * n_asset
        weights[assets.index("CASH")] = 1.0
        weights_dict = dict(zip(assets, weights))
    else:
        covariance_matrix_ = matrix(covariance_matrix.values)
        P = covariance_matrix_
        q = matrix(np.zeros(n_asset))

        if 'G' in kwargs.keys():
            G = kwargs['G']
        else:
            G = matrix(np.diag(-1 * np.ones(n_asset)))

        if 'h' in kwargs.keys():
            h = kwargs['h']
        else:
            h = matrix(.0, (n_asset, 1))

        A = matrix(np.ones(n_asset)).T
        b = matrix([1.0])
        solvers.options['show_progress'] = False
        sol = solvers.qp(P, q, G, h, A, b)
        weights = sol['x']
        weights_dict = dict(zip(assets, weights))

        # 计算最小方差组合的预期收益率
        expected_return_ = matrix(expected_return.values)
        expected_return_portfolio = np.dot(expected_return_, weights)
        expected_total_risk = np.sqrt(np.dot(np.dot(weights.T, covariance_matrix_), weights))

        print("最优组合预期收益率：%f" % (expected_return_portfolio))
        print("最优组合预期总风险：%f" % (expected_total_risk))


    return weights_dict

def getRiskBugetPortfolio(risk_budget, covariance_matrix, **kwargs):
    def func(x):
        covariance_matrix_ = matrix(covariance_matrix.values)
        tmp = (covariance_matrix_ * np.matrix(x).T).A1
        risk_contribution = x * tmp
        #total_risk  = np.sqrt(np.dot(np.dot(np.matrix(x), covariance_matrix_), np.matrix(x).T).A1[0])
        risk_budget_ = risk_budget.values[0]
        delta_risk = 0
        n = len(risk_contribution)
        for i in range(n):
            for j in range(n):
                delta_risk += (risk_budget_[j] * risk_contribution[i] - risk_budget_[i] * risk_contribution[j]) ** 2
        return delta_risk / 2


    #设置初始值为等权重
    x0 = np.ones(covariance_matrix.shape[0]) / covariance_matrix.shape[0]

    #设置各大类资产上下限
    if "bnds" not in kwargs.keys():
        bnds = tuple((0.0, 1.0) for x in x0)
    else:
        bnds = kwargs["bnds"]

    #设置限制条件，权重相加等于1
    cons = ({'type' : 'eq', 'fun' : lambda x : sum(x) - 1})

    #设置优化器参数
    options = {'disp' : False, 'maxiter' : 1000, 'ftol' : 1e-20}

    res = minimize(func, x0, bounds=bnds, constraints=cons, method='SLSQP', options=options)

    if res['success'] == False:
        print(res['message'])

    weights = dict(zip(covariance_matrix.index, res['x']))
    return weights
































