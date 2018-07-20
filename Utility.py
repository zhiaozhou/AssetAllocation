import pandas as pd

#保存dataframe到excel
def save(df, filename):
    writer = pd.ExcelWriter(filename)
    df.to_excel(writer)
    writer.save()

