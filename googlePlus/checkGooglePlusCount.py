# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os

imageRootPath = "E:\\GooglePlus\\"

def getCount(path):
    tempFile = open(path, 'r')
    lines = tempFile.readlines()
    tempFile.close()
    for line in lines:
        line = line.split("\t")
        imagePath = imageRootPath + line[4].replace("\n", "") + "\\" + line[1]
        imagePath = imagePath.decode('UTF-8').encode('GBK')
        if os.path.exists(imagePath):
            count1 = len(os.listdir(imagePath))
        else:
            count1 = 0
        count2 = int(line[2])
        if count1 != count2:
            print line[1] + ": " + str(count1) + ", " + str(count2)
    print "check over!"

getCount("info\\save.data")
