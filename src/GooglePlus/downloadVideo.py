# -*- coding:utf-8  -*-
'''
Created on 2013-6-15

@author: rena
'''

from common import common
import copy
import os
import sys
import time
import traceback
import urllib2

class downloadVideo(common.Tool):
    
    def trace(self, msg):
        if self.isDebug == 1:
            msg = self.getTime() + " " + msg
    #        self.printMsg(msg, False)
            if self.isLog == 1:
                self.writeFile(msg, self.traceLogPath)
    
    def printErrorMsg(self, msg):
        if self.isShowError == 1:
            msg = self.getTime() + " [Error] " + msg
            self.printMsg(msg, False)
            if self.isLog == 1:
                if msg.find("HTTP Error 500") != -1:
                    return
                if msg.find("urlopen error The read operation timed out") != -1:
                    return
                self.writeFile(msg, self.errorLogPath)
    
    def printStepMsg(self, msg):
        if self.isShowStep == 1:
            msg = self.getTime() + " " + msg
            self.printMsg(msg, False)
            if self.isLog == 1:
                self.writeFile(msg, self.stepLogPath)
    
    def __init__(self):
        processPath = os.getcwd()
        configFile = open(processPath + "\\..\\common\\config.ini", 'r')
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
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", processPath + "\\log\\errorLog.txt", 1, prefix=processPath + "\\")
        self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", processPath + "\\log\\traceLog.txt", 1, prefix=processPath + "\\")
        self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", processPath + "\\log\\stepLog.txt", 1, prefix=processPath + "\\")
        self.memberUIdListFilePath = self.getConfig(config, "MEMBER_UID_LIST_FILE_NAME", processPath + "\\idlist.txt", 1, prefix=processPath + "\\")
        self.resultFilePath = self.getConfig(config, "GET_VIDEO_DOWNLOAD_URL_FILE_NAME", processPath + "\\info\\get_result.html", 1, prefix=processPath + "\\")
        # 配置文件获取程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isGetVideoUrl = self.getConfig(config, "IS_GET_VIDEO_URL", 1, 2)
        self.isProxy = self.getConfig(config, "IS_PROXY", 1, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        self.printMsg("config init succeed")
        
    def main(self):
        # video
        if self.isGetVideoUrl != 1:
            self.processExit()
        startTime = time.time()
        # 判断各种目录是否存在
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not os.path.exists(stepLogDir):
                if not self.createDir(stepLogDir):
                    self.printErrorMsg("create " + stepLogDir + " error")
                    self.processExit()
                self.printStepMsg("step log file path is not exist, create it: " + stepLogDir)
            errorLogDir = os.path.dirname(self.errorLogPath)
            if not os.path.exists(errorLogDir):
                if not self.createDir(errorLogDir):
                    self.printErrorMsg("create " + errorLogDir + " error")
                    self.processExit()
                self.printStepMsg("error log file path is not exist, create it: " + errorLogDir)
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not os.path.exists(traceLogDir):
                if not self.createDir(traceLogDir):
                    self.printErrorMsg("create " + traceLogDir + " error")
                    self.processExit()
                self.printStepMsg("trace log file path is not exist, create it: " + traceLogDir)
        videoUrlFileDir = os.path.dirname(self.resultFilePath)
        if not os.path.exists(videoUrlFileDir):
            if not self.createDir(videoUrlFileDir):
                self.printErrorMsg("create " + videoUrlFileDir + " error")
                self.processExit()
            self.printStepMsg("video URL file path is not exist, create it: " + videoUrlFileDir)
        if os.path.exists(self.resultFilePath):
            isDelete = False
            while not isDelete:
                input = raw_input(self.resultFilePath + " is exist, do you want to remove it and continue? (Y)es or (N)o: ")
                try:
                    input = input.lower()
                    if input in ["y", "yes"]:
                        isDelete = True
                    elif input in ["n", "no"]:
                        self.processExit()
                except:
                    pass
                resultFile = open(self.resultFilePath, 'w')
                resultFile.close()
        # 设置代理
        if self.isProxy == 1:
            self.proxy(self.proxyIp, self.proxyPort)
        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.memberUIdListFilePath):
            userListFile = open(self.memberUIdListFilePath, 'r')
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                if len(userInfo) < 10:
                    continue
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.printErrorMsg("Not exists member id list file: " + self.memberUIdListFilePath + ", process stop!")
            self.processExit()
        newMemberUidListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.memberUIdListFilePath)[-1]
        newMemberUidListFile = open(newMemberUidListFilePath, 'w')
        newMemberUidListFile.close()

        newMemberUidList = copy.deepcopy(userIdList)
        for newUserId in newMemberUidList:
            # 如果没有名字，则名字用uid代替
            if len(newMemberUidList[newUserId]) < 2:
                newMemberUidList[newUserId].append(newMemberUidList[newUserId][0])
            # image count
            if len(newMemberUidList[newUserId]) < 3:
                newMemberUidList[newUserId].append("0")
            # image URL
            if len(newMemberUidList[newUserId]) < 4:
                newMemberUidList[newUserId].append("")
            # video count
            if len(newMemberUidList[newUserId]) < 5:
                newMemberUidList[newUserId].append("0")
            # video token
            if len(newMemberUidList[newUserId]) < 6:
                newMemberUidList[newUserId].append("")
            else:
                newMemberUidList[newUserId][5] = ""
            # 处理member 队伍信息
            if len(newMemberUidList[newUserId]) < 7:
                newMemberUidList[newUserId].append("")
                
        allVideoCount = 0
        for userId in userIdList:
            userName = newMemberUidList[userId][1]
            self.printStepMsg("UID: " + str(userId) + ", Member: " + userName)
            # 初始化数据
            videoCount = 0
            videoUrlList = []
            videoAlbumUrl = 'https://plus.google.com/' + userId + '/videos'
            self.trace("photo Album URL:" + videoAlbumUrl)
            videoAlbumPage = self.doGet(videoAlbumUrl)
            if videoAlbumPage:
                videoUrlIndex = videoAlbumPage.find('&quot;https://video.googleusercontent.com/?token')
                while videoUrlIndex != -1:
                    videoUrlStart = videoAlbumPage.find("http", videoUrlIndex)
                    videoUrlStop = videoAlbumPage.find('&quot;', videoUrlStart)
                    videoUrl = videoAlbumPage[videoUrlStart:videoUrlStop].replace("\u003d", "=")
                    # video token 取前20位
                    tokenStart = videoUrl.find("?token=") + 7
                    videoToken = videoUrl[tokenStart:tokenStart + 20]
                    # 将第一张image的URL保存到新id list中
                    if newMemberUidList[userId][5] == "":
                        newMemberUidList[userId][5] = videoToken
                    if len(userIdList[userId]) >= 6:
                        if videoToken == userIdList[userId][5]:
                            break
                    if videoUrl in videoUrlList:
                        videoUrlIndex = videoAlbumPage.find('&quot;https://video.googleusercontent.com/?token', videoUrlIndex + 1)
                        continue
                    videoUrlList.append(videoUrl)
                    videoCount += 1
                    videoUrlIndex = videoAlbumPage.find('&quot;https://video.googleusercontent.com/?token', videoUrlIndex + 1)
            else:
                self.printErrorMsg("can not get videoAlbumPage: " + videoAlbumUrl)
            # 生成下载视频url的文件
            if videoCount > 0:
                allVideoCount += videoCount
                index = 0
                try:
                    index = int(userIdList[userId][4])
                except:
                    pass
                newMemberUidList[userId][4] = str(int(newMemberUidList[userId][4]) + videoCount)
                resultFile = open(self.resultFilePath, 'a')
                while videoUrlList != []:
                    videoUrl = videoUrlList.pop()
                    index += 1
                    resultFile.writelines("<a href=" + videoUrl + ">" + str(userName + "_" + "%03d" % index) + "</a><br>\n")
                resultFile.close()
            # 保存最后的信息
            newMemberUidListFile = open(newMemberUidListFilePath, 'a')
            newMemberUidListFile.write("\t".join(newMemberUidList[userId]) + "\n")
            newMemberUidListFile.close()

        # 排序并保存新的idList.txt
        tmpList = []
        tmpUserIdList = sorted(newMemberUidList.keys())
        for index in tmpUserIdList:
            tmpList.append("\t".join(newMemberUidList[index]))
        newMemberUidListString = "\n".join(tmpList)
        newMemberUidListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.memberUIdListFilePath)[-1]
        self.printStepMsg("save new id list file: " + newMemberUidListFilePath)
        newMemberUidListFile = open(newMemberUidListFilePath, 'w')
        newMemberUidListFile.write(newMemberUidListString)
        newMemberUidListFile.close()
        
        stopTime = time.time()
        self.printStepMsg("all members' video url get succeed, use " + str(int(stopTime - startTime)) + " seconds, sum get video count: " + str(allVideoCount))

if __name__ == '__main__':
    downloadVideo().main()
