# -*- coding:GBK  -*-
'''
Created on 2013-5-6

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''
import urllib2
import os
import shutil
import sys
import time
import traceback

class shinoda():
    
    def doGet(self, url):
    # http请求
        import sys
        import traceback
        import urllib2
        global IS_SET_TIMEOUT
        if url.find("http") == -1:
            return None
        count = 0
        while 1:
            try:
                request = urllib2.Request(url)
                # 设置头信息
                request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0 FirePHP/0.7.2')
                # 设置访问超时
                if sys.version_info < (2, 7):
                    if not IS_SET_TIMEOUT:
                        urllib2.socket.setdefaulttimeout(20)
                        IS_SET_TIMEOUT = True
                    response = urllib2.urlopen(request)
                else:
                    response = urllib2.urlopen(request, timeout=20)
                return response.read()
            except Exception, e:
                # 代理无法访问
                if str(e).find("[Errno 10061] ") != -1:
                    input = raw_input("无法访问代理服务器，请检查代理设置。是否需要继续程序？(Y)es or (N)o：").lower()
                    if input in ["y", "yes"]:
                        pass
                    elif input in ["n", "no"]:
                        sys.exit()
                # 超时
                elif str(e).find("timed out") != -1:
                    self.printMsg("访问页面超时，重新连接请稍后")
                else:
                    self.printMsg(str(e))
                    traceback.print_exc()
            count += 1
            if count > 10:
                self.printMsg("无法访问页面：" + url)
                return False
    
    def proxy(self, ip, port):
    # 设置代理
        proxyHandler = urllib2.ProxyHandler({'https':"http://" + ip + ":" + port})
        opener = urllib2.build_opener(proxyHandler)
        urllib2.install_opener(opener)
        self.printMsg("设置代理成功")
                
    def getConfig(self, config, key, defaultValue, mode, prefix=None, postfix=None):
    # 获取配置文件
    # config : 字典格式，如：{key1:value1, key2:value2}
    # mode 0 : 直接赋值
    # mode 1 : 字符串拼接
    # mode 2 : 取整
    # mode 3 : 文件路径，以'\'开头的为当前目录下创建
    # prefix: 前缀，只有在mode=1时有效
    # postfix: 后缀，只有在mode=1时有效
        value = None
        if config.has_key(key):
            if mode == 0:
                value = config[key]
            elif mode == 1:
                value = config[key]
                if prefix != None:
                    value = prefix + value
                if postfix != None:
                    value = value + postfix
            elif mode == 2:
                try:
                    value = int(config[key])
                except:
                    self.printMsg("配置文件config.ini中key为'" + key + "'的值必须是一个整数，使用程序默认设置")
                    traceback.print_exc()
                    value = defaultValue
            elif mode == 3:
                value = config[key]
                if value[0] == "\\":
                    value = os.getcwd() + value
                return value
        else:
            self.printMsg("配置文件config.ini中没有找到key为'" + key + "'的参数，使用程序默认设置")
            value = defaultValue
        return value
    
    def getTime(self):
        return time.strftime('%m-%d %H:%M:%S', time.localtime(time.time()))
    
    def writeFile(self, msg, filePath):
        logFile = open(filePath, 'a')
        logFile.write(msg + "\n")
        logFile.close()
        
    def createDir(self, path):
        count = 0
        while 1:
            try:
                if count >= 5:
                    return False
                os.makedirs(path)
                if os.path.isdir(path):
                    return True
            except Exception, e:
                self.printMsg(str(e))
                time.sleep(5)
                traceback.print_exc()
            count +=1
            
    def removeDirFiles(self, dirPath): 
        for fileName in os.listdir(dirPath): 
            targetFile = os.path.join(dirPath, fileName) 
            if os.path.isfile(targetFile): 
                os.remove(targetFile)
                
    def processExit(self):
        sys.exit()
        
    def trace(self, msg):
        if self.isDebug == 1:
            msg = self.getTime() + " " + msg
    #        self.printMsg(msg, False)
            if self.isLog == 1:
                self.writeFile(msg, self.traceLogPath)
    
    def printMsg(self, msg, isTime=True):
        if isTime:
            msg = self.getTime() + " " + msg
        print msg
        
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
            imageFile = open(imagePath + "\\" + str("%05d" % imageCount) + "." + fileType, "wb")
            self.printMsg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
            imageFile.write(imgByte)
            imageFile.close()
            self.printMsg("下载成功")
        else:
            self.printErrorMsg("获取图片信息失败：" + imageUrl)
                           
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
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
        self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.getConfig(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        # 配置文件获取程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImagePageCount = self.getConfig(config, "GET_IMAGE_PAGE_COUNT", 1, 2)
        self.isProxy = self.getConfig(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        self.printMsg("配置文件读取完成")
    
    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not os.path.exists(stepLogDir):
                if not self.createDir(stepLogDir):
                    self.printErrorMsg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                    self.processExit()
                self.printStepMsg("步骤日志目录不存在，创建文件夹：" + stepLogDir)
            errorLogDir = os.path.dirname(self.errorLogPath)
            if not os.path.exists(errorLogDir):
                if not self.createDir(errorLogDir):
                    self.printErrorMsg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
                    self.processExit()
                self.printStepMsg("错误日志目录不存在，创建文件夹：" + errorLogDir)
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not os.path.exists(traceLogDir):
                if not self.createDir(traceLogDir):
                    self.printErrorMsg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                    self.processExit()
                self.printStepMsg("调试日志目录不存在，创建文件夹：" + traceLogDir)
        # 图片排序后的保存目录
        if os.path.exists(self.imageDownloadPath):
            if os.path.isdir(self.imageDownloadPath):
                isDelete = False
                while not isDelete:
                    # 手动输入是否删除旧文件夹中的目录
                    input = raw_input("图片保存目录：" + self.imageDownloadPath + " 已经存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except:
                        pass
                self.printStepMsg("删除图片保存目录：" + self.imageDownloadPath)
                # 删除目录
                shutil.rmtree(self.imageDownloadPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageDownloadPath):
                    time.sleep(5)
            else:
                self.printStepMsg("图片保存目录：" + self.imageDownloadPath + "已存在相同名字的文件，自动删除")
                os.remove(self.imageDownloadPath)
        self.printStepMsg("创建图片保存目录：" + self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.printErrorMsg("创建图片保存目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.processExit()
        # 图片下载临时目录
        if os.path.exists(self.imageTempPath):
            if os.path.isdir(self.imageTempPath):
                isDelete = False
                while not isDelete:
                    # 手动输入是否删除旧文件夹中的目录
                    input = raw_input("图片下载临时目录：" + self.imageTempPath + " 已经存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except:
                        pass
                self.printStepMsg("删除图片下载临时目录：" + self.imageTempPath)
                shutil.rmtree(self.imageTempPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageTempPath):
                    time.sleep(5)
            else:
                self.printStepMsg("图片下载临时目录：" + self.imageTempPath + "已存在相同名字的文件，自动删除")
                os.remove(self.imageTempPath)
        self.printStepMsg("创建图片下载临时目录：" + self.imageTempPath)
        if not self.createDir(self.imageTempPath):
            self.printErrorMsg("创建图片下载临时目录：" + self.imageTempPath + " 失败，程序结束！")
            self.processExit()
        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.proxy(self.proxyIp, self.proxyPort)
        # 读取存档文件
        saveFilePath = os.getcwd() + "\\" + ".".join(sys.argv[0].split("\\")[-1].split(".")[:-1]) + ".save"
        lastImageUrl = ""
        imageStartIndex = 0
        if os.path.exists(saveFilePath):
            saveFile = open(saveFilePath, 'r')
            saveInfo = saveFile.read()
            saveFile.close()
            saveList = saveInfo.split("\t")
            if len(saveList) >= 2:
                imageStartIndex = saveList[0]
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
            self.trace("博客页面地址:" + indexUrl)
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
                    self.trace("图片地址:" + imageUrl)
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
                    imgTagStart = indexPage.find('<img ', imgTagStart)
                    if imgTagStart == -1:
                        break
                    imgTagStop = indexPage.find('/>', imgTagStart)
                    imageIndex = indexPage.find('src="http://blog.mariko-shinoda.net', imgTagStart, imgTagStop)
                    if imageIndex == -1:
                        imgTagStart += 1  
                        continue
                    imageStart = indexPage.find("http", imageIndex)
                    imageStop = indexPage.find('"', imageStart)
                    imageUrl = indexPage[imageStart:imageStop]
                    self.trace("图片地址:" + imageUrl)
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
        
        self.printStepMsg("下载完毕")
        
        # 排序复制到保存目录
        if self.isSort == 1:
            allImageCount = 0
            for fileName in sorted(os.listdir(self.imageTempPath), reverse=True):
                imageStartIndex += 1
                imagePath = self.imageTempPath + "\\" + fileName
                fileType = fileName.split(".")[-1]
                shutil.copyfile(imagePath, self.imageDownloadPath + "\\" + str("%05d" % imageStartIndex) + "." + fileType)
                allImageCount += 1
            self.printStepMsg("图片从下载目录移动到保存目录成功")
            # 删除下载临时目录中的图片
            shutil.rmtree(self.imageTempPath, True)
            
        # 保存新的存档文件
        newSaveFilePath = os.getcwd() + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(saveFilePath)[-1]
        self.printStepMsg("保存新y存档文件: " + newSaveFilePath)
        newSaveFile = open(newSaveFilePath, 'w')
        newSaveFile.write(str(imageStartIndex) + "\t" + newLastImageUrl)
        newSaveFile.close()
            
        stopTime = time.time()
        self.printStepMsg("成功下载最新图片，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(imageCount - 1) + "张")

if __name__ == '__main__':
    shinoda().main()
