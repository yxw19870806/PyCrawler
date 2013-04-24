#-*- coding:utf-8  -*-
'''
Created on 2013-4-14

@author: rena

输出目录和txt文件中图片数量不一致的成员名字，None则没有
'''

import os

imageRootPath = "Z:\\G+\\image\\"

def getCount(path):
    tempFile = open(path, 'r')
    lines = tempFile.readlines()
    tempFile.close()
    for line in lines:
        line = line.split("\t")
        imagePath = imageRootPath + line[4].replace("\n", "") + "\\" + line[1]
        if len(os.listdir(imagePath)) != int(line[2]):
            print line[1]
    
print getCount("BK_idlist.txt")
