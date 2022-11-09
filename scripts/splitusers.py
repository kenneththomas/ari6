import fixtools as ft
import re

logfile = open('../logs/a5lfix.log','r')
allfile = open('../logs/everyone.log','w')

log = logfile.readlines()

userlist = []
parsed = []
aiusers = ['bari','ren','hikachu','heyzeus']


# find unique users
for line in log:
    try:
        f = ft.parsefix(line)
        for aiuser in aiusers:
            if aiuser in f['49'].lower():
                #if the length of f['58'] is more than 6 characters
                if len(f['58']) > 6:
                    allfile.write(f['58'])
    except:
        continue
    user = f['49']
    parsed.append(f)
    if user not in userlist:
        userlist.append(user)

for user in userlist:
    userfile = '../logs/{}.log'.format(user)
    a = open(userfile,'w')
    for line in parsed:
        if line['49'] == user:
            a.write(line['58'])
    a.close()

