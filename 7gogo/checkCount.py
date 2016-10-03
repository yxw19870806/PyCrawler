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
        name = line[0]
        imagePath = imageRootPath + name
        if os.path.exists(imagePath):
            all_file = os.listdir(imagePath)
            count1 = len(all_file)
            max_count = int(max(all_file).split('.')[0])
        else:
            count1 = 0
            max_count = 0
        count2 = int(line[2])

        if count1 != count2 or count1 != max_count:
            print name + ": " + str(count1) + ", " + str(count2) + ", " + str(max_count)
    print "check over!"

getCount("info\\save.data", "D:\\workspace\\G+\\7gogo\\video\\")
