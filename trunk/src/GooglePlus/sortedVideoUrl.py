#-*- coding:utf-8  -*-
'''
Created on 2013-4-14

@author: rena

µ¹ÐðÅÅÁÐurlË³Ðò
'''

import os

soreceFilePath = os.getcwd() + "\\sorted_source.txt"
resultFilePath = os.getcwd() + "\\sorted_result.txt"

sourceFile = open(soreceFilePath, 'r')
lines = sourceFile.readlines()
sourceFile.close()
count = 1
user = []
newUser = []
userList = []
isContinue = True
for line in lines:
    if line.find("https:") != -1:
        if isContinue:
            line = line[line.find(":") + 2:]
            line = line.split(" ")
            user.append(line[2] + "\n")
    elif line.find("****************************************************************************************************") != -1:
        if isContinue:
            videoCount = len(user) - 1
            newUser.append(user[0])
            if videoCount > 0:
                for i in range(videoCount):
                    newUser.append(str(i + 1) + ": " + user[videoCount - i])
            newUser.append("****************************************************************************************************\n")
            user = []
        else:
            isContinue = True 
    else:
        userId = line.split(" ")[0]
        if userId in userList:
            isContinue = False
        else:
            userList.append(userId)
            user.append(line)

resultFile = open(resultFilePath, 'w')
for i in newUser:
    resultFile.write(i)
resultFile.close()
