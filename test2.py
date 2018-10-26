import pandas as pd
from Analysis import *

benchmark = pd.read_excel("D:\Python Project\AssetAllocation\\result\基金\激进\近5年\\benchmark.xls")
benchmark.set_index(keys="trade_date", inplace=True)

portfolio_return1 = pd.read_excel("D:\Python Project\AssetAllocation\\result\基金\激进\近5年\portfolio_return.xls")
portfolio_return1.set_index(keys="date", inplace=True)

portfolio_return2 = pd.read_excel("D:\Python Project\AssetAllocation\\result\基金\稳健\近5年\portfolio_return.xls")
portfolio_return2.set_index(keys="date", inplace=True)

portfolio_return3 = pd.read_excel("D:\Python Project\AssetAllocation\\result\基金\保守\近5年\portfolio_return.xls")
portfolio_return3.set_index(keys="date", inplace=True)

return_data = benchmark.merge(portfolio_return1, how="left", left_index = True, right_index = True)
return_data = return_data.merge(portfolio_return2, how="left", left_index = True, right_index = True)
return_data = return_data.merge(portfolio_return3, how="left", left_index = True, right_index = True)
return_data = return_data.dropna(how='any')

return_data.rename(columns={"benchmark" : "基准", "portfolio_x" : "激进", "portfolio_y" : "稳健", "portfolio" : "保守"}, inplace=True)

fmt = {"基准" : "b-", "激进" : "r-", "稳健" : "y-", "保守" : "g-"}
drawValueCurve(return_data, filename="三种策略对比", show=True, fmt=fmt)