from Backtest import *
from Analysis import *
from Utility import *

#assets = ["DY0001", "H11001", "NHCI"]
#assets = ["000300", "000905", "CBA00601", "CBA02001", "NHAU", "NHAI", "NHMI", "NHECI"]

assets = ["DY0001", "H11001", "NHCI", "HSI", "SPX", "NHAU"]
funds = dict()
funds["DY0001"] = 10001137
funds["H11001"] = 10000073


es_target = dict()
es_target["DY0001"] = 0.1
es_target["H11001"] = 0.02
es_target["NHCI"] = 0.06
es_target["HSI"] = 0.06
es_target["SPX"] = 0.06
es_target["NHAU"] = 0.06



bond_assets = ["H11001"]

factor_weight = dict()
factor_weight["momentum"] = 1.0
factor_weight["volatility"] = 0.25
factor_weight["corr"] = 0.25

asset_weight_cap = dict()
asset_weight_cap["H11001"] = 0.2

#加载沪深300择时
long_short_flag = pd.read_excel("全A择时.xls")


#portfolio_return, weights_record, risk_budget_record = backtest4(assets, "2013-05-01", "2014-04-30", es_target, bond_assets, 3)
portfolio_return, weights_record, risk_budget_record, weights_record_daily = aggresiveStrategy(assets, "2016-05-01", "2018-04-30", factor_weight, es_target, asset_weight_cap,
                                                                         bond_assets, 3, long_short_flag)
save(portfolio_return, "portfolio_return.xls")
save(weights_record, "weights_record.xls")
save(risk_budget_record, "risk_budget_record.xls")
save(weights_record_daily, "weights_record_daily.xls")



portfolio_return = pd.read_excel("portfolio_return.xls", sheetname="Sheet1")
portfolio_return.set_index("date", inplace=True)


period = list(portfolio_return.index)
period_start_time = period[0].strftime("%Y-%m-%d")
period_end_time = period[-1].strftime("%Y-%m-%d")
index_return = getAssetReturn(assets, period_start_time, period_end_time)
benchmark = pd.DataFrame(index_return.mean(axis=1), columns=["benchmark"])
save(benchmark, "benchmark.xls")


return_data = portfolio_return.merge(benchmark, how="left", left_index = True, right_index = True)
#return_data = return_data.merge(index_return, how="left", left_index = True, right_index = True)
#drawValueCurve(return_data, "对比,png")


drawValueCurve(return_data, "净值曲线.png")
print("策略统计数据：")
portfolio_analysis = portfolioAnalysis(portfolio_return)
print("基准统计数据：")
benchmark_analysis = portfolioAnalysis(benchmark)


'''
index_data = getDailyReturnData(assets, period_start_time, period_end_time)
index_analysis = indexAnalysis(index_data)

analysis_data = index_analysis.merge(pd.DataFrame(portfolio_analysis, columns=["portfolio"]), how="left", left_index = True, right_index = True)
analysis_data = analysis_data.merge(pd.DataFrame(benchmark_analysis, columns=["benchmark"]), how="left", left_index = True, right_index = True)

save(analysis_data, "分析结果.xls")
'''







