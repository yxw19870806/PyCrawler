# -*- coding:utf-8  -*-
'''
Created on 2013-6-15

@author: rena
'''
from common import common
import os
import sys
import time

class RenameVideo(common.Tool):
    
    def __init__(self):
        # 获取配置文件
        processPath = os.getcwd()
        configFile = open(processPath + "\\config.ini", 'r')
        lines = configFile.readlines()
        configFile.close()
        config = {}
        for line in lines:
            line = line.lstrip().rstrip().replace(" ", "")
            if len(line) > 1 and line[0] != "#":
                try:
                    line = line.split("=")
                    config[line[0]] = line[1]
                except Exception, e:
                    self.printMsg(str(e))
                    pass
        # 配置文件获取配置
        self.videoFilePath = "Z:\\G\\" # 视频源目录，保存刚下载来的视频
        self.destRootPath = "Z:\\G+\\video\\"   # 视频目标目录，保存已重命名的视频
        self.memberUIdListFilePath = self.getConfig(config, "MEMBER_UID_LIST_FILE_NAME", processPath + "\\idlist.txt", 1, processPath + "\\")
        self.printMsg("config init succeed")
        
    def main(self):
        startTime = time.time()
        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.memberUIdListFilePath):
            userListFile = open(self.memberUIdListFilePath, 'r')
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.printErrorMsg("Not exists member id list file: " + self.memberUIdListFilePath + ", process stop!")
            sys.exit()
        
        userList = {}
        for userId in userIdList:
            userName = userIdList[userId][1]
            path = userIdList[userId][6]
            userList[userName] = path

        # 遍历目标文件夹
        videoList = sorted(os.listdir(self.videoFilePath))
        count = 0
        for video in videoList:
            videoName = video.replace(".html", "")
            fileName, fileType = videoName.split(".")
            fileNameList = fileName.split("_")
            userName = ""
            for word in fileNameList:
                if word.isdigit():
                    fileIndex = word
                    break
                if userName == "":
                    userName += word
                else:
                    userName += "_" + word
            sourcePath = self.videoFilePath + video
            destPath = self.destRootPath + userList[userName] + "\\" + userName + "\\" + fileIndex + "." + fileType
            destDir = os.path.dirname(destPath)
            if not os.path.exists(destDir):
                if not self.createDir(destDir):
                    self.printMsg("create " + destDir + " error")
                    sys.exit()
            os.rename(sourcePath, destPath)
            count += 1
        
        stopTime = time.time()
        self.printMsg("video move succeed, use " + str(int(stopTime - startTime)) + " seconds, sum count: " + str(count))

if __name__ == '__main__':
    RenameVideo().main()
