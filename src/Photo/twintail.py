# -*- coding:utf-8  -*-
'''
Created on 2013-12-15

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common
import os
import shutil
import time

class weibo(common.Tool):

    def trace(self, msg):
        super(weibo, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def printErrorMsg(self, msg):
        super(weibo, self).printErrorMsg(msg, self.isShowError, self.errorLogPath)
        
    def printStepMsg(self, msg):
        super(weibo, self).printStepMsg(msg, self.isShowError, self.stepLogPath)

    def printMsg(self, msg, isTime=True):
        if isTime:
            msg = self.getTime() + " " + msg
        print msg
        
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
        # 代理
        self.isProxy = self.getConfig(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
        self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.printMsg("配置文件读取完成")
            
    def main(self):
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
        if os.path.exists(self.imageDownloadPath):
            if os.path.isdir(self.imageDownloadPath):
                isDelete = False
                while not isDelete:
                    # 手动输入是否删除旧文件夹中的目录
                    input = raw_input(self.getTime() + u" 图片保存目录：" + self.imageDownloadPath + u" 已经存在，是否需要删除该文件夹并继续程序？(Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except Exception, e:
                        self.printErrorMsg(str(e))
                        pass
                self.printStepMsg(u"删除图片保存目录: " + self.imageDownloadPath)
                # 删除目录
                shutil.rmtree(self.imageDownloadPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageDownloadPath):
                    time.sleep(5)
            else:
                self.printStepMsg(u"图片保存目录: " + self.imageDownloadPath + u"已存在相同名字的文件，自动删除")
                os.remove(self.imageDownloadPath)
        self.printStepMsg(u"创建图片保存目录: " + self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.printErrorMsg(u"创建图片保存目录：" + self.imageDownloadPath + u" 失败，程序结束！")
            self.processExit()
        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.proxy(self.proxyIp, self.proxyPort, "http")
        
        url = "http://twintail-japan.com/campus/contents/%s.html"
        imageUrl = "http://twintail-japan.com/campus/contents/%s"
        allImageCount = 0
        for pageNumber in range(1, 60):
            page = self.doGet(url % pageNumber)
            nameStart = page.find("名前 /")
            nameStop = page.find("(", nameStart)
            name = page[nameStart + 11:nameStop].replace(" ", "").replace("\n", "")
            self.trace(u"页面地址:" + url % pageNumber)
            self.printMsg(u"名字：" + name)
            imagePath = self.imageDownloadPath + "\\" + ("%02d" % pageNumber) + " " + name.decode("utf-8")
            if os.path.exists(imagePath):
                shutil.rmtree(imagePath, True)
            if not self.createDir(imagePath):
                self.printErrorMsg(u"创建图片下载目录：" + imagePath + u" 失败，程序结束！")
                self.processExit()
            imageCount = 1
            if page == False:
                break
            imageStart = page.find("<span>")
            while imageStart != -1:
                imageStop = page.find("</span>", imageStart)
                imageUrlPath = page[imageStart + 6:imageStop]
                imgByte = self.doGet(imageUrl % imageUrlPath)
                if imgByte:
                    fileType = (imageUrl % imageUrlPath).split(".")[-1]
                    imageFile = open(imagePath + "\\" + str("%02d" % imageCount) + "." + fileType, "wb")
                    self.printMsg(u"开始下载第" + str(imageCount) + u"张图片：" + imageUrl % imageUrlPath)
                    imageFile.write(imgByte)
                    imageFile.close()
                    self.printMsg(u"下载成功")
                    imageCount += 1
                imageStart = page.find("<span>", imageStart + 1)
            allImageCount += imageCount

if __name__ == "__main__":
    weibo().main()
