# -*- coding:utf-8  -*-
'''
Created on 2013-5-6

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common
import os
import shutil
import sys
import time

class shinoda(common.Tool):

    def trace(self, msg):
        super(shinoda, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def printErrorMsg(self, msg):
        super(shinoda, self).printErrorMsg(msg, self.isShowError, self.errorLogPath)
        
    def printStepMsg(self, msg):
        super(shinoda, self).printStepMsg(msg, self.isShowError, self.stepLogPath)

    def download(self, imageUrl, imagePath, imageCount):
        imgByte = self.doGet(imageUrl)
        if imgByte:
            fileType = imageUrl.split(".")[-1]
            imageFile = open(imagePath + "\\" + str("%05d" % imageCount) + "." + fileType, "wb")
            self.printMsg(u"开始下载第" + str(imageCount) + u"张图片：" + imageUrl)
            imageFile.write(imgByte)
            imageFile.close()
            self.printMsg(u"下载成功")
        else:
            self.printErrorMsg(u"获取图片信息失败：" + imageUrl)
                           
    def __init__(self):
        processPath = os.getcwd()
        configFile = open(processPath + "\\..\\common\\config.ini", "r")
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
        # 程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImagePageCount = self.getConfig(config, "GET_IMAGE_PAGE_COUNT", 1, 2)
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
        self.printMsg(u"配置文件读取完成")
    
    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.createDir(stepLogDir):
                self.printErrorMsg(u"创建步骤日志目录：" + stepLogDir + u" 失败，程序结束！")
                self.processExit()
            self.printStepMsg(u"步骤日志目录不存在，创建文件夹: " + stepLogDir)
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.createDir(traceLogDir):
                self.printErrorMsg(u"创建调试日志目录：" + traceLogDir + u" 失败，程序结束！")
                self.processExit()
            self.printStepMsg(u"调试日志目录不存在，创建文件夹: " + traceLogDir)
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.createDir(errorLogDir):
            self.printErrorMsg(u"创建错误日志目录：" + errorLogDir + u" 失败，程序结束！")
            self.processExit()
        self.printStepMsg(u"错误日志目录不存在，创建文件夹：" + errorLogDir)
        # 图片排序后的保存目录
        if os.path.exists(self.imageDownloadPath):
            if os.path.isdir(self.imageDownloadPath):
                isDelete = False
                while not isDelete:
                    # 手动输入是否删除旧文件夹中的目录
                    input = raw_input(self.getTime() + u" 图片保存目录：" + self.imageDownloadPath + u" 已经存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except:
                        pass
                self.printStepMsg(u"删除图片保存目录：" + self.imageDownloadPath)
                # 删除目录
                shutil.rmtree(self.imageDownloadPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageDownloadPath):
                    shutil.rmtree(self.imageDownloadPath, True)
                    time.sleep(5)
            else:
                self.printStepMsg(u"图片保存目录：" + self.imageDownloadPath + u"已存在相同名字的文件，自动删除")
                os.remove(self.imageDownloadPath)
        self.printStepMsg(u"创建图片保存目录：" + self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.printErrorMsg(u"创建图片保存目录：" + self.imageDownloadPath + u" 失败，程序结束！")
            self.processExit()
        # 图片下载临时目录
        if os.path.exists(self.imageTempPath):
            if os.path.isdir(self.imageTempPath):
                isDelete = False
                while not isDelete:
                    # 手动输入是否删除旧文件夹中的目录
                    input = raw_input(self.getTime() + u" 图片下载临时目录：" + self.imageTempPath + u" 已经存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except:
                        pass
                self.printStepMsg(u"删除图片下载临时目录：" + self.imageTempPath)
                shutil.rmtree(self.imageTempPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageTempPath):
                    shutil.rmtree(self.imageTempPath, True)
                    time.sleep(5)
            else:
                self.printStepMsg(u"图片下载临时目录：" + self.imageTempPath + u"已存在相同名字的文件，自动删除")
                os.remove(self.imageTempPath)
        self.printStepMsg(u"创建图片下载临时目录：" + self.imageTempPath)
        if not self.createDir(self.imageTempPath):
            self.printErrorMsg(u"创建图片下载临时目录：" + self.imageTempPath + u" 失败，程序结束！")
            self.processExit()
        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.proxy(self.proxyIp, self.proxyPort, "http")
        # 读取存档文件
        saveFilePath = os.getcwd() + "\\" + ".".join(sys.argv[0].split("\\")[-1].split(".")[:-1]) + ".save"
        lastImageUrl = ""
        imageStartIndex = 0
        if os.path.exists(saveFilePath):
            saveFile = open(saveFilePath, "r")
            saveInfo = saveFile.read()
            saveFile.close()
            saveList = saveInfo.split("\t")
            if len(saveList) >= 2:
                imageStartIndex = int(saveList[0])
                lastImageUrl = saveList[1]
        # 下载
        url = "http://blog.mariko-shinoda.net/index%s.html"
        pageIndex = 1
        imageCount = 1
        isOver = False
        newLastImageUrl = ""
        while True:
            if isOver:
                break
            # 达到配置文件中的下载数量，结束
            if self.getImagePageCount != 0 and pageIndex > self.getImagePageCount:
                break
            if pageIndex > 1:
                indexUrl = url % ("_" + str(pageIndex))
                indexPage = self.doGet(indexUrl)
            else:
                indexUrl = url % ("")
                indexPage = self.doGet(indexUrl)
            self.trace(u"博客页面地址：" + indexUrl)
            if indexPage:
                # old image:
                imageIndex = 0
                while True:
                    imageIndex = indexPage.find('<a href="http://mariko-shinoda.up.seesaa.net', imageIndex)
                    if imageIndex == -1:
                        break
                    imageStart = indexPage.find("http", imageIndex) 
                    imageStop = indexPage.find('"', imageStart)
                    imageUrl = indexPage[imageStart:imageStop]
                    self.trace(u"图片地址：" + imageUrl)
                    if imageUrl.find("data") == -1:
                        if newLastImageUrl == "":
                            newLastImageUrl = imageUrl
                        # 检查是否已下载到前一次的图片
                        if lastImageUrl == imageUrl:
                            isOver = True
                            break
                        # 下载图片
                        self.download(imageUrl, self.imageTempPath, imageCount)
                        imageCount += 1
                    imageIndex += 1
                if isOver:
                    break
                # new image:
                imgTagStart = 0
                while True:
                    imgTagStart = indexPage.find("<img ", imgTagStart)
                    if imgTagStart == -1:
                        break
                    imgTagStop = indexPage.find("/>", imgTagStart)
                    imageIndex = indexPage.find('src="http://blog.mariko-shinoda.net', imgTagStart, imgTagStop)
                    if imageIndex == -1:
                        imgTagStart += 1  
                        continue
                    imageStart = indexPage.find("http", imageIndex)
                    imageStop = indexPage.find('"', imageStart)
                    imageUrl = indexPage[imageStart:imageStop]
                    self.trace(u"图片地址：" + imageUrl)
                    if imageUrl.find("data") == -1:
                        if newLastImageUrl == "":
                            newLastImageUrl = imageUrl
                        # 检查是否已下载到前一次的图片
                        if lastImageUrl == imageUrl:
                            isOver = True
                            break
                        # 下载图片
                        self.download(imageUrl, self.imageTempPath, imageCount)
                        imageCount += 1
                    imgTagStart += 1
                if isOver:
                    break
            else:
                break
            pageIndex += 1
        
        self.printStepMsg(u"下载完毕")
        
        # 排序复制到保存目录
        if self.isSort == 1:
            allImageCount = 0
            for fileName in sorted(os.listdir(self.imageTempPath), reverse=True):
                imageStartIndex += 1
                imagePath = self.imageTempPath + "\\" + fileName
                fileType = fileName.split(".")[-1]
                shutil.copyfile(imagePath, self.imageDownloadPath + "\\" + str("%05d" % imageStartIndex) + "." + fileType)
                allImageCount += 1
            self.printStepMsg(u"图片从下载目录移动到保存目录成功")
            # 删除下载临时目录中的图片
            shutil.rmtree(self.imageTempPath, True)
            
        # 保存新的存档文件
        newSaveFilePath = os.getcwd() + "\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(saveFilePath)[-1]
        self.printStepMsg(u"保存新存档文件: " + newSaveFilePath)
        newSaveFile = open(newSaveFilePath, "w")
        newSaveFile.write(str(imageStartIndex) + "\t" + newLastImageUrl)
        newSaveFile.close()
            
        stopTime = time.time()
        self.printStepMsg(u"成功下载最新图片，耗时" + str(int(stopTime - startTime)) + u"秒，共计图片" + str(imageCount - 1) + u"张")

if __name__ == "__main__":
    shinoda().main()
