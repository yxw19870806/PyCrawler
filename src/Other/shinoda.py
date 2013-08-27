# -*- coding:utf-8  -*-
'''
Created on 2013-5-6

@author: haruka
'''
from common import common
import os
import shutil
import sys
import time

class shinoda(common.Tool):
    
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

    def download(self, imageUrl, imagePath, imageCount):
        imgByte = self.doGet(imageUrl)
        if imgByte:
            fileType = imageUrl.split(".")[-1]
            imageFile = open(imagePath + "\\" + str("%03d" % imageCount) + "." + fileType, "wb")
            self.printMsg("start download " + str(imageCount) + ": " + imageUrl)
            imageFile.write(imgByte)
            imageFile.close()
            self.printMsg("download succeed")
        else:
            self.printErrorMsg("download image error: " + imageUrl)
                           
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
        self.messageUrlLogFilePath = self.getConfig(config, "MESSAGE_URL_LOG_FILE_NAME", processPath + "\\log\\messageLog.txt", 1, prefix=processPath + "\\")
        self.imageUrlLogFilePath = self.getConfig(config, "IMAGE_URL_LOG_FILE_NAME", processPath + "\\log\\messageLog.txt", 1, prefix=processPath + "\\")
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", processPath + "\\log\\errorLog.txt", 1, prefix=processPath + "\\")
        self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", processPath + "\\log\\traceLog.txt", 1, prefix=processPath + "\\")
        self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", processPath + "\\log\\stepLog.txt", 1, prefix=processPath + "\\")
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", processPath + "\\photo", 1, prefix=processPath + "\\")
        self.imageTempDirName = self.getConfig(config, "IMAGE_TEMP_DIR_NAME", "tmpImage", 0)
        self.memberUIdListFilePath = self.getConfig(config, "MEMBER_UID_LIST_FILE_NAME", processPath + "\\idlist.txt", 1, prefix=processPath + "\\")
        # 配置文件获取程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSaveMessageUrl = self.getConfig(config, "IS_SAVE_MESSAGE_URL", 1, 2)
        self.isSaveImageUrl = self.getConfig(config, "IS_SAVE_IMAGE_URL", 1, 2)
        self.isDownloadImage = self.getConfig(config, "IS_DOWNLOAD_IMAGE", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImagePageCount = self.getConfig(config, "GET_IMAGE_PAGE_COUNT", 1, 2)
#        self.isProxy = self.getConfig(config, "IS_PROXY", 1, 2)
#        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
#        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        self.printMsg("config init succeed")
    
    def main(self):
        # picture
        if self.isDownloadImage != 1:
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
        if self.isSaveMessageUrl == 1:
            messageUrlLogFileDir = os.path.dirname(self.messageUrlLogFilePath)
            if not os.path.exists(messageUrlLogFileDir):
                if not self.createDir(messageUrlLogFileDir):
                    self.printErrorMsg("create " + messageUrlLogFileDir + " error")
                    self.processExit()
                self.printStepMsg("message URL log file path is not exist, create it: " + messageUrlLogFileDir)
        if os.path.exists(self.imageDownloadPath):
            if os.path.isdir(self.imageDownloadPath):
                isDelete = False
                while not isDelete:
                    input = raw_input(self.imageDownloadPath + " is exist, do you want to remove it and continue? (Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except:
                        pass
                self.printStepMsg("image download path: " + self.imageDownloadPath + " is exist, remove it")
                shutil.rmtree(self.imageDownloadPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageDownloadPath):
                    time.sleep(5)
            else:
                self.printStepMsg("image download path: " + self.imageDownloadPath + " is a file, delete it")
                os.remove(self.imageDownloadPath)
        self.printStepMsg("created image download path: " + self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.printErrorMsg("create " + self.imageDownloadPath + " error")
            self.processExit()
        # 设置代理
#        if self.isProxy == 1:
#            self.proxy(self.proxyIp, self.proxyPort)
        # 下载
        imageTempPath = os.getcwd() + "\\" + self.imageTempDirName + "\\"
        url = "http://blog.mariko-shinoda.net/index%s.html"
        indexCount = 1
        allImageCount = 1
        while True:
            imageCount = 1
            imagePath = imageTempPath + str("%03d" % indexCount)
            if indexCount > 1:
                imageUrl = url % ("_" + str(indexCount))
                indexPage = self.doGet(imageUrl)
            else:
                imageUrl = url % ("")
                indexPage = self.doGet(imageUrl)
            self.trace("index URL:" + imageUrl)
            if indexPage:
                if not os.path.exists(imagePath):
                    os.makedirs(imagePath)
                # old image:
                imageIndex = 0
                while True:
                    imageIndex = indexPage.find('<a href="http://mariko-shinoda.up.seesaa.net', imageIndex)
                    if imageIndex == -1:
                        break
                    imageStart = indexPage.find("http", imageIndex) 
                    imageStop = indexPage.find('"', imageStart)
                    imageUrl = indexPage[imageStart:imageStop]
                    self.trace("image URL:" + imageUrl)
                    if imageUrl.find("data") == -1:
                        self.download(imageUrl, imagePath, imageCount)
                        imageCount += 1
                        allImageCount += 1
                    imageIndex += 1
                # new image:
                imageIndex = 0
                while True:
                    imageIndex = indexPage.find('<img src="http://blog.mariko-shinoda.net', imageIndex)
                    if imageIndex == -1:
                        break
                    imageStart = indexPage.find("http", imageIndex)
                    imageStop = indexPage.find('"', imageStart)
                    imageUrl = indexPage[imageStart:imageStop]
                    self.trace("image URL:" + imageUrl)
                    if imageUrl.find("data") == -1:
                        self.download(imageUrl, imagePath, imageCount)
                        imageCount += 1
                        allImageCount += 1
                    imageIndex += 1          
            else:
                self.printStepMsg("down load over!, count: " + str(allImageCount))
            indexCount += 1
            
        if self.isSaveMessageUrl == 1:
            self.writeFile("****************************************************************************************************", self.messageUrlLogFilePath, isTime=False)
        if self.isSaveImageUrl == 1:
            self.writeFile("****************************************************************************************************", self.imageUrlLogFilePath, isTime=False)
        
        # 排序
        if self.isSort == 1:
            allImageCount = 1
            for index1 in sorted(os.listdir(imageTempPath), reverse=True):
                for fileName in sorted(os.listdir(imageTempPath + index1), reverse=True):
                    imagePath = imageTempPath + index1 + "\\" + fileName
                    fileType = fileName.split(".")[-1]
                    shutil.copyfile(imagePath, self.imageDownloadPath + "\\" + str("%05d" % allImageCount) + "." + fileType)
                    allImageCount += 1
            self.printStepMsg("sorted over!, count: " + str(allImageCount))

        stopTime = time.time()
        self.printStepMsg("all members' image download succeed, use " + str(int(stopTime - startTime)) + " seconds, sum download image count: " + str(allImageCount))

if __name__ == '__main__':
    shinoda().main()
