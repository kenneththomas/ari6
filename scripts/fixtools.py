from collections import OrderedDict as odict

def parsefix(fixmsg):
    return odict(item.split("=") for item in fixmsg.split(";"))

def tweak(fixdict,tag,value):
    addedtag = False # maybe theres a more efficient way to do this
    if tag not in fixdict.keys():
        addedtag = True
    fixdict.update({tag : value})
    if addedtag:
        trailer(fixdict)
    return fixdict

def trailer(fixdict):
    fixdict.move_to_end('58')
    fixdict.move_to_end('10')
    return fixdict

def exportfix(fixdict):
    genfix=''
    for key,val in fixdict.items():
        if key != '10':
            genfix = genfix + str(key) + "=" + str(val) + ';'
        else: # tail tag should not have a semicolon at the end
            genfix = genfix + str(key) + "=" + str(val)
    return genfix