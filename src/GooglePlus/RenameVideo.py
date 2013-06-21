# -*- coding:utf-8  -*-
'''
Created on 2013-6-15

@author: rena
'''

import os
import sys
import time
import traceback
import urllib2

class RenameVideo():
    
    def processExit(self):
        sys.exit()
        
    def doGet(self, url):
        if url.find("http") == -1:
            return None
        count = 0
        while 1:
            try:
                request = urllib2.Request(url)
                if sys.version_info < (2, 7):
                    response = urllib2.urlopen(request)
                else:
                    response = urllib2.urlopen(request, timeout=20)
                return response.read()
            except Exception, e:
                self.printMsg(str(e))
                traceback.print_exc()
            count += 1
            if count > 10:
                self.printMsg("can not connection " + url)
                return False
            
    def getTime(self):
        return time.strftime('%H:%M:%S', time.localtime(time.time()))
     
    def printMsg(self, msg):
        msg = self.getTime() + " " + msg
        print msg
            
    def createDir(self, path):
        count = 0
        while 1:
            try:
                if count >= 5:
                    return False
                os.makedirs(path)
                if os.path.isdir(path):
                    return True
                count += 1
            except:
                pass
        
    # mode 0 : 直接赋值
    # mode 1 : 字符串拼接
    # mode 2 : 取整
    def getConfig(self, config, key, defaultValue, mode, addValue=None):
        value = None
        if config.has_key(key):
            if mode == 0:
                value = config[key]
            elif mode == 1:
                value = addValue + config[key]
            elif mode == 2:
                try:
                    value = int(config[key])
                except:
                    self.printMsg("'" + key + "' must is a number in config.ini, default value")
                    value = 1
        else:
            self.printMsg("Not found '" + key + "' in config.ini, default value")
            value = defaultValue
        return value
    
    def __init__(self):
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
        # 配置文件获取日志文件路径
        self.videoFilePath = "Z:\\G2\\"
        self.destRootPath = "Z:\\G+\\video\\"
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
            self.processExit()
        
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
                    self.processExit()
            os.rename(sourcePath, destPath)
            count += 1
        
        stopTime = time.time()
        self.printMsg("video move succeed, use " + str(int(stopTime - startTime)) + " seconds, sum count: " + str(count))

if __name__ == '__main__':
    RenameVideo().main()
