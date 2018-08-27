import pandas as pd
from Predict import *
from Utility import *
from Analysis import *
assets = ["DY0001", "H11001", "NHCI", "HSI", "SPX", "NHAU"]

'''
portfolio_return = pd.read_excel("D:\Python Project\AssetAllocation\测试结果\安信+激进参数+择时\震荡市\portfolio_return.xls")
portfolio_return.set_index(keys="date", inplace=True)
period = list(portfolio_return.index)
period_start_time = period[0].strftime("%Y-%m-%d")
period_end_time = period[-1].strftime("%Y-%m-%d")
index_return = getAssetReturn(assets, period_start_time, period_end_time)
benchmark = pd.DataFrame(index_return.mean(axis=1), columns=["benchmark"])

save(benchmark, "benchmark震荡市.xls")
'''

return_data = getDailyIndexData(assets, "2012-06-01", "2014-05-31", "CHG_PCT")
index_analysis = indexAnalysis(return_data)
print(index_analysis)