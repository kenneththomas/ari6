import fixtools as ft
import numpy as np
import pandas as pd
from collections import OrderedDict as odict
import glob

# poststats.py should be run AFTER genstats.py, as it relies on those generated files

path = '../stats/daily' # use your path
all_files = glob.glob(path + "/*.csv")

li = []

for filename in all_files:
    df = pd.read_csv(filename, index_col=None, header=0)
    li.append(df)

frame = pd.concat(li, axis=0, ignore_index=True).sort_values(by=['Date'])

print(frame)

# split by user
users = frame.User.unique()
dates = frame.Date.unique()
print(users)

usertotals = []

for user in users:
    df2 = frame[frame['User'] == user]
    if ' ' in user:
        user = user.replace(' ','')
    df2.to_csv('../stats/user/{}.csv'.format(user), index=False)
    df4 = df2['Total']
    usertotals.append('{},{}'.format(user,df4.sum()))

print(usertotals)

totals = open('../stats/totals.csv', 'w')
for line in usertotals:
    try:
        totals.write(line + '\n')
    except:
        print('error processing {}'.format(line))
totals.close()

# total for date
df3 = frame[frame['User'] == 'TOTAL']
print(df3[['Date','Total']])
df3.to_csv('../stats/byday.csv', index=False)




