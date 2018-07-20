from Backtest import *
from Analysis import *
from Utility import *

#assets = ["DY0001", "H11001", "NHCI"]
#assets = ["000300", "000905", "CBA00601", "CBA02001", "NHAU", "NHAI", "NHMI", "NHECI"]
assets = ["DY0001", "H11001", "NHCI", "HSI", "SPX", "NHAU"]
es_target = dict()
es_target["DY0001"] = 0.06
es_target["H11001"] = 0.02
es_target["NHCI"] = 0.06
es_target["HSI"] = 0.06
es_target["SPX"] = 0.06
es_target["NHAU"] = 0.06

bond_assets = ["H11001"]

'''
es_target["DY0001"] = 0.06
es_target["H11001"] = 0.02
es_target["NHCI"] = 0.06
bond_assets = ["H11001"]
'''
'''
es_target["000300"] = 0.06
es_target["000905"] = 0.06
es_target["CBA00601"] = 0.02
es_target["CBA02001"] = 0.02
es_target["NHAU"] = 0.06
es_target["NHAI"] = 0.06
es_target["NHMI"] = 0.06
es_target["NHECI"] = 0.06
'''


portfolio_return, weights_record, risk_budget_record = backtest4(assets, "2014-06-01", "2015-06-01", es_target, bond_assets)
save(portfolio_return, "portfolio_return13.xls")
save(weights_record, "weights_record13.xls")
save(risk_budget_record, "risk_budget_record13.xls")


'''
portfolio_return = pd.read_excel("portfolio_return10.xls", sheetname="Sheet1")
portfolio_return.set_index("date", inplace=True)
'''


period = list(portfolio_return.index)
period_start_time = period[0].strftime("%Y-%m-%d")
period_end_time = period[-1].strftime("%Y-%m-%d")
index_return = getAssetReturn(["000300"], period_start_time, period_end_time)
return_data = portfolio_return.merge(index_return, how="left", left_index = True, right_index = True)

drawValueCurve(return_data, "净值曲线13.png")
portfolioAnalysis(portfolio_return)
portfolioAnalysis(index_return)



