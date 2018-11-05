from Predict import *
import numpy as np
from sklearn import linear_model
from Date import *

def getSlopeSeries(asset, start_date, end_date, N):
    prev_date = tDaysBackwardOffset(start_date, N - 1)
    highest_index = getDailyIndexData([asset], prev_date, end_date, "HIGHEST_INDEX")
    lowest_index = getDailyIndexData([asset], prev_date, end_date, "LOWEST_INDEX")
    n = highest_index.shape[0]
    slope = np.zeros(n - N + 1)
    for i in range(N - 1, n, 1):
        x = lowest_index.iloc[i - N + 1 : i + 1, 0].values
        y = highest_index.iloc[i - N + 1 : i + 1, 0].values
        regr = linear_model.LinearRegression()
        regr.fit(x.reshape(-1, 1), y.reshape(-1, 1))
        slope[i - N + 1] = regr.coef_[0][0]
        '''
        plt.scatter(x, y)
        plt.plot(x, regr.predict(x.reshape(-1, 1)).reshape(-1, 1))
        plt.show()
        '''
    slope = pd.Series(data=slope, index=list(highest_index.index)[N - 1 :], name="slope")
    return slope

def getRSRS(slope):
    mean_value = np.mean(slope)
    std_value = np.std(slope, ddof=1)
    RSRS = (slope[-1] - mean_value) / std_value
    return RSRS

def getPrevLongShortDecision(asset, date, M, N, thr):
    prev_date = tDaysBackwardOffset(date, 2 * M - 1)
    slope = getSlopeSeries(asset, prev_date, date, N)
    n = len(slope)
    i = n - 1
    while i >= M - 1:
        slope_window = slope[i - M + 1 : i]
        RSRS = getRSRS(slope_window)
        if RSRS > thr:
            return 1
        elif RSRS < -thr:
            return 0
        i = i - 1
    return -1

def getMA(asset, date, M):
    prev_date = tDaysBackwardOffset(date, M - 1)
    close_index = getDailyIndexData([asset], prev_date, date, "CLOSE_INDEX")
    return close_index.mean(axis=0).values[0]

def findLongShortDecisions(long_short_flag):
    dates = list(long_short_flag.index)
    n = len(dates)
    '''
    for i in range(n):
        dates[i] = dates[i].strftime("%Y-%m-%d")
    '''
    decisions = dict()
    for i in range(1, n):
        if long_short_flag.iloc[i, 0] != long_short_flag.iloc[i - 1, 0]:
            decisions[dates[i - 1]] = long_short_flag.iloc[i, 0]
    return decisions














