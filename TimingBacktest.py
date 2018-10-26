from Timing import *
from Analysis import *
import empyrical
def RSRSBackTest(asset, start_date, end_date, N, M):
    #获取指数在回测区间内的收益
    chg_pct = getDailyIndexData([asset], start_date, end_date, 'CHG_PCT')
    index_return = empyrical.cum_returns(chg_pct.iloc[:, 0], starting_value=1)

    #start_date之前的多空信号
    prev_decision = getPrevLongShortDecision(asset, start_date, M, N, 0.7)
    if prev_decision == -1:
        print("Cannot get previous long short decision!")
        return

    prev_date = tDaysBackwardOffset(start_date, M - 1)
    slope = getSlopeSeries(asset, prev_date, end_date, N)
    n = len(slope)
    RSRS = np.zeros(n - M + 1)
    for i in range(M - 1, n, 1):
        slope_window = slope.iloc[i - M  + 1 : i + 1]
        RSRS[i - M + 1] = getRSRS(slope_window)

    RSRS = pd.Series(data=RSRS, index=list(slope.index)[M - 1 :], name="RSRS")
    n = len(RSRS)
    long_short_flag = pd.Series(data = np.zeros(n), index=RSRS.index, name="long_short_flag")
    trade_dates = list(RSRS.index)
    long_decision_date = []
    short_decision_date = []
    long_short_flag.iloc[0] = prev_decision

    for i in range(1, n, 1):
        #当天的多空标志沿用前一天收市后的判断，当天产生的多空标志用于下一天
        long_short_flag.iloc[i] = prev_decision
        if RSRS.iloc[i] > 0.7 and prev_decision == 0:

            trade_date = trade_dates[i].strftime("%Y-%m-%d")
            ma20 = getMA(asset, trade_date, 20)
            if i < 3:
                trade_date_pre3 = tDaysBackwardOffset(trade_date, 3)
            else:
                trade_date_pre3 = trade_dates[i - 3].strftime("%Y-%m-%d")
            ma20_pre3 = getMA(asset, trade_date_pre3, 20)

            if ma20 > ma20_pre3:
                prev_decision = 1
                long_decision_date.append(trade_dates[i])

        elif RSRS.iloc[i] < -0.7 and prev_decision == 1:
            prev_decision = 0
            short_decision_date.append(trade_dates[i])

    rsrs_chg_pct = np.zeros(n)
    for i in range(n):
        rsrs_chg_pct[i] = chg_pct.iloc[i,0] * long_short_flag.iloc[i]
    rsrs_chg_pct = pd.Series(data=rsrs_chg_pct, index=chg_pct.index, name="timing")
    rsrs_return = empyrical.cum_returns(rsrs_chg_pct, starting_value=1)

    return_data = pd.DataFrame({asset : index_return,
                                'timing' : rsrs_return})
    fig = drawValueCurve(return_data)
    buy_point = index_return.loc[long_decision_date]
    sell_point = index_return.loc[short_decision_date]
    plt.plot_date(buy_point.index, buy_point.values, fmt='ro', xdate=True, ydate=False)
    plt.plot_date(sell_point.index, sell_point.values, fmt='go', xdate=True, ydate=False)
    plt.savefig(asset + "择时.png")
    fig.show()
    return long_decision_date, short_decision_date,long_short_flag

def FaberBackTest(asset, start_date, end_date):
    # 获取指数在回测区间内的收益
    chg_pct = getDailyIndexData([asset], start_date, end_date, 'CHG_PCT')
    index_return = empyrical.cum_returns(chg_pct.iloc[:, 0], starting_value=1)

    #获得调仓日期
    adjust_dates = generateAdjustDate2(start_date, end_date)

    N = chg_pct.shape[0]
    long_short_flag = pd.Series(data=np.zeros(N), index=chg_pct.index, name="long_short_flag")
    long_decision_date = []
    short_decision_date = []

    n = len(adjust_dates)
    prev_decision = -1
    #针对每个调仓日生成多空信号
    for i in range(n):
        adjust_date = adjust_dates[i]
        tmp = datetime.datetime.strptime(adjust_date, "%Y-%m-%d")
        month_start_date = datetime.datetime(tmp.year, tmp.month, 1)
        period_start_date = month_start_date - relativedelta(months=8)
        period_start_date = period_start_date.strftime("%Y-%m-%d")
        month_end_dates = generateAdjustDate2(period_start_date, adjust_date)
        month_end_dates.append(adjust_date)
        monthly_index = getMonthlyIndexData([asset], month_end_dates)
        monthly_average = monthly_index.mean().values[0]
        if monthly_index.iloc[-1, 0] >= monthly_average:
            flag = 1
        else:
            flag = 0

        if i < n - 1:
            next_adjust_date = adjust_dates[i + 1]
        else:
            next_adjust_date = end_date

        if flag != prev_decision:
            if flag == 1:
                if i == 0:
                    long_decision_date.append(chg_pct.index[0])
                else:
                    long_decision_date.append(datetime.datetime.strptime(adjust_date, "%Y-%m-%d").date())
            else:
                if i == 0:
                    short_decision_date.append(chg_pct.index[0])
                else:
                    short_decision_date.append(datetime.datetime.strptime(adjust_date, "%Y-%m-%d").date())
            prev_decision = flag

        period_start_date = datetime.datetime.strptime(adjust_date, "%Y-%m-%d").date()
        period_end_date = datetime.datetime.strptime(next_adjust_date, "%Y-%m-%d").date()
        long_short_flag[(long_short_flag.index > period_start_date) & (long_short_flag.index <= period_end_date)] = flag

    faber_chg_pct = np.zeros(N)

    for i in range(N):
        faber_chg_pct[i] = chg_pct.iloc[i,0] * long_short_flag.iloc[i]

    faber_chg_pct = pd.Series(data=faber_chg_pct, index=chg_pct.index, name="timing")
    faber_return = empyrical.cum_returns(faber_chg_pct, starting_value=1)

    return_data = pd.DataFrame({asset : index_return,
                                'timing' : faber_return})
    fig = drawValueCurve(return_data)
    buy_point = index_return.loc[long_decision_date]
    sell_point = index_return.loc[short_decision_date]
    plt.plot_date(buy_point.index, buy_point.values, fmt='ro', xdate=True, ydate=False)
    plt.plot_date(sell_point.index, sell_point.values, fmt='go', xdate=True, ydate=False)
    plt.savefig(asset + "择时.png")
    fig.show()

    portfolioAnalysis(pd.DataFrame(return_data.iloc[:, 0]))
    portfolioAnalysis(pd.DataFrame(return_data.iloc[:, 1]))
    return long_decision_date, short_decision_date, long_short_flag




















