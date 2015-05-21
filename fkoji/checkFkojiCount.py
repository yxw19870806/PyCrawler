# -*- coding:UTF-8  -*-
'''
Created on 2015-5-19

@author: hikaru

输出目录和txt文件中图片数量不一致的成员名字
'''

import os

imageRootPath = "Z:\\G+\\fkoji\\"

def getCount(path):
    tempFile = open(path, 'r')
    lines = tempFile.readlines()
    tempFile.close()
    for line in lines:
        if line.find('http') != -1:
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
