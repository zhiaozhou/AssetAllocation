from Backtest import *
from Analysis import *
from Utility import *


assets = ["000300", "H11001", "HSI", "SPX", "NHAU"]
funds = dict()
funds["000300"] = 10000957
funds["H11001"] = 10000073
funds["HSI"] = 10001032
funds["SPX"] = 10001416
funds["NHAU"] = 10001411

es_target = dict()
es_target["000300"] = 0.06
es_target["H11001"] = 0.02
es_target["HSI"] = 0.06
es_target["SPX"] = 0.06
es_target["NHAU"] = 0.06



bond_assets = ["H11001"]
ashare_asset = "000300"

factor_weight = dict()
factor_weight["momentum"] = 1.0
factor_weight["volatility"] = 0.5
factor_weight["corr"] = 0.5

asset_weight_cap = dict()
asset_weight_cap["H11001"] = 0.6

start_date = "2016-05-01"
end_date = "2018-04-30"

#加载沪深300择时
long_short_flag = pd.read_excel("全A择时.xls")
portfolio_return, weights_record, risk_budget_record, weights_record_daily = conservativeStrategy(assets, start_date, end_date, factor_weight, es_target, asset_weight_cap,
                                                                         bond_assets, ashare_asset, 3, long_short_flag, mode=1, funds=funds)
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
return_data = return_data.dropna(how='any')


drawValueCurve(return_data, filename="净值曲线.png", show=True)
print("策略统计数据：")
portfolio_analysis = portfolioAnalysis(portfolio_return)
print("基准统计数据：")
benchmark_analysis = portfolioAnalysis(benchmark)