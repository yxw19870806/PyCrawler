#-*- coding:utf-8  -*-
'''
Created on 2013-4-21

@author: rena

输出目录和txt文件中视频数量不一致的成员列表
'''
import os

videoRootPath = "Z:\\G+\\video\\"
allVideoUrlFilePath = os.getcwd() + "\\info\\allVideo.txt"
unableDownloadFilePath = "queshao.txt"

# 视频路径中各成员视频数量
memberList1 = {}
list1 = os.listdir(videoRootPath)
for path1 in list1:
    if path1 == "OTHER":
        continue
    list2 = os.listdir(videoRootPath + path1)
    for path2 in list2:
        list3 = os.listdir(videoRootPath + path1 + "\\" + path2)
        for member in list3:
            memberList1[member] = len(os.listdir(videoRootPath + path1 + "\\" + path2 + "\\" + member))

# 记录所有视频url的txt文件中各成员视频数量
memberList2 = {}
isContinue = True
name = ""
tempFile = open(allVideoUrlFilePath, 'r')
lines = tempFile.readlines()
tempFile.close()
for line in lines:
    if line.find("https:") != -1:
        if isContinue:
            memberList2[name] += 1
    elif line.find("****************************************************************************************************") != -1:
        if isContinue:
            name = ""
            isContinue = False             
    else:
            isContinue = True
            name = line.split(" ")[1][:-1]
            if not memberList2.has_key(name):
                memberList2[name] = 0

# 记录无法下载的视频url的txt文件中各成员视频数量
memberList3 = {}
isContinue = True
name = ""
tempFile = open(unableDownloadFilePath, 'r')
lines = tempFile.readlines()
tempFile.close()
for line in lines:
    if line.find("https:") != -1:
        if isContinue:
            memberList3[name] += 1
    elif line.find("****************************************************************************************************") != -1:
        if isContinue:
            name = ""
            isContinue = False             
    else:
            isContinue = True
            name = line[:-1]
            if not memberList3.has_key(name):
                memberList3[name] = 0

memberList = {}
for member in memberList2:
    if memberList1.has_key(member) and memberList3.has_key(member) and memberList2[member] == memberList1[member] + memberList3[member] \
        or memberList1.has_key(member) and memberList2[member] == memberList1[member] \
        or memberList3.has_key(member) and memberList2[member] == memberList3[member]:
        continue
    if memberList1.has_key(member):
        count1 = memberList1[member]
    else:
        count1 = 0
    if memberList2.has_key(member):
        count2 = memberList2[member]
    else:
        count2 = 0
    if memberList3.has_key(member):
        count3 = memberList3[member]
    else:
        count3 = 0
    if count2 != count1 + count3:
        print member + ": " + str(count2) + " / " + str(count1 + count3)