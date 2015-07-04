# -*- coding:UTF-8  -*-
'''
Created on 2013-4-14

@author: hikaru

输出目录和txt文件中图片数量不一致的成员名字
'''

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
        if not isinstance(line[1], int):
            continue
        count2 = int(line[1])
        if count1 != count2:
            print line[0] + ": " + str(count1) + ", " + str(count2)
    print "check over!"

getCount("info\\idlist_1.txt", "Z:\\G+\\Twitter\\twitter1\\")
getCount("info\\idlist_2.txt", "Z:\\G+\\Twitter\\twitter2\\")
getCount("info\\idlist_3.txt", "Z:\\G+\\Twitter\\twitter3\\")