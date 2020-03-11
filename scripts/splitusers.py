import fixtools as ft

logfile = open('../logs/a5lfix.log','r')

log = logfile.readlines()

userlist = []
parsed = []


# find unique users
for line in log:
    try:
        f = ft.parsefix(line)
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
            print('match, writing')
            a.write(line['58'])
    a.close()

