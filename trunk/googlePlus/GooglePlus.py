# -*- coding:UTF-8  -*-
'''
Created on 2013-4-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''
from common import common

import copy
import os
import shutil
import time

class GooglePlus(common.Tool):

    def trace(self, msg):
        super(GooglePlus, self).trace(msg, self.isShowError, self.traceLogPath)

    def printErrorMsg(self, msg):
        super(GooglePlus, self).printErrorMsg(msg, self.isShowError, self.errorLogPath)

    def printStepMsg(self, msg):
        super(GooglePlus, self).printStepMsg(msg, self.isShowError, self.stepLogPath)

    def __init__(self):
        config = self.analyzeConfig( os.getcwd() + "\\..\\common\\config.ini")
        # 程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImageCount = self.getConfig(config, "GET_IMAGE_COUNT", 0, 2)
        self.getImageUrlCount = self.getConfig(config, "GET_IMAGE_URL_COUNT", 100, 2)
        # 代理
        self.isProxy = self.getConfig(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ""
            self.stepLogPath = ""
        else:
            self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.getConfig(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.userIdListFilePath = self.getConfig(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
        self.printMsg("配置文件读取完成")

    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.makeDir(stepLogDir, 0):
                self.printErrorMsg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                self.processExit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.makeDir(traceLogDir, 0):
                self.printErrorMsg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                self.processExit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.makeDir(errorLogDir, 0):
            self.printErrorMsg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
            self.processExit()

        # 图片保存目录
        self.printStepMsg("创建图片根目录：" + self.imageDownloadPath)
        if not self.makeDir(self.imageDownloadPath, 2):
            self.printErrorMsg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.processExit()

        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.proxy(self.proxyIp, self.proxyPort, "https")

        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.userIdListFilePath):
            userListFile = open(self.userIdListFilePath, "r")
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                if len(userInfo) < 10:
                    continue
                userInfo = userInfo.replace("\xef\xbb\xbf", "")
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.printErrorMsg("用户ID存档文件: " + self.userIdListFilePath + "不存在，程序结束！")
            self.processExit()
        # 创建临时存档文件
        newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        newUserIdListFile = open(newUserIdListFilePath, "w")
        newUserIdListFile.close()
        # 复制处理存档文件
        newUserIdList = copy.deepcopy(userIdList)
        for newUserId in newUserIdList:
            # 如果没有名字，则名字用uid代替
            if len(newUserIdList[newUserId]) < 2:
                newUserIdList[newUserId].append(newUserIdList[newUserId][0])
            # 如果没有初始image count，则为0
            if len(newUserIdList[newUserId]) < 3:
                newUserIdList[newUserId].append("0")
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(newUserIdList[newUserId]) < 4:
                newUserIdList[newUserId].append("")
            else:
                newUserIdList[newUserId][3] = ""
            # video count
            if len(newUserIdList[newUserId]) < 5:
                newUserIdList[newUserId].append("0")
            # video token
            if len(newUserIdList[newUserId]) < 6:
                newUserIdList[newUserId].append("")
            # 处理成员队伍信息
            if len(newUserIdList[newUserId]) < 7:
                newUserIdList[newUserId].append("")

        totalImageCount = 0
        # 循环下载每个id
        for userId in sorted(userIdList.keys()):
            userName = newUserIdList[userId][1]
            self.printStepMsg("ID: " + str(userId) + ", 名字: " + userName)
            # 初始化数据
            imageCount = 1
            messageUrlList = []
            imageUrlList = []
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(userIdList[userId]) > 3 and userIdList[userId][3].find("picasaweb.google.com/") != -1 and int(userIdList[userId][2]) != 0:
                isError = True
            else:
                isError = False

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userName
            if not self.makeDir(imagePath, 1):
                self.printErrorMsg("创建图片下载目录： " + imagePath + " 失败，程序结束！")
                self.processExit()

            # 图片下载
#            photoAlbumUrl = "https://plus.google.com/photos/%s/albums/posts?banner=pwa" % (userId)
            photoAlbumUrl = 'https://plus.google.com/_/photos/pc/read/'
            now = time.time() * 100
            key = ''
            postData = 'f.req=[["posts",null,null,"synthetic:posts:%s",3,"%s",null],[%s,1,null],"%s",null,null,null,null,null,null,null,2]&at=AObGSAj1ll9iGT-1d05vTuxV5yygWelh9g:%s&' % (userId, userId, self.getImageUrlCount, key, now)
            self.trace("信息首页地址：" + photoAlbumUrl)
            photoAlbumPage = self.doGet(photoAlbumUrl, postData)
            if photoAlbumPage:
                messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId)
                isOver = False
                while messageIndex != -1:
                    messageStart = photoAlbumPage.find("http", messageIndex)
                    messageStop = photoAlbumPage.find('"', messageStart)
                    messageUrl = photoAlbumPage[messageStart:messageStop]
                    # 将第一张image的URL保存到新id list中
                    if newUserIdList[userId][3] == "":
                        newUserIdList[userId][3] = messageUrl
                    # 检查是否已下载到前一次的图片
                    if len(userIdList[userId]) >= 4 and userIdList[userId][3].find("picasaweb.google.com/") != -1:
                        if messageUrl == userIdList[userId][3]:
                            isError = False
                            break
                    self.trace("message URL:" + messageUrl)
                    # 判断是否重复
                    if messageUrl in messageUrlList:
                        messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex + 1)
                        continue
                    messageUrlList.append(messageUrl)
                    messagePage = self.doGet(messageUrl)
                    if not messagePage:
                        self.printErrorMsg("无法获取信息页: " + messageUrl)
                        messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex + 1)
                        continue
                    flag = messagePage.find("<div><a href=")
                    while flag != -1:
                        imageIndex = messagePage.find("<img src=", flag, flag + 200)
                        if imageIndex == -1:
                            self.printErrorMsg("信息页：" + messageUrl + " 中没有找到标签'<img src='")
                            break
                        imageStart = messagePage.find("http", imageIndex)
                        imageStop = messagePage.find('"', imageStart)
                        imageUrl = messagePage[imageStart:imageStop]
                        self.trace("image URL:" + imageUrl)
                        if imageUrl in imageUrlList:
                            flag = messagePage.find("<div><a href=", flag + 1)
                            continue
                        imageUrlList.append(imageUrl)
                        # 重组URL并使用最大分辨率
                        # https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/Ic42/s128/16%252520-%2525201.jpg
                        # ->
                        # https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/s0-Ic42/16%252520-%2525201.jpg
                        tempList = imageUrl.split("/")
                        tempList[-2] = "s0"
                        imageUrl = "/".join(tempList[:-3]) + '/s0-' + tempList[-3] + '/' + tempList[-1]
                        self.printStepMsg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                        imgByte = self.doGet(imageUrl)
                        if imgByte:
                            # 文件类型
                            if imageUrl.rfind('/') < imageUrl.rfind('.'):
                                fileType = imageUrl.split(".")[-1]
                            else:
                                fileType = 'jpg'
                            # 保存图片
                            imageFile = open(imagePath + "\\" + str("%04d" % imageCount) + "." + fileType, "wb")
                            imageFile.write(imgByte)
                            self.printStepMsg("下载成功")
                            imageFile.close()
                            imageCount += 1
                        else:
                            self.printErrorMsg("获取第" + str(imageCount) + "张图片信息失败：" + str(userId) + ": " + imageUrl)
                        # 达到配置文件中的下载数量，结束
                        if len(userIdList[userId]) >= 4 and userIdList[userId][3] != '' and self.getImageCount > 0 and imageCount > self.getImageCount:
                            isOver = True
                            break
                        flag = messagePage.find("<div><a href=", flag + 1)
                    if isOver:
                        break
                    messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex + 1)
            else:
                self.printErrorMsg("无法获取相册首页: " + photoAlbumUrl + ' ' + userName)

            self.printStepMsg(userName + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userId][2] = str(int(newUserIdList[userId][2]) + imageCount - 1)
            totalImageCount += imageCount - 1

            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + newUserIdList[userId][6] + "\\" + userName
                    if not self.makeDir(destPath, 1):
                        self.printErrorMsg("创建图片子目录： " + destPath + " 失败，程序结束！")
                        self.processExit()

                    # 倒叙排列
                    if len(userIdList[userId]) >= 3:
                        count = int(userIdList[userId][2]) + 1
                    else:
                        count = 1
                    for fileName in imageList:
                        fileType = fileName.split(".")[1]
                        self.copyFiles(imagePath + "\\" + fileName, destPath + "\\" + str("%04d" % count) + "." + fileType)
                        count += 1
                    self.printStepMsg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self.printErrorMsg(userName + "图片数量异常，请手动检查")

            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, "a")
            newUserIdListFile.write("\t".join(newUserIdList[userId]) + "\n")
            newUserIdListFile.close()

        stopTime = time.time()
        self.printStepMsg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(totalImageCount) + "张")

if __name__ == "__main__":
    GooglePlus().main()
