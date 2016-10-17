# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os

imageRootPath = "Z:\\G+\\fkoji\\"

def getCount(path):
    tempFile = open(path, "r")
    lines = tempFile.readlines()
    tempFile.close()
    for line in lines:
        if line.find("http") != -1:
            continue
        line = line.split("\t")
        imagePath = imageRootPath + line[0].replace("\n", "")
        if os.path.exists(imagePath):
            count1 = len(os.listdir(imagePath))
        else:
            count1 = 0
        count2 = int(line[1])
        if count1 != count2:
            print line[0] + ": " + str(count1) + ", " + str(count2)
    print "check over!"

getCount("fkoji.save")
