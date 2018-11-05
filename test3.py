import pandas as pd
from Predict import *
from Utility import *
from Analysis import *
from TimingBacktest import *
from datetime import datetime
#assets = ["DY0001", "H11001", "NHCI", "HSI", "SPX", "NHAU"]
#assets = ["A股", "债券", "期货", "港股", "美股", "黄金"]
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

#plotWeights(assets, [0.250342, 0.0, 0.105921, 0.286105, 0.357642, 0.0])

'''
return_data = getAssetReturn(["DY0001"], "2013-05-02", "2018-04-27")
return_data.rename(columns={"DY0001" : "A股"}, inplace=True)
fig = drawValueCurve(return_data, "通联全A.png")

dates = [datetime.datetime.strptime("2014-06-18", "%Y-%m-%d"), datetime.datetime.strptime("2014-09-03", "%Y-%m-%d"),
         datetime.datetime.strptime("2015-03-13", "%Y-%m-%d"), datetime.datetime.strptime("2015-06-17", "%Y-%m-%d"),
         datetime.datetime.strptime("2015-12-01", "%Y-%m-%d"), datetime.datetime.strptime("2017-06-29", "%Y-%m-%d")]
points = return_data.loc[dates]
plt.plot_date(points.index, points.values, fmt='ro', xdate=True, ydate=False)
plt.show()
'''

'''
funds = [10001416]
fund_data1 = getDailyFundData(funds, "2016-05-01", "2018-04-30", "RETURN_RATE")
fund_data1 = pd.DataFrame(empyrical.cum_returns(fund_data1.loc[:, 10001416], starting_value=1.0))

fund_data2 = getDailyFundData(funds, "2016-05-01", "2018-04-30", "ADJ_NAV")
fund_data2 = fund_data2.apply(lambda x: x / 1.2288)
print("done!")
'''

'''
funds = [10000957, 10000073, 10001032, 10001416, 10001411]
fund_data1 = getDailyFundData(funds, "2016-05-01", "2018-04-30", "RETURN_RATE", mode=1)
print("done!")
'''


'''
asset_return = getAssetReturn(["000300"], '2016-05-01', '2018-04-30')
fund_return = getDailyFundData([10000957], '2016-05-01', '2018-04-30', "RETURN_RATE")
fund_return = pd.DataFrame(data = empyrical.cum_returns(fund_return.loc[:, 10000957], starting_value=1.0), columns=[10000957])
return_data = pd.merge(asset_return, fund_return, how='outer', left_index = True, right_index = True)
return_data = return_data.dropna(how='any')
drawValueCurve(return_data, filename="基金和基准比对")
'''

#trade_date = tDaysBackwardOffset('2018-01-01', 599)
#long_decision_date, short_decision_date,long_short_flag = RSRSBackTest("000300", "2018-01-01", "2018-10-22", 18, 600)
#print("done!")
#adjust_dates = generateAdjustDate2("2018-01-01", "2018-10-12", market="SPX")

'''
adjust_date = '2017-12-29'
tmp = datetime.strptime(adjust_date, "%Y-%m-%d")
month_start_date = datetime(tmp.year, tmp.month, 1)
period_start_date = month_start_date - relativedelta(months=8)
period_start_date = period_start_date.strftime("%Y-%m-%d")
month_end_dates = generateAdjustDate2(period_start_date, adjust_date)
month_end_dates.append(adjust_date)
monthly_index_data = getMonthlyIndexData(["SPX"], month_end_dates)
monthly_average = monthly_index_data.mean()
print("done!")
'''


long_decision_date, short_decision_date,long_short_flag = FaberBackTest("SPX", "2014-01-01", "2018-10-24")
print("done!")




