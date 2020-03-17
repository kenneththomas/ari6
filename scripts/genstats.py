import fixtools as ft
import numpy as np
import pandas as pd

logfile = '../logs/a5lfix.log'

a = open(logfile,'r')

ll = []

for message in a.readlines():
    try:
        f = ft.parsefix(message)
    except:
        continue
    # which user
    # which day
    # which hour
    dt = (pd.to_datetime(f['52']))
    new = [dt,f['49']]
    ll.append(new)

df = pd.DataFrame(ll, columns=['Timestamp', 'User'])
print(df)

# count by user totals
cbu = df['User'].value_counts(dropna=True)
print(cbu)

#print(df.Timestamp.dt.date.head())

# export count by user
cbu.to_csv('../stats/totals.csv')

#for index, row in df.iterrows():
    #print(row['User'], row['Timestamp'])

# count by day totals
datelist = []
dates = df['Timestamp'].dt.date.value_counts(dropna=True)

# export count by day
dates.to_csv('../stats/byday.csv')

# populate date list
for index, row in df.iterrows():
    date = row['Timestamp'].date()
    print(date)
    if date not in datelist:
        datelist.append(date)

print(dates)
print(datelist)

for date in datelist:
    filename = '../stats/daily/{}.csv'.format(date)
    # create dataframe only matching this particular day
    df2 = (df['Timestamp'].dt.date == date)
    df3 = df.loc[df2]
    print(df3)
    # now we need for each hour
    hourcount =  df3['Timestamp'].dt.hour.value_counts(dropna=True)
    print(hourcount)
    hourcount.to_csv(filename)



