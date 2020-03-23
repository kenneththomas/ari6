import fixtools as ft
import numpy as np
import pandas as pd
from collections import OrderedDict as odict

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
    try:
       dt = (pd.to_datetime(f['52']))
       new = [dt,f['49']]
    except:
        print('this message is producing an error.')
        print(f)
    ll.append(new)

df = pd.DataFrame(ll, columns=['Timestamp', 'User'])

# split out into day
datelist = []
dates = df['Timestamp'].dt.date.value_counts(dropna=True).sort_index()

# populate date list
for index, row in df.iterrows():
    date = row['Timestamp'].date()
    if date not in datelist:
        datelist.append(date)

print(dates)

for date in datelist:
    dexport = ['User,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,Total']
    filename = '../stats/daily/{}.csv'.format(date)
    # create dataframe only matching this particular day
    df2 = (df['Timestamp'].dt.date == date)
    df3 = df.loc[df2]

    # find users active on this day
    print(date)
    users = df3.User.unique()
    for user in users:
        usermessagecount = 0
        #print(user)
        # split by user
        df4 = df3[df3['User'] == user]
        # split by hour
        hourcount = df4['Timestamp'].dt.hour.value_counts(dropna=True).sort_index()
        print(user + str(date))
        print(hourcount)
        hourraw = str(hourcount).replace(' ',',').splitlines()
        #remove junk at end
        hourraw.pop()
        uhdict = odict()

        # populate with 0s just in case blank
        for i in range (0,24):
            uhdict[str(i)] = '0'

        for hour in hourraw:
            hour = hour.split(',')
            a = hour[0] # which hour
            b = hour[4] # how many messages during this hour
            uhdict[str(a)] = str(b)

        newstring = user
        for i in uhdict.keys():
            x = uhdict[str(i)]
            newstring = newstring + ',' + x

            # to get a total for the day
            usermessagecount += int(x)

        print(usermessagecount)

        #add total column for user
        newstring = newstring + ',' + str(usermessagecount)

        dexport.append(newstring)

    print(dexport)

    # export
    dayfile = open(filename,'w')
    for line in dexport:
        dayfile.write(line + '\n')
    dayfile.close()


# count by user totals
cbu = df['User'].value_counts(dropna=True)
print(cbu)

#print(df.Timestamp.dt.date.head())

# export count by user
cbu.to_csv('../stats/totals.csv')

# count by day totals
datelist = []
dates = df['Timestamp'].dt.date.value_counts(dropna=True).sort_index()

# export count by day
dates.to_csv('../stats/byday.csv')