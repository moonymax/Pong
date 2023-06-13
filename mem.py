"""
save and load json
remove file from os safely
"""
import json
def loadjson(filename):
    file = open(filename, 'r')
    j = json.loads(''.join(file.readlines()))
    file.close()
    return j

def savejson(filename, j):
    file = open(filename, 'w')
    s = json.dumps(j)
    file.write(s)
    file.close()


def remove(filename):
    #prevent directory crawling
    if '/' in filename:return
    if os.path.exists(filename):os.remove(filename)
    else:print("The file does not exist")