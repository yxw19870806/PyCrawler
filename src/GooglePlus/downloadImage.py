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

startTime = time.time()
isNewFunc = 48

def processExit():
    sys.exit()

def printMsg(msg):
    print msg
    
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
            pass

# 配置文件获取日志文件路径
if config.has_key("MESSAGE_URL_LOG_FILE_NAME"):
    messageUrlLogFilePath = processPath + "\\" + config["MESSAGE_URL_LOG_FILE_NAME"]
else:
    printMsg("Not found 'MESSAGE_URL_LOG_FILE_NAME' in config.ini, default value")
    messageUrlLogFilePath = processPath + "\\log\\messageLog.txt"
if config.has_key("IMAGE_URL_LOG_FILE_NAME"):
    imageUrlLogFilePath = processPath + "\\" + config["IMAGE_URL_LOG_FILE_NAME"]
else:
    printMsg("Not found 'IMAGE_URL_LOG_FILE_NAME' in config.ini, default value")
    imageUrlLogFilePath = processPath + "\\log\\messageLog.txt"
if config.has_key("VIDEO_FILE_NAME"):
    videoFilePath = processPath + "\\" + config["VIDEO_FILE_NAME"]
else:
    printMsg("Not found 'VIDEO_FILE_NAME' in config.ini, default value")
    videoFilePath = processPath + "\\video.txt"
if config.has_key("ERROR_LOG_FILE_NAME"):
    errorLogPath = processPath + "\\" + config["ERROR_LOG_FILE_NAME"]
else:
    printMsg("Not found 'ERROR_LOG_FILE_NAME' in config.ini, default value")
    errorLogPath = processPath + "\\log\\errorLog.txt"
if config.has_key("TRACE_LOG_FILE_NAME"):
    traceLogPath = processPath + "\\" + config["TRACE_LOG_FILE_NAME"]
else:
    printMsg("Not found 'TRACE_LOG_FILE_NAME' in config.ini, default value")
    traceLogPath = processPath + "\\log\\traceLog.txt"
if config.has_key("STEP_LOG_FILE_NAME"):
    stepLogPath = processPath + "\\" + config["STEP_LOG_FILE_NAME"]
else:
    printMsg("Not found 'STEP_LOG_FILE_NAME' in config.ini, default value")
    stepLogPath = processPath + "\\log\\stepLog.txt"
if config.has_key("IMAGE_DOWNLOAD_DIR_NAME"):
    imageDownloadPath = processPath + "\\" + config["IMAGE_DOWNLOAD_DIR_NAME"]
else:
    printMsg("Not found 'IMAGE_DOWNLOAD_DIR_NAME' in config.ini, default value")
    imageDownloadPath = processPath + "\\download"
if config.has_key("IMAGE_TEMP_DIR_NAME"):
    imageTmpDirName = config["IMAGE_TEMP_DIR_NAME"]
else:
    printMsg("Not found 'IMAGE_TEMP_DIR_NAME' in config.ini, default value")
    imageTmpDirName = "temp"
if config.has_key("MEMBER_UID_LIST_FILE_NAME"):
    memberUIdListFilePath = processPath + "\\" + config["MEMBER_UID_LIST_FILE_NAME"]
else:
    printMsg("Not found 'MEMBER_UID_LIST_FILE_NAME' in config.ini, default value")
    memberUIdListFilePath = processPath + "\\idlist.txt"

# 配置文件获取程序配置
if config.has_key("VERSION"):
    try:
        version = int(config["VERSION"])
    except:
        printMsg("'VERSION' must is a number in config.ini, default value")
        version = 1
else:
    printMsg("Not found 'VERSION' in config.ini, default value")
    version = 1
if config.has_key("IS_LOG"):
    try:
        isLog = int(config["IS_LOG"])
    except:
        printMsg("'IS_LOG' must is a number in config.ini, default value")
        isLog = 1
else:
    printMsg("Not found 'IS_LOG' in config.ini, default value")
    isLog = 1
if config.has_key("IS_SHOW_ERROR"):
    try:
        isShowError = int(config["IS_SHOW_ERROR"])
    except:
        printMsg("'IS_SHOW_ERROR' must is a number in config.ini, default value")
        isShowError = 1
else:
    printMsg("Not found 'IS_SHOW_ERROR' in config.ini, default value")
    isShowError = 1
if config.has_key("IS_DEBUG"):
    try:
        isDebug = int(config["IS_DEBUG"])
    except:
        printMsg("'IS_DEBUG' must is a number in config.ini, default value")
        isDebug = 1
else:
    printMsg("Not found 'IS_DEBUG' in config.ini, default value")
    isDebug = 1
if config.has_key("IS_SHOW_STEP"):
    try:
        isShowStep = int(config["IS_SHOW_STEP"])
    except:
        printMsg("'IS_SHOW_STEP' must is a number in config.ini, default value")
        isShowStep = 1
else:
    printMsg("Not found 'IS_SHOW_STEP' in config.ini, default value")
    isShowStep = 1
if config.has_key("IS_SAVE_MESSAGE_URL"):
    try:
        isSaveMessageUrl = int(config["IS_SAVE_MESSAGE_URL"])
    except:
        printMsg("'IS_SAVE_MESSAGE_URL' must is a number in config.ini, default value")
        isSaveMessageUrl = 1
else:
    printMsg("Not found 'IS_SAVE_MESSAGE_URL' in config.ini, default value")
    isSaveMessageUrl = 1
if config.has_key("IS_SAVE_IMAGE_URL"):
    try:
        isSaveImageUrl = int(config["IS_SAVE_IMAGE_URL"])
    except:
        printMsg("'IS_SAVE_IMAGE_URL' must is a number in config.ini, default value")
        isSaveImageUrl = 1
else:
    printMsg("Not found 'IS_SAVE_IMAGE_URL' in config.ini, default value")
    isSaveImageUrl = 1
if config.has_key("iS_SAVE_VIDEO_URL"):
    try:
        isSaveVideoUrl = int(config["iS_SAVE_VIDEO_URL"])
    except:
        printMsg("'iS_SAVE_VIDEO_URL' must is a number in config.ini, default value")
        isSaveVideoUrl = 1
else:
    printMsg("Not found 'iS_SAVE_VIDEO_URL' in config.ini, default value")
    isSaveVideoUrl = 1
if config.has_key("IS_DOWNLOAD_IMAGE"):
    try:
        isDownloadImage = int(config["IS_DOWNLOAD_IMAGE"])
    except:
        printMsg("'IS_DOWNLOAD_IMAGE' must is a number in config.ini, default value")
        isDownloadImage = 1
else:
    printMsg("Not found 'IS_DOWNLOAD_IMAGE' in config.ini, default value")
    isDownloadImage = 1
if config.has_key("IS_SORT"):
    try:
        isSort = int(config["IS_SORT"])
    except:
        printMsg("'IS_SORT' must is a number in config.ini, default value")
        isSort = 1
else:
    printMsg("Not found 'IS_SORT' in config.ini, default value")
    isSort = 1
if config.has_key("GET_IMAGE_COUNT"):
    try:
        getImageCount = int(config["GET_IMAGE_COUNT"])
    except:
        printMsg("'GET_IMAGE_COUNT' must is a number in config.ini, default value")
        getImageCount = 0
else:
    printMsg("Not found 'GET_IMAGE_COUNT' in config.ini, default value")
    getImageCount = 0    

def getTime():
    return time.strftime('%H:%M:%S', time.localtime(time.time()))

def doGet(url):
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
            trace("url: " + url)
            printErrorMsg(str(e) + ": " + url)
            traceback.print_exc()
        count += 1
        if count > 10:
            printErrorMsg("can not connection " + url)
            return False

def trace(msg):
    if isDebug == 1:
        msg = getTime() + " " + msg
#        print msg
        if isLog == 1:
            logFile = open(traceLogPath, 'a')
            logFile.write(msg + "\n")
            logFile.close()

def printErrorMsg(msg):
    if isShowError == 1:
        msg = getTime() + " [Error] " + msg
        print msg
        if isLog == 1:
            if msg.find("HTTP Error 500") != -1:
                return
            if msg.find("urlopen error The read operation timed out") != -1:
                return
            logFile = open(errorLogPath, 'a')
            logFile.write(msg + "\n")
            logFile.close()

def printStepMsg(msg):
    if isShowStep == 1:
        msg = getTime() + " " + msg
        print msg
        if isLog == 1:
            logFile = open(stepLogPath, 'a')
            logFile.write(msg + "\n")
            logFile.close()

def writeLog(msg, filePath, isTime=True):
    if isTime:
        msg = getTime() + " " + msg
    logFile = open(filePath, 'a')
    logFile.write(msg + "\n")
    logFile.close()

def removeDirFiles(dirPath): 
    for fileName in os.listdir(dirPath): 
        targetFile = os.path.join(dirPath, fileName) 
        if os.path.isfile(targetFile): 
            os.remove(targetFile)

# 判断各种目录是否存在
if isLog == 1:
    stepLogDir = os.path.dirname(stepLogPath)
    if not os.path.exists(stepLogDir):
        os.makedirs(stepLogDir)
        printStepMsg("step log file path is not exist, create it: " + stepLogDir)
    errorLogDir = os.path.dirname(errorLogPath)
    if not os.path.exists(errorLogDir):
        os.makedirs(errorLogDir)
        printStepMsg("error log file path is not exist, create it: " + errorLogDir)
    traceLogDir = os.path.dirname(traceLogPath)
    if not os.path.exists(traceLogDir):
        os.makedirs(traceLogDir)
        printStepMsg("trace log file path is not exist, create it: " + traceLogDir)
if isSaveMessageUrl == 1:
    messageUrlLogFileDir = os.path.dirname(messageUrlLogFilePath)
    if not os.path.exists(messageUrlLogFileDir):
        os.makedirs(messageUrlLogFileDir)
        printStepMsg("message URL log file path is not exist, create it: " + messageUrlLogFileDir)
if isSaveImageUrl == 1:
    imageUrlLogFileDir = os.path.dirname(imageUrlLogFilePath)
    if not os.path.exists(imageUrlLogFileDir):
        printStepMsg("image URL log file path is not exist, create it: " + imageUrlLogFileDir)
        os.makedirs(imageUrlLogFileDir)
if isSaveVideoUrl == 1:
    videoFileDir = os.path.dirname(videoFilePath)
    if not os.path.exists(videoFileDir):
        printStepMsg("video URL file path is not exist, create it: " + videoFileDir)
        os.makedirs(videoFileDir)
if isDownloadImage == 1:
    if os.path.exists(imageDownloadPath):
        if os.path.isdir(imageDownloadPath):
            isDelete = False
            while not isDelete:
                input = raw_input(imageDownloadPath + "is exist, do you want to remove it and continue? (Y)es or (N)o: ")
                try:
                    input = input.lower() 
                    if input in ["y", "yes"]:
                        isDelete = True
                    elif input in ["n", "no"]:
                        processExit()
                except:
                    pass            
            printStepMsg("image download path: " + imageDownloadPath + " is exist, remove it")
            shutil.rmtree(imageDownloadPath, True)
            # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
            while os.path.exists(imageDownloadPath):
                time.sleep(5)
        else:
            printStepMsg("image download path: " + imageDownloadPath + " is a file, delete it")
            os.remove(imageDownloadPath)
    printStepMsg("created  image download path: " + imageDownloadPath)
    os.makedirs(imageDownloadPath)

printStepMsg("config init succeed")

# 设置代理
if config.has_key("IS_PROXY"):
    try:
        isProxy = int(config["IS_PROXY"])
    except:
        printMsg("'IS_PROXY' must is a number in config.ini, default value")
        isProxy = 0
else:
    isProxy = 0
if isProxy == 1:
    if config.has_key("PROXY_IP"):
        proxyIp = config["PROXY_IP"]
    else:
        printErrorMsg("Not found proxy IP in config.ini! process stop!")
        processExit()
    if config.has_key("PROXY_PORT"):
        proxyPort = config["PROXY_PORT"]
    else:
        printErrorMsg("Not found proxy port in config.ini! process stop!")
        processExit()
    proxyHandler = urllib2.ProxyHandler({'https':"http://" + proxyIp + ":" + proxyPort})
    opener = urllib2.build_opener(proxyHandler)
    urllib2.install_opener(opener)
    printStepMsg("proxy set succeed")

# 寻找idlist，如果没有结束进程
userIdList = {}
if os.path.exists(memberUIdListFilePath):
    userListFile = open(memberUIdListFilePath, 'r')
    allUserList = userListFile.readlines()
    userListFile.close()
    for userInfo in allUserList:
        userInfo = userInfo.replace(" ", "")
        userInfo = userInfo.replace("\n", "")
        userInfoList = userInfo.split("\t")
        userIdList[userInfoList[0]] = userInfoList
else:
    printErrorMsg("Not exists member id list file: " + memberUIdListFilePath + ", process stop!")
    processExit()
newMemberUIdListFilePath = processPath + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(memberUIdListFilePath)[-1]
newMemberUIdListFile = open(newMemberUIdListFilePath, 'w')
newMemberUIdListFile.close()
# 寻找id.txt，如果没有结束进程
# if version == isNewFunc:
#     userIdList = {}
#     if os.path.exists(memberUIdListFilePath):
#         userListFile = open(memberUIdListFilePath, 'r')
#         allUserList = userListFile.readlines()
#         userListFile.close()
#         for userInfo in allUserList:
#             userInfo = userInfo.replace(" ", "")
#             userInfo = userInfo.replace("\n", "")
#             userInfoList = userInfo.split("\t")
#             userIdList[userInfoList[0]] = userInfoList
#     else:
#         printErrorMsg("Not exists member id list file: " + memberUIdListFilePath + ", process stop!")
#         processExit()
#     newMemberUIdListFilePath = processPath + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(memberUIdListFilePath)[-1]
#     newMemberUIdListFile = open(newMemberUIdListFilePath, 'w')
#     newMemberUIdListFile.close()
# else:    
#     if os.path.exists("id.txt"):
#         userIdFile = open("id.txt", 'r')
#         userIdList = userIdFile.readlines()
#         userIdFile.close()
#         for index in range(len(userIdList)):
#             userIdList[index] = filter(str.isdigit, userIdList[index])
#     else:
#         printErrorMsg("Not exists id.txt, process stop!")
#         processExit()
#     # 根据user Id查找成员名字
#     allUserIdList = {}
#     if os.path.exists(memberUIdListFilePath):
#         userListFile = open(memberUIdListFilePath, 'r')
#         allUserList = userListFile.readlines()
#         userListFile.close()
#         for userInfo in allUserList:
#             userInfo = userInfo.split("\t")
#             allUserIdList[userInfo[0]] = userInfo[1].replace("\n", "")

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
# if version == isNewFunc:
#     newMemberUIdList = copy.deepcopy(userIdList)
#     for newUserId in newMemberUIdList:
#         if len(newMemberUIdList[newUserId]) < 2:
#             newMemberUIdList[newUserId].append(newMemberUIdList[newUserId][0])
#         if len(newMemberUIdList[newUserId]) < 3:
#             newMemberUIdList[newUserId].append("0")
#         if len(newMemberUIdList[newUserId]) < 4:
#             newMemberUIdList[newUserId].append("")
#         else:
#             newMemberUIdList[newUserId][3] = ""
#         if len(newMemberUIdList[newUserId]) < 5:
#             newMemberUIdList[newUserId].append("")

allImageCount = 0
allVideoCount = 0
for userId in userIdList:
    errCount = 0
    isPass = False
    userName = newMemberUIdList[userId][1]
#     if version == isNewFunc:
#         userName = userIdList[userId][1]
#     else:
#         if allUserIdList.has_key(userId):
#             userName = allUserIdList[userId]
#         else:
#             userName = str(userId)
    printStepMsg("UID: " + str(userId) + ", Member: " + userName)
    
    imagePath = imageDownloadPath + "\\" + imageTmpDirName
#     if version == isNewFunc:
#         imagePath = imageDownloadPath + "\\" + imageTmpDirName
#     else:
#         if isSort == 1:
#             imagePath = imageDownloadPath + "\\" + imageTmpDirName
#         else:
#             imagePath = imageDownloadPath + "\\" + userName
    if os.path.exists(imagePath):
        shutil.rmtree(imagePath, True)
    os.makedirs(imagePath)
    
    # 日志文件插入信息
    if isSaveMessageUrl == 1:
        writeLog(userId + " " + userName, messageUrlLogFilePath, isTime=False)
    if isSaveImageUrl == 1:
        writeLog(userId + " " + userName, imageUrlLogFilePath, isTime=False)
    if isSaveVideoUrl == 1:
        writeLog(userId + " " + userName, videoFilePath, isTime=False)

    # 初始化数据
    pageCount = 0
    imageCount = 1
    videoCount = 1
    messageUrlList = []
    imageUrlList = []
    videoIdList = []
    while 1:
        if isPass:
                break
        # 获取信息总页,offset=N表示返回最新的N到N+100条信息所在的url
        photoAlbumUrl = "https://plus.google.com/_/photos/posts/%s?offset=%s" % (userId, pageCount)
        trace("photo Album URL:" + photoAlbumUrl)
        photoAlbumPage = doGet(photoAlbumUrl)
        if not photoAlbumPage:
            printErrorMsg("can not get photoAlbumPage: " + photoAlbumUrl)
            pageCount += 100
            if errCount >= 5:
                printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
#                 if version == isNewFunc:
#                     newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                allImageCount += imageCount - 1
                allVideoCount += videoCount - 1
                isPass = True
                break
            errCount += 1
            continue
         
        # 判断信息总页字节数大小，是否小于300
        if len(photoAlbumPage) < 300:
            printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
            newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
#             if version == isNewFunc:
#                 newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
            allImageCount += imageCount - 1
            allVideoCount += videoCount - 1
            break
            
        messageIndex = 1
        while messageIndex != 0:
            isFindVideo = False
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
                    printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                    newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
                    allImageCount += imageCount - 1
                    allVideoCount += videoCount - 1
                    isPass = True
                    break
#             if version == isNewFunc:
#                 if newMemberUIdList[userId][3] == "":
#                     newMemberUIdList[userId][3] = messageUrl
#                 if len(userIdList[userId]) >= 4 and userIdList[userId][3].find("plus.google.com/photos/" + str(userId) + "/albums/"):
#                     if messageUrl == userIdList[userId][3]:
#                         printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
#                         newMemberUIdList[userId][2] = str(int(newMemberUIdList[userId][2]) + imageCount - 1)
#                         allImageCount += imageCount - 1
#                         allVideoCount += videoCount - 1
#                         isPass = True
#                         break
            trace("message URL:" + messageUrl)
            if not (messageUrl in messageUrlList):
                messageUrlList.append(messageUrl)
                if isSaveMessageUrl == 1:
                    writeLog(messageUrl, messageUrlLogFilePath)
                messagePage = doGet(messageUrl)
                if not messagePage:
                    printErrorMsg("can not get messagePage: " + messageUrl)
                    messageIndex += 1
                    continue
                # video
                if isSaveVideoUrl == 1:
                    videoIdIndex = messagePage.find("redirector.googlevideo.com")
                    while videoIdIndex != -1:
                        videoIdStart = messagePage.find("id\u003d", videoIdIndex)
                        videoIdStop = messagePage.find("\u0026", videoIdStart)
                        videoId = messagePage[videoIdStart + 8:videoIdStop]
                        if not (videoId in videoIdList):
                            videoIdList.append(videoId)
                            writeLog(str(videoCount) + ": " + videoId + " " + messageUrl, videoFilePath, isTime=False)
                            printStepMsg("video " + str(videoCount) + ": " + videoId)
                            videoCount += 1
                            isFindVideo = True
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
#                                     writeLog(str(videoCount) + ": " + videoUrl + "  " + messageUrl + "  " + photoAlbumUrl, videoFilePath, isTime=False)
#                                     printStepMsg("video " + str(videoCount) + ": " + videoUrl)
#                                     videoCount += 1
#                                     isFindVideo = True
#                             videoIndex = messagePage.find("video.googleusercontent.com", videoIndex + 1)
                # picture
                if isDownloadImage == 1:
                    picasawebIndex = messagePage.find("picasaweb.google.com/" + userId)
                    if picasawebIndex != -1:
                        picasawebStart = messagePage.find("http", picasawebIndex - 10)
                        picasawebStop = messagePage.find('"', picasawebStart)
                        picasawebUrl = messagePage[picasawebStart:picasawebStop]
                        trace("picasaweb URL:" + picasawebUrl)
                        picasawebPage = doGet(picasawebUrl)
                        if not picasawebPage:
                            printErrorMsg("can not get picasawebPage: " + picasawebUrl)
                            messageIndex += 1
                            continue
                        imageIndex = picasawebPage.find('"media":')
                        while imageIndex != -1:
                            imageStart = picasawebPage.find("http", imageIndex)
                            imageStop = picasawebPage.find('"', imageStart)
                            imageUrl = picasawebPage[imageStart:imageStop]
                            trace("image URL:" + imageUrl)                       
                            if not (imageUrl in imageUrlList):
                                imageUrlList.append(imageUrl)
                                if isSaveImageUrl == 1:
                                    writeLog(str(imageCount) + ": " + imageUrl + "  " + messageUrl + "  " + photoAlbumUrl, imageUrlLogFilePath, isTime=False)
                                imageResizeIndex = 0
                                for index in range(imageUrl.count("/")):
                                    imageResizeIndex = imageUrl.find("/", imageResizeIndex) + 1
                                imageUrl = imageUrl[:imageResizeIndex] + "s0/" + imageUrl[imageResizeIndex:]
                                fileType = imageUrl.split(".")[-1]
                                imgByte = doGet(imageUrl)
                                if imgByte:
                                    filename = str("%04d" % imageCount)                                
                                    imageFile = open(imagePath + "\\" + str(filename) + "." + fileType, "wb")
                                    printStepMsg("start download " + str(imageCount) + ": " + imageUrl)
                                    imageFile.write(imgByte)
                                    imageFile.close()
                                    printStepMsg("download succeed")
                                    imageCount += 1
                                    if getImageCount > 0 and imageCount > getImageCount:
                                        printStepMsg(userName + " download over, download image count: " + str(imageCount - 1) + ", video count: " + str(videoCount - 1))
                                        allImageCount += imageCount - 1
                                        allVideoCount += videoCount - 1
                                        isPass = True
                                        break
                                else:
                                    printErrorMsg("image path not found: " + imageUrl)
                            imageIndex = picasawebPage.find('"media":', imageIndex + 1)
                    else:
                        printErrorMsg("picasaweb.google.com not found in " + messageUrl)
            messageIndex += 1
        pageCount += 100
        
    if isSaveMessageUrl == 1:
        writeLog("****************************************************************************************************", messageUrlLogFilePath, isTime=False)
    if isSaveImageUrl == 1:
        writeLog("****************************************************************************************************", imageUrlLogFilePath, isTime=False)
    if isSaveVideoUrl == 1:
        writeLog("****************************************************************************************************", videoFilePath, isTime=False)
    
    # 排序
    if isDownloadImage == 1 and isSort == 1:
        imageList = sorted(os.listdir(imagePath), reverse=True)
        # 判断排序目标文件夹是否存在
        if len(imageList) >= 1:
            destPath = imageDownloadPath + "\\" + newMemberUIdList[userId][4] + "\\" + userName
#             if version == isNewFunc:
#                 destPath = imageDownloadPath + "\\" + newMemberUIdList[userId][4] + "\\" + userName
#             else:
#                 destPath = imageDownloadPath + "\\" + userName
            if os.path.exists(destPath):
                if os.path.isdir(destPath):
                    printStepMsg("image download path: " + destPath + " is exist, remove all files in it")
                    removeDirFiles(destPath)
                else:
                    printStepMsg("image download path: " + destPath + " is a file, delete it")
                    os.remove(destPath)
                    os.makedirs(destPath)
            else:
                printStepMsg("create image download path: " + destPath)
                os.makedirs(destPath)

            # 倒叙排列
            if len(userIdList[userId]) >= 3:
                count = int(userIdList[userId][2]) + 1
            else:
                count = 1
#             if version == isNewFunc:
#                 if len(userIdList[userId]) >= 3:
#                     count = int(userIdList[userId][2]) + 1
#                 else:
#                     count = 1
#             else:
#                 count = 1
            for fileName in imageList:
                fileType = fileName.split(".")[1]
                shutil.copyfile(imagePath + "\\" + fileName, destPath + "\\" + str("%04d" % count) + "." + fileType)
                count += 1
            printStepMsg("sorted over, continue next member")
        # 删除临时文件夹
        shutil.rmtree(imagePath, True)

        # 保存最后的信息
        newMemberUIdListFile = open(newMemberUIdListFilePath, 'a')
        newMemberUIdListFile.write("\t".join(newMemberUIdList[userId]) + "\n")
        newMemberUIdListFile.close()        
#         if version == isNewFunc:
#             newMemberUIdListFile = open(newMemberUIdListFilePath, 'a')
#             newMemberUIdListFile.write("\t".join(newMemberUIdList[userId]) + "\n")
#             newMemberUIdListFile.close()

# 保存新的idList.txt
tmpList = []
tmpUserIdList = sorted(newMemberUIdList.keys())
for index in tmpUserIdList:
    tmpList.append("\t".join(newMemberUIdList[index]))
newMemberUIdListString = "\n".join(tmpList)
newMemberUIdListFilePath = processPath + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(memberUIdListFilePath)[-1]
printStepMsg("save new id list file: " + newMemberUIdListFilePath)
newMemberUIdListFile = open(newMemberUIdListFilePath, 'w')
newMemberUIdListFile.write(newMemberUIdListString)
newMemberUIdListFile.close()

# if version == isNewFunc:
# # 保存新的idList.txt
#     tmpList = []
#     tmpUserIdList = sorted(newMemberUIdList.keys())
#     for index in tmpUserIdList:
#         tmpList.append("\t".join(newMemberUIdList[index]))
#     newMemberUIdListString = "\n".join(tmpList)
#     newMemberUIdListFilePath = processPath + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(memberUIdListFilePath)[-1]
#     printStepMsg("save new id list file: " + newMemberUIdListFilePath)
#     newMemberUIdListFile = open(newMemberUIdListFilePath, 'w')
#     newMemberUIdListFile.write(newMemberUIdListString)
#     newMemberUIdListFile.close()

stopTime = time.time()
printStepMsg("all members' image download succeed, use " + str(int(stopTime - startTime)) + " seconds, sum download image count: " + str(allImageCount) + ", video count: " + str(allVideoCount))
