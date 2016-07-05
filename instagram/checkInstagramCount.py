# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os

def getCount(idPath, imageRootPath):
    tempFile = open(idPath, 'r')
    lines = tempFile.readlines()
    tempFile.close()
    for line in lines:
        line = line.split("\t")
        imagePath = imageRootPath + line[0]
        imagePath = imagePath.decode('UTF-8').encode('GBK')
        if os.path.exists(imagePath):
            count1 = len(os.listdir(imagePath))
        else:
            count1 = 0
        count2 = int(line[1])
        if count1 != count2:
            print line[0] + ": " + str(count1) + ", " + str(count2)
    print "check over!"

getCount("info\\idlist.txt", "Z:\\G+\\instagram\\")