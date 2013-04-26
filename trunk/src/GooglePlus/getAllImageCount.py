'''
Created on 2013-4-14

@author: rena
'''

def getCount(path):
    tempFile = open(path, 'r')
    lines = tempFile.readlines()
    tempFile.close()
    count = 0
    for line in lines:
        line = line.split("\t")
        count += int(line[2])
    return count
    
a = getCount("info\\bk_idlist.txt")
b = getCount("2013-04-24_23_14_24_idlist.txt")
print a
print b
print b - a
