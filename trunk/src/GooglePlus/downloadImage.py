# -*- coding:utf-8  -*-
'''
Created on 2013-4-8

@author: haruka
'''

import os
import shutil
import sys
import time
import traceback
import urllib2
import copy

class downloadImage():
    
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
                self.trace("url: " + url)
                self.printErrorMsg(str(e) + ": " + url)
                traceback.print_exc()
            count += 1
            if count > 10:
                self.printErrorMsg("can not connection " + url)
                return False
    
    def getTime(self):
        return time.strftime('%H:%M:%S', time.localtime(time.time()))

    def printMsg(self, msg):
        msg = self.getTime() + " " + msg
        print msg
        
    def trace(self, msg):
        if self.isDebug == 1:
            msg = self.getTime() + " " + msg
    #        print msg
            if self.isLog == 1:
                logFile = open(self.traceLogPath, 'a')
                logFile.write(msg + "\n")
                logFile.close()
    
    def printErrorMsg(self, msg):
        if self.isShowError == 1:
            msg = self.getTime() + " [Error] " + msg
            print msg
            if self.isLog == 1:
                if msg.find("HTTP Error 500") != -1:
                    return
                if msg.find("urlopen error The read operation timed out") != -1:
                    return
                logFile = open(self.errorLogPath, 'a')
                logFile.write(msg + "\n")
                logFile.close()
    
    def printStepMsg(self, msg):
        if self.isShowStep == 1:
            msg = self.getTime() + " " + msg
            print msg
            if self.isLog == 1:
                logFile = open(self.stepLogPath, 'a')
                logFile.write(msg + "\n")
                logFile.close()
    
    def writeFile(self, msg, filePath, isTime=True):
        if isTime:
            msg = self.getTime() + " " + msg
        logFile = open(filePath, 'a')
        logFile.write(msg + "\n")
        logFile.close()
    
    def removeDirFiles(self, dirPath): 
        for fileName in os.listdir(dirPath): 
            targetFile = os.path.join(dirPath, fileName) 
            if os.path.isfile(targetFile): 
                os.remove(targetFile)

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

    def proxy(self):
            proxyHandler = urllib2.ProxyHandler({'https':"http://" + self.proxyIp + ":" + self.proxyPort})
            opener = urllib2.build_opener(proxyHandler)
            urllib2.install_opener(opener)
            self.printStepMsg("proxy set succeed")
    
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
        self.messageUrlLogFilePath = self.getConfig(config, "MESSAGE_URL_LOG_FILE_NAME", processPath + "\\log\\messageLog.txt", 1, processPath + "\\")
        self.imageUrlLogFilePath = self.getConfig(config, "IMAGE_URL_LOG_FILE_NAME", processPath + "\\log\\messageLog.txt", 1, processPath + "\\")
        self.videoFilePath = self.getConfig(config, "VIDEO_FILE_NAME", processPath + "\\video.txt", 1, processPath + "\\")
        self.videoUrlFilePath = self.getConfig(config, "VIDEO_DOWNLOAD_URL_FILE_NAME", processPath + "\\videoDownloadUrl.txt", 1, processPath + "\\")
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", processPath + "\\log\\errorLog.txt", 1, processPath + "\\")
        self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", processPath + "\\log\\traceLog.txt", 1, processPath + "\\")
        self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", processPath + "\\log\\stepLog.txt", 1, processPath + "\\")
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", processPath + "\\download", 1, processPath + "\\")
        self.imageTmpDirName = self.getConfig(config, "IMAGE_TEMP_DIR_NAME", "tmpImage", 0)
        self.memberUIdListFilePath = self.getConfig(config, "MEMBER_UID_LIST_FILE_NAME", processPath + "\\idlist.txt", 1, processPath + "\\")
        # 配置文件获取程序配置
        self.version = self.getConfig(config, "VERSION", 1, 2)
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSaveMessageUrl = self.getConfig(config, "IS_SAVE_MESSAGE_URL", 1, 2)
        self.isSaveImageUrl = self.getConfig(config, "IS_SAVE_IMAGE_URL", 1, 2)
        self.isSaveVideoUrl = self.getConfig(config, "iS_SAVE_VIDEO_URL", 1, 2)
        self.isSaveVideoDownloadUrl = self.getConfig(config, "iS_SAVE_VIDEO_DOWNLOAD_URL", 1, 2)
        self.isDownloadImage = self.getConfig(config, "IS_DOWNLOAD_IMAGE", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImageCount = self.getConfig(config, "GET_IMAGE_COUNT", 1, 2)
        self.isProxy = self.getConfig(config, "IS_PROXY", 1, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        self.printMsg("config init succeed")

    def main(self):
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
        if self.isSaveVideoUrl == 1:
            imageUrlLogFileDir = os.path.dirname(self.imageUrlLogFilePath)
            if not os.path.exists(imageUrlLogFileDir):
                if not self.createDir(imageUrlLogFileDir):
                    self.printErrorMsg("create " + imageUrlLogFileDir + " error")
                    self.processExit()
                self.printStepMsg("image URL log file path is not exist, create it: " + imageUrlLogFileDir)
        if self.isSaveVideoUrl == 1:
            videoFileDir = os.path.dirname(self.videoFilePath)
            if not os.path.exists(videoFileDir):
                if not self.createDir(videoFileDir):
                    self.printErrorMsg("create " + videoFileDir + " error")
                    self.processExit()
                self.printStepMsg("video URL file path is not exist, create it: " + videoFileDir)
        if self.isDownloadImage == 1:
            if os.path.exists(self.imageDownloadPath):
                if os.path.isdir(self.imageDownloadPath):
                    isDelete = False
                    while not isDelete:
                        input = raw_input(self.imageDownloadPath + "is exist, do you want to remove it and continue? (Y)es or (N)o: ")
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
            self.printStepMsg("created  image download path: " + self.imageDownloadPath)
            if not self.createDir(self.imageDownloadPath):
                self.printErrorMsg("create " + self.imageDownloadPath + " error")
                self.processExit()
        # 设置代理
        if self.isProxy == 1:
            self.proxy()
        
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
        newMemberUIdListFilePath = os.getcwd() + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.memberUIdListFilePath)[-1]
        newMemberUIdListFile = open(newMemberUIdListFilePath, 'w')
        newMemberUIdListFile.close()

        newMemberUIdList = copy.deepcopy(userIdList)
        for newUserId in newMemberUIdList:
            # 如果没有名字，则名字用uid代替
            if len(newMemberUIdList[newUserId]) < 2:
                newMemberUIdList[newUserId].append(newMemberUIdList[newUserId][0])
            # 如果没有出事image count，则为0
            if len(newMemberUIdList[newUserId]) < 3:
                newMemberUIdList[newUserId].append("0")
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(newMemberUIdList[newUserId]) < 4:
                newMemberUIdList[newUserId].append("")
            else:
                newMemberUIdList[newUserId][3] = ""
            # 处理member 队伍信息
            if len(newMemberUIdList[newUserId]) < 5:
                newMemberUIdList[newUserId].append("")
        allImageCount = 0
        allVideoCount = 0
        for userId in userIdList:
            errCount = 0
            isPass = False
            isFirstVideoId = True
            isFirstVideoUrl = True
            userName = newMemberUIdList[userId][1]
            self.printStepMsg("UID: " + str(userId) + ", Member: " + userName)
            
            if self.isSort == 1:
                imagePath = self.imageDownloadPath + "\\" + self.imageTmpDirName
            else:
                imagePath = self.imageDownloadPath + "\\" + userName
            if not self.createDir(imagePath):
                self.printErrorMsg("create " + imagePath + " error")
                self.processExit()
            # 日志文件插入信息
            if self.isSaveMessageUrl == 1:
                self.writeFile(userId + " " + userName, self.messageUrlLogFilePath, isTime=False)
            if self.isSaveImageUrl == 1:
                self.writeFile(userId + " " + userName, self.imageUrlLogFilePath, isTime=False)
                
            # 初始化数据
            pageCount = 0
            imageCount = 1
            videoCount = 1
            messageUrlList = []
            imageUrlList = []
            videoIdList = []
            videoUrlList = []
            postMessage = None
            while 1:
                if isPass:
                        break
                # 获取信息总页,offset=N表示返回最新的N到N+100条信息所在的url
                photoAlbumUrl = "https://plus.google.com/_/photos/posts/%s?offset=%s" % (userId, pageCount)
                self.trace("photo Album URL:" + photoAlbumUrl)
                photoAlbumPage = self.doGet(photoAlbumUrl)
                if not photoAlbumPage:
                    self.printErrorMsg("can not get photoAlbumPage: " + photoAlbumUrl)
                    pageCount += 100
                    if errCount >= 5:
                        self.printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                        newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                        allImageCount += imageCount - 1
                        allVideoCount += videoCount - 1
                        isPass = True
                        break
                    errCount += 1
                    continue
                 
                # 判断信息总页字节数大小，是否小于300
                if len(photoAlbumPage) < 300:
                    self.printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                    if self.version == 1:
                        newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                    else:
                        newMemberUIdList[userId][2] = newMemberUIdList[userId][2]
                    allImageCount += imageCount - 1
                    allVideoCount += videoCount - 1
                    break
                    
                messageIndex = 1
                while messageIndex != 0:
                    if isPass:
                        break
                    if self.version == 1:
                        messageIndex = photoAlbumPage.find("plus.google.com/photos/" + userId + "/albums/", messageIndex)
                        messageStart = photoAlbumPage.find("http", messageIndex - 10)
                        messageStop = photoAlbumPage.find('"', messageStart)
                        messageUrl = photoAlbumPage[messageStart:messageStop]
                    else:
                        messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex)
                        messageStart = photoAlbumPage.find("http", messageIndex)
                        messageStop = photoAlbumPage.find('"', messageStart)
                        messageUrl = photoAlbumPage[messageStart:messageStop]
                    if messageIndex == -1:
                        break
                    
                    # 将第一张image的URL保存到新id list中
                    if newMemberUIdList[userId][3] == "":
                        newMemberUIdList[userId][3] = messageUrl
                    if len(userIdList[userId]) >= 4 and userIdList[userId][3].find("picasaweb.google.com/"):
                        if messageUrl == userIdList[userId][3]:
                            self.printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                            if self.version == 1:
                                newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                            else:
                                newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                            allImageCount += imageCount - 1
                            allVideoCount += videoCount - 1
                            isPass = True
                            break
                    self.trace("message URL:" + messageUrl)
                    if not (messageUrl in messageUrlList):
                        messageUrlList.append(messageUrl)
                        if self.isSaveMessageUrl == 1:
                            self.writeFile(messageUrl, self.messageUrlLogFilePath)
                        messagePage = self.doGet(messageUrl)
                        if not messagePage:
                            self.printErrorMsg("can not get messagePage: " + messageUrl)
                            messageIndex += 1
                            continue
                        # video
                        if self.isSaveVideoUrl == 1:
                            videoIdIndex = messagePage.find("redirector.googlevideo.com")
                            while videoIdIndex != -1:
                                if self.version == 1:
                                    videoIdStart = messagePage.find("id\u003d", videoIdIndex)
                                    videoIdStop = messagePage.find("\u0026", videoIdStart)
                                else:
                                    videoIdStart = messagePage.find("?id=", videoIdIndex)
                                    videoIdStop = messagePage.find("&", videoIdStart)
                                videoId = messagePage[videoIdStart + 8:videoIdStop]
                                if not (videoId in videoIdList):
                                    videoIdList.append(videoId)
                                    if isFirstVideoId:
                                        self.writeFile(userId + " " + userName, self.videoFilePath, isTime=False)
                                        isFirstVideoId = False
                                    self.writeFile(str(videoCount) + ": " + videoId + " " + messageUrl, self.videoFilePath, isTime=False)
                                    self.printStepMsg("video " + str(videoCount) + ": " + videoId)
                                    if self.isSaveVideoDownloadUrl == 1:
                                        if postMessage == None:
                                            postMessage = self.doGet("https://plus.google.com/photos/" + str(userId) + "/albums/posts")
                                        if postMessage:
                                            videoUrlIndex = postMessage.find("video.googleusercontent.com", postMessage.find(videoId))
                                            videoUrlStart = postMessage.find("http", videoUrlIndex - 10)
                                            videoUrlStop = postMessage.find('"' , videoUrlStart)
                                            videoUrl = postMessage[videoUrlStart:videoUrlStop]
                                            videoUrl = videoUrl.replace("\u003d", '=')
                                            if not videoUrl in videoUrlList:
                                                videoUrlList.append(videoUrl)
                                                self.printStepMsg("video download url: " + videoUrl)
                                                if isFirstVideoUrl:
                                                    self.writeFile(userId + " " + userName, self.videoUrlFilePath, isTime=False)
                                                    isFirstVideoUrl = False
                                                self.writeFile(str(videoCount) + ": " + videoUrl, self.videoUrlFilePath, isTime=False)
                                    videoCount += 1
                                videoIdIndex = messagePage.find("redirector.googlevideo.com", videoIdIndex + 1)
                        # picture
                        if self.isDownloadImage == 1:
                            if self.version == 1:
                                picasawebIndex = messagePage.find("picasaweb.google.com/" + userId)
                                if picasawebIndex != -1:
                                    picasawebStart = messagePage.find("http", picasawebIndex - 10)
                                    picasawebStop = messagePage.find('"', picasawebStart)
                                    picasawebUrl = messagePage[picasawebStart:picasawebStop]
                                    self.trace("picasaweb URL:" + picasawebUrl)
                                    picasawebPage = self.doGet(picasawebUrl)
                                    if not picasawebPage:
                                        self.printErrorMsg("can not get picasawebPage: " + picasawebUrl)
                                        messageIndex += 1
                                        continue
                                    imageIndex = picasawebPage.find('"media":')
                                    while imageIndex != -1:
                                        imageStart = picasawebPage.find("http", imageIndex)
                                        imageStop = picasawebPage.find('"', imageStart)
                                        imageUrl = picasawebPage[imageStart:imageStop]
                                        self.trace("image URL:" + imageUrl)                       
                                        if not (imageUrl in imageUrlList):
                                            imageUrlList.append(imageUrl)
                                            if self.isSaveVideoUrl == 1:
                                                self.writeFile(str(imageCount) + ": " + imageUrl + "  " + messageUrl + "  " + photoAlbumUrl, self.imageUrlLogFilePath, isTime=False)
                                            imageResizeIndex = 0
                                            for index in range(imageUrl.count("/")):
                                                imageResizeIndex = imageUrl.find("/", imageResizeIndex) + 1
                                            imageUrl = imageUrl[:imageResizeIndex] + "s0/" + imageUrl[imageResizeIndex:]
                                            fileType = imageUrl.split(".")[-1]
                                            imgByte = self.doGet(imageUrl)
                                            if imgByte:
                                                filename = str("%04d" % imageCount)
                                                imageFile = open(imagePath + "\\" + str(filename) + "." + fileType, "wb")
                                                self.printStepMsg("start download " + str(imageCount) + ": " + imageUrl)
                                                imageFile.write(imgByte)
                                                imageFile.close()
                                                self.printStepMsg("download succeed")
                                                imageCount += 1
                                                if self.getImageCount > 0 and imageCount > self.getImageCount:
                                                    self.printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                                                    if self.version == 1:
                                                        newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                                                    else:
                                                        newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                                                    allImageCount += imageCount - 1
                                                    allVideoCount += videoCount - 1
                                                    isPass = True
                                                    break
                                            else:
                                                self.printErrorMsg("image path not found: " + imageUrl)
                                        imageIndex = picasawebPage.find('"media":', imageIndex + 1)
                                else:
                                    self.printErrorMsg("picasaweb.google.com not found in " + messageUrl)
                            else:
                                flag = messagePage.find("<div><a href=")
                                while flag != -1:
                                    imageIndex = messagePage.find("<img src=", flag, flag + 200)
                                    if imageIndex != -1:
                                        imageStart = messagePage.find("http", imageIndex)
                                        imageStop = messagePage.find('"', imageStart)
                                        imageUrl = messagePage[imageStart:imageStop]
                                        self.trace("image URL:" + imageUrl)                       
                                        if not (imageUrl in imageUrlList):
                                            tempList = imageUrl.split("/")
                                            tempList[-2] = "s0"
                                            imageUrl = "/".join(tempList)
                                            fileType = imageUrl.split(".")[-1]
                                            imgByte = self.doGet(imageUrl)
                                            if imgByte:
                                                filename = str("%04d" % imageCount)
                                                imageFile = open(imagePath + "\\" + str(filename) + "." + fileType, "wb")
                                                self.printStepMsg("start download " + str(imageCount) + ": " + imageUrl)
                                                imageFile.write(imgByte)
                                                imageFile.close()
                                                self.printStepMsg("download succeed")
                                                imageCount += 1
                                                if self.getImageCount > 0 and imageCount > self.getImageCount:
                                                    self.printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                                                    if self.version == 1:
                                                        newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                                                    else:
                                                        newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                                                    allImageCount += imageCount - 1
                                                    allVideoCount += videoCount - 1
                                                    isPass = True
                                                    break
                                    else:
                                        self.printErrorMsg("'<img src=' not found  in " + messageUrl)
                                        continue
                                    flag = messagePage.find("<div><a href=", flag + 1)
                    messageIndex += 1
                pageCount += 100
                
            if self.isSaveMessageUrl == 1:
                self.writeFile("****************************************************************************************************", self.messageUrlLogFilePath, isTime=False)
            if self.isSaveImageUrl == 1:
                self.writeFile("****************************************************************************************************", self.imageUrlLogFilePath, isTime=False)
            if self.isSaveVideoUrl == 1 and not isFirstVideoId:
                self.writeFile("****************************************************************************************************", self.videoFilePath, isTime=False)
            if self.isSaveVideoDownloadUrl == 1 and not isFirstVideoUrl:
                self.writeFile("****************************************************************************************************", self.videoUrlFilePath, isTime=False)
            
            # 排序
            if self.isDownloadImage == 1 and self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + newMemberUIdList[userId][4] + "\\" + userName
                    if os.path.exists(destPath):
                        if os.path.isdir(destPath):
                            self.printStepMsg("image download path: " + destPath + " is exist, remove all files in it")
                            self.removeDirFiles(destPath)
                        else:
                            self.printStepMsg("image download path: " + destPath + " is a file, delete it")
                            os.remove(destPath)
                            if not self.createDir(destPath):
                                self.printErrorMsg("create " + destPath + " error")
                                self.processExit()
                    else:
                        self.printStepMsg("create image download path: " + destPath)
                        if not self.createDir(destPath):
                            self.printErrorMsg("create " + destPath + " error")
                            self.processExit()
        
                    # 倒叙排列
                    if len(userIdList[userId]) >= 3:
                        count = int(userIdList[userId][2]) + 1
                    else:
                        count = 1
                    for fileName in imageList:
                        fileType = fileName.split(".")[1]
                        shutil.copyfile(imagePath + "\\" + fileName, destPath + "\\" + str("%04d" % count) + "." + fileType)
                        count += 1
                    self.printStepMsg("sorted over, continue next member")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)
        
                # 保存最后的信息
                newMemberUIdListFile = open(newMemberUIdListFilePath, 'a')
                newMemberUIdListFile.write("\t".join(newMemberUIdList[userId]) + "\n")
                newMemberUIdListFile.close()        

        # 保存新的idList.txt
        tmpList = []
        tmpUserIdList = sorted(newMemberUIdList.keys())
        for index in tmpUserIdList:
            tmpList.append("\t".join(newMemberUIdList[index]))
        newMemberUIdListString = "\n".join(tmpList)
        newMemberUIdListFilePath = os.getcwd() + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.memberUIdListFilePath)[-1]
        self.printStepMsg("save new id list file: " + newMemberUIdListFilePath)
        newMemberUIdListFile = open(newMemberUIdListFilePath, 'w')
        newMemberUIdListFile.write(newMemberUIdListString)
        newMemberUIdListFile.close()
        
        stopTime = time.time()
        self.printStepMsg("all members' image download succeed, use " + str(int(stopTime - startTime)) + " seconds, sum download image count: " + str(allImageCount) + ", video count: " + str(allVideoCount))

if __name__ == '__main__':
    downloadImage().main()
