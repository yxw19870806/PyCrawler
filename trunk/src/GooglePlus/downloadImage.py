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
        if config.has_key("MESSAGE_URL_LOG_FILE_NAME"):
            self.messageUrlLogFilePath = processPath + "\\" + config["MESSAGE_URL_LOG_FILE_NAME"]
        else:
            self.printMsg("Not found 'MESSAGE_URL_LOG_FILE_NAME' in config.ini, default value")
            self.messageUrlLogFilePath = processPath + "\\log\\messageLog.txt"
        if config.has_key("IMAGE_URL_LOG_FILE_NAME"):
            self.imageUrlLogFilePath = processPath + "\\" + config["IMAGE_URL_LOG_FILE_NAME"]
        else:
            self.printMsg("Not found 'IMAGE_URL_LOG_FILE_NAME' in config.ini, default value")
            self.imageUrlLogFilePath = processPath + "\\log\\messageLog.txt"
        if config.has_key("VIDEO_FILE_NAME"):
            self.videoFilePath = processPath + "\\" + config["VIDEO_FILE_NAME"]
        else:
            self.printMsg("Not found 'VIDEO_FILE_NAME' in config.ini, default value")
            self.videoFilePath = processPath + "\\video.txt"
        if config.has_key("VIDEO_DOWNLOAD_URL_FILE_NAME"):
            self.videoUrlFilePath = processPath + "\\" + config["VIDEO_DOWNLOAD_URL_FILE_NAME"]
        else:
            self.printMsg("Not found 'VIDEO_DOWNLOAD_URL_FILE_NAME' in config.ini, default value")
            self.videoUrlFilePath = processPath + "\\videoDownloadUrl.txt"
        if config.has_key("ERROR_LOG_FILE_NAME"):
            self.errorLogPath = processPath + "\\" + config["ERROR_LOG_FILE_NAME"]
        else:
            self.printMsg("Not found 'ERROR_LOG_FILE_NAME' in config.ini, default value")
            self.errorLogPath = processPath + "\\log\\errorLog.txt"
        if config.has_key("TRACE_LOG_FILE_NAME"):
            self.traceLogPath = processPath + "\\" + config["TRACE_LOG_FILE_NAME"]
        else:
            self.printMsg("Not found 'TRACE_LOG_FILE_NAME' in config.ini, default value")
            self.traceLogPath = processPath + "\\log\\traceLog.txt"
        if config.has_key("STEP_LOG_FILE_NAME"):
            self.stepLogPath = processPath + "\\" + config["STEP_LOG_FILE_NAME"]
        else:
            self.printMsg("Not found 'STEP_LOG_FILE_NAME' in config.ini, default value")
            self.stepLogPath = processPath + "\\log\\stepLog.txt"
        if config.has_key("IMAGE_DOWNLOAD_DIR_NAME"):
            self.imageDownloadPath = processPath + "\\" + config["IMAGE_DOWNLOAD_DIR_NAME"]
        else:
            self.printMsg("Not found 'IMAGE_DOWNLOAD_DIR_NAME' in config.ini, default value")
            self.imageDownloadPath = processPath + "\\download"
        if config.has_key("IMAGE_TEMP_DIR_NAME"):
            self.imageTmpDirName = config["IMAGE_TEMP_DIR_NAME"]
        else:
            self.printMsg("Not found 'IMAGE_TEMP_DIR_NAME' in config.ini, default value")
            self.imageTmpDirName = "temp"
        if config.has_key("MEMBER_UID_LIST_FILE_NAME"):
            self.memberUIdListFilePath = processPath + "\\" + config["MEMBER_UID_LIST_FILE_NAME"]
        else:
            self.printMsg("Not found 'MEMBER_UID_LIST_FILE_NAME' in config.ini, default value")
            self.memberUIdListFilePath = processPath + "\\idlist.txt"
        # 配置文件获取程序配置
#         if config.has_key("self.version"):
#             try:
#                 self.version = int(config["self.version"])
#             except:
#                 self.printMsg("'self.version' must is a number in config.ini, default value")
#                 self.version = 1
#         else:
#             self.printMsg("Not found 'self.version' in config.ini, default value")
#             self.version = 1
        if config.has_key("IS_LOG"):
            try:
                self.isLog = int(config["IS_LOG"])
            except:
                self.printMsg("'IS_LOG' must is a number in config.ini, default value")
                self.isLog = 1
        else:
            self.printMsg("Not found 'IS_LOG' in config.ini, default value")
            self.isLog = 1
        if config.has_key("IS_SHOW_ERROR"):
            try:
                self.isShowError = int(config["IS_SHOW_ERROR"])
            except:
                self.printMsg("'IS_SHOW_ERROR' must is a number in config.ini, default value")
                self.isShowError = 1
        else:
            self.printMsg("Not found 'IS_SHOW_ERROR' in config.ini, default value")
            self.isShowError = 1
        if config.has_key("IS_DEBUG"):
            try:
                self.isDebug = int(config["IS_DEBUG"])
            except:
                self.printMsg("'IS_DEBUG' must is a number in config.ini, default value")
                self.isDebug = 1
        else:
            self.printMsg("Not found 'IS_DEBUG' in config.ini, default value")
            self.isDebug = 1
        if config.has_key("IS_SHOW_STEP"):
            try:
                self.isShowStep = int(config["IS_SHOW_STEP"])
            except:
                self.printMsg("'IS_SHOW_STEP' must is a number in config.ini, default value")
                self.isShowStep = 1
        else:
            self.printMsg("Not found 'IS_SHOW_STEP' in config.ini, default value")
            self.isShowStep = 1
        if config.has_key("IS_SAVE_MESSAGE_URL"):
            try:
                self.isSaveMessageUrl = int(config["IS_SAVE_MESSAGE_URL"])
            except:
                self.printMsg("'IS_SAVE_MESSAGE_URL' must is a number in config.ini, default value")
                self.isSaveMessageUrl = 1
        else:
            self.printMsg("Not found 'IS_SAVE_MESSAGE_URL' in config.ini, default value")
            self.isSaveMessageUrl = 1
        if config.has_key("IS_SAVE_IMAGE_URL"):
            try:
                self.isSaveImageUrl = int(config["IS_SAVE_IMAGE_URL"])
            except:
                self.printMsg("'IS_SAVE_IMAGE_URL' must is a number in config.ini, default value")
                self.isSaveImageUrl = 1
        else:
            self.printMsg("Not found 'IS_SAVE_IMAGE_URL' in config.ini, default value")
            self.isSaveImageUrl = 1
        if config.has_key("iS_SAVE_VIDEO_URL"):
            try:
                self.isSaveVideoUrl = int(config["iS_SAVE_VIDEO_URL"])
            except:
                self.printMsg("'iS_SAVE_VIDEO_URL' must is a number in config.ini, default value")
                self.isSaveVideoUrl = 1
        else:
            self.printMsg("Not found 'iS_SAVE_VIDEO_URL' in config.ini, default value")
            self.isSaveVideoUrl = 1
        if config.has_key("iS_SAVE_VIDEO_DOWNLOAD_URL"):
            try:
                self.isSaveVideoDownloadUrl = int(config["iS_SAVE_VIDEO_DOWNLOAD_URL"])
            except:
                self.printMsg("'iS_SAVE_VIDEO_DOWNLOAD_URL' must is a number in config.ini, default value")
                self.isSaveVideoDownloadUrl = 1
        else:
            self.printMsg("Not found 'iS_SAVE_VIDEO_DOWNLOAD_URL' in config.ini, default value")
            self.isSaveVideoDownloadUrl = 1
        if config.has_key("IS_DOWNLOAD_IMAGE"):
            try:
                self.isDownloadImage = int(config["IS_DOWNLOAD_IMAGE"])
            except:
                self.printMsg("'IS_DOWNLOAD_IMAGE' must is a number in config.ini, default value")
                self.isDownloadImage = 1
        else:
            self.printMsg("Not found 'IS_DOWNLOAD_IMAGE' in config.ini, default value")
            self.isDownloadImage = 1
        if config.has_key("IS_SORT"):
            try:
                self.isSort = int(config["IS_SORT"])
            except:
                self.printMsg("'IS_SORT' must is a number in config.ini, default value")
                self.isSort = 1
        else:
            self.printMsg("Not found 'IS_SORT' in config.ini, default value")
            self.isSort = 1
        if config.has_key("GET_IMAGE_COUNT"):
            try:
                self.getImageCount = int(config["GET_IMAGE_COUNT"])
            except:
                self.printMsg("'GET_IMAGE_COUNT' must is a number in config.ini, default value")
                self.getImageCount = 0
        else:
            self.printMsg("Not found 'GET_IMAGE_COUNT' in config.ini, default value")
            self.getImageCount = 0
        if config.has_key("IS_PROXY"):
            try:
                self.isProxy = int(config["IS_PROXY"])
            except:
                self.printMsg("'IS_PROXY' must is a number in config.ini, default value")
                self.isProxy = 0
        else:
            self.isProxy = 0
        if self.isProxy == 1:
            if config.has_key("PROXY_IP"):
                self.proxyIp = config["PROXY_IP"]
            else:
                self.printMsg("Not found proxy IP in config.ini! process stop!")
                self.processExit()
            if config.has_key("PROXY_PORT"):
                self.proxyPort = config["PROXY_PORT"]
            else:
                self.printMsg("Not found proxy port in config.ini! process stop!")
                self.processExit()
        self.printMsg("config init succeed")

    def proxy(self):
            proxyHandler = urllib2.ProxyHandler({'https':"http://" + self.proxyIp + ":" + self.proxyPort})
            opener = urllib2.build_opener(proxyHandler)
            urllib2.install_opener(opener)
            self.printStepMsg("proxy set succeed")
        
    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not os.path.exists(stepLogDir):
                os.makedirs(stepLogDir)
                self.printStepMsg("step log file path is not exist, create it: " + stepLogDir)
            errorLogDir = os.path.dirname(self.errorLogPath)
            if not os.path.exists(errorLogDir):
                os.makedirs(errorLogDir)
                self.printStepMsg("error log file path is not exist, create it: " + errorLogDir)
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not os.path.exists(traceLogDir):
                os.makedirs(traceLogDir)
                self.printStepMsg("trace log file path is not exist, create it: " + traceLogDir)
        if self.isSaveMessageUrl == 1:
            messageUrlLogFileDir = os.path.dirname(self.messageUrlLogFilePath)
            if not os.path.exists(messageUrlLogFileDir):
                os.makedirs(messageUrlLogFileDir)
                self.printStepMsg("message URL log file path is not exist, create it: " + messageUrlLogFileDir)
        if self.isSaveVideoUrl == 1:
            imageUrlLogFileDir = os.path.dirname(self.imageUrlLogFilePath)
            if not os.path.exists(imageUrlLogFileDir):
                self.printStepMsg("image URL log file path is not exist, create it: " + imageUrlLogFileDir)
                os.makedirs(imageUrlLogFileDir)
        if self.isSaveVideoUrl == 1:
            videoFileDir = os.path.dirname(self.videoFilePath)
            if not os.path.exists(videoFileDir):
                self.printStepMsg("video URL file path is not exist, create it: " + videoFileDir)
                os.makedirs(videoFileDir)
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
            os.makedirs(self.imageDownloadPath)
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
            userName = newMemberUIdList[userId][1]
            self.printStepMsg("UID: " + str(userId) + ", Member: " + userName)
            
            imagePath = self.imageDownloadPath + "\\" + self.imageTmpDirName
            if os.path.exists(imagePath):
                shutil.rmtree(imagePath, True)
            os.makedirs(imagePath)
            
            # 日志文件插入信息
            if self.isSaveMessageUrl == 1:
                self.writeFile(userId + " " + userName, self.messageUrlLogFilePath, isTime=False)
            if self.isSaveImageUrl == 1:
                self.writeFile(userId + " " + userName, self.imageUrlLogFilePath, isTime=False)
            if self.isSaveVideoUrl == 1:
                self.writeFile(userId + " " + userName, self.videoFilePath, isTime=False)
            if self.isSaveVideoDownloadUrl == 1:
                self.writeFile(userId + " " + userName, self.videoUrlFilePath, isTime=False)
                
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
                    newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                    allImageCount += imageCount - 1
                    allVideoCount += videoCount - 1
                    break
                    
                messageIndex = 1
                while messageIndex != 0:
                    if isPass:
                        break            
                    messageIndex = photoAlbumPage.find("plus.google.com/photos/" + userId + "/albums/", messageIndex)
                    if messageIndex == -1:
                        break
                    messageStart = photoAlbumPage.find("http", messageIndex - 10)
                    messageStop = photoAlbumPage.find('"', messageStart)
                    messageUrl = photoAlbumPage[messageStart:messageStop]
                    # 将第一张image的URL保存到新id list中
                    if newMemberUIdList[userId][3] == "":
                        newMemberUIdList[userId][3] = messageUrl
                    if len(userIdList[userId]) >= 4 and userIdList[userId][3].find("plus.google.com/photos/" + str(userId) + "/albums/"):
                        if messageUrl == userIdList[userId][3]:
                            self.printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
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
                                videoIdStart = messagePage.find("id\u003d", videoIdIndex)
                                videoIdStop = messagePage.find("\u0026", videoIdStart)
                                videoId = messagePage[videoIdStart + 8:videoIdStop]
                                if not (videoId in videoIdList):
                                    videoIdList.append(videoId)
                                    self.writeFile(str(videoCount) + ": " + videoId + " " + messageUrl, self.videoFilePath, isTime=False)
                                    self.printStepMsg("video " + str(videoCount) + ": " + videoId)
                                    if self.isSaveVideoDownloadUrl == 1:
                                        if postMessage == None:
                                            postMessage = self.doGet("https://plus.google.com/photos/" + str(userId) + "/albums/posts")
                                        if postMessage:
                                            videoUrlStart = postMessage.find("video.googleusercontent.com", postMessage.find(videoId))
                                            videoUrlStop = postMessage.find('"' , videoUrlStart)
                                            videoUrl = postMessage[videoUrlStart:videoUrlStop]
                                            videoUrl = videoUrl.replace("\u003d", '=')
                                            if not videoUrl in videoUrlList:
                                                videoUrlList.append(videoUrl)
                                                self.printStepMsg("video download url: " + videoUrl)
                                                self.writeFile(str(videoCount) + ": " + videoUrl, self.videoUrlFilePath, isTime=False)
                                        videoCount += 1
                                videoIdIndex = messagePage.find("redirector.googlevideo.com", videoIdIndex + 1)
        # #                         http://redirector.googlevideo.com/videoplayback?id\u003de3d428eb43ded4ec\u0026itag\u003d36\u0026source\u003dp
        #                         messageId = messageUrl.split("/albums/")[-1]
        #                         
        #                         videoPageUrl = "https://plus.google.com/photos/" + userId + "/albums/posts/" + messageId + "?pid=" + messageId + "&oid=" + userId
        #                         videoPage = doGet(videoPageUrl)
        #                         print videoPageUrl
        # #                         https://plus.google.com/photos/104832409151547328144/albums/5878936582792776369/5878936581433789618?pid=5878936581433789618&oid=104832409151547328144
        #                         videoIndex = videoPage.find("video.googleusercontent.com")
        #                         while videoIndex != -1:
        #                             if messagePage.find("token", videoIndex, videoIndex + 50) != -1:
        #                                 videStart = messagePage.find("http", videoIndex - 10)
        #                                 videStop = messagePage.find('"', videStart)
        #                                 videoUrl = messagePage[videStart:videStop]
        #                                 trace("video URL:" + videoUrl)
        #                                 if not(videoUrl in videoUrlList):
        #                                     videoUrlList.append(videoUrl)
        #                                     videoUrl = videoUrl.replace("\u003d", '=')
        #                                     writeFile(str(videoCount) + ": " + videoUrl + "  " + messageUrl + "  " + photoAlbumUrl, self.videoFilePath, isTime=False)
        #                                     self.printStepMsg("video " + str(videoCount) + ": " + videoUrl)
        #                                     videoCount += 1
        #                                     isFindVideo = True
        #                             videoIndex = messagePage.find("video.googleusercontent.com", videoIndex + 1)
                        # picture
                        if self.isDownloadImage == 1:
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
                                                allImageCount += imageCount - 1
                                                allVideoCount += videoCount - 1
                                                isPass = True
                                                break
                                        else:
                                            self.printErrorMsg("image path not found: " + imageUrl)
                                    imageIndex = picasawebPage.find('"media":', imageIndex + 1)
                            else:
                                self.printErrorMsg("picasaweb.google.com not found in " + messageUrl)
                    messageIndex += 1
                pageCount += 100
                
            if self.isSaveMessageUrl == 1:
                self.writeFile("****************************************************************************************************", self.messageUrlLogFilePath, isTime=False)
            if self.isSaveImageUrl == 1:
                self.writeFile("****************************************************************************************************", self.imageUrlLogFilePath, isTime=False)
            if self.isSaveVideoUrl == 1:
                self.writeFile("****************************************************************************************************", self.videoFilePath, isTime=False)
            if self.isSaveVideoDownloadUrl == 1:
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
                            os.makedirs(destPath)
                    else:
                        self.printStepMsg("create image download path: " + destPath)
                        os.makedirs(destPath)
        
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
