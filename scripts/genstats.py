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
    dexport = ['User,Date,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,Total']

    # this ordered dictionary will contain the message total for all users during this day
    dailytotal = odict({})
    # populate dailytotal with each hour
    for i in range (0,24):
        dailytotal[str(i)] = 0

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
            b = hour[-1] # how many messages during this hour
            uhdict[str(a)] = str(b)
            dailytotal[str(a)] = dailytotal[str(a)] + int(b)

        newstring = user + ',' + str(date)
        for i in uhdict.keys():
            x = uhdict[str(i)]
            newstring = newstring + ',' + x

            # to get a user's total for the day
            usermessagecount += int(x)


        #add total column for user
        newstring = newstring + ',' + str(usermessagecount)

        dexport.append(newstring)

    # total row for day
    dailymessagecount = 0
    dailystring = 'TOTAL' + ',' + str(date)
    for i in dailytotal.keys():
        x = dailytotal[str(i)]
        dailystring = dailystring + ',' + str(x)

        # to get a total for the day
        dailymessagecount += int(x)

    dailystring = dailystring + ',' + str(dailymessagecount)


    # export
    dayfile = open(filename,'w')
    for line in dexport:
        dayfile.write(line + '\n')
    dayfile.write(dailystring + '\n')
    dayfile.close()