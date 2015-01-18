# -*- coding:GBK  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

import copy
import md5
import os
import random
import shutil
import time

from common import common, json


class weibo(common.Tool):
    
    def trace(self, msg):
        super(weibo, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def printErrorMsg(self, msg):
        super(weibo, self).printErrorMsg(msg, self.isShowError, self.errorLogPath)
        
    def printStepMsg(self, msg):
        super(weibo, self).printStepMsg(msg, self.isShowError, self.stepLogPath)
        
    def visit(self, url):
        tempPage = self.doGet(url)
        if tempPage:
            redirectUrlIndex = tempPage.find("location.replace")           
            if redirectUrlIndex != -1:
                redirectUrlStart = tempPage.find("'", redirectUrlIndex) + 1
                redirectUrlStop = tempPage.find("'", redirectUrlStart)
#                 redirectUrlStart = tempPage.find('"', redirectUrlIndex) + 1
#                 redirectUrlStop = tempPage.find('"', redirectUrlStart)
                redirectUrl = tempPage[redirectUrlStart:redirectUrlStop]
                return str(self.doGet(redirectUrl))
            elif tempPage.find("用户名或密码错误") != -1:
                self.printErrorMsg("登陆状态异常，请在浏览器中重新登陆微博账号")
                self.processExit()
            else:
                try:
                    tempPage = tempPage.decode("utf-8")
                    if tempPage.find("用户名或密码错误") != -1:
                        self.printErrorMsg("登陆状态异常，请在浏览器中重新登陆微博账号")
                        self.processExit()
                except Exception, e:
                    pass
                return str(tempPage)
        return False

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
        # 每次请求获取的图片数量
        self.IMAGE_COUNT_PER_PAGE = 20
        # 程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImageCount = self.getConfig(config, "GET_IMAGE_COUNT", 0, 2)
        # 代理设置
        self.isProxy = self.getConfig(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.getConfig(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ''
            self.stepLogPath = ''
        else:
            self.traceLogPath = self.getConfig(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.getConfig(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = os.getcwd() +  "\\photo2"
        self.imageTempPath = os.getcwd() +  "\\photo2\\tempImage"
        self.userIdListFilePath = os.getcwd() + "\\info\\idlist_2.txt"
        # 操作系统&浏览器
        self.browerVersion = self.getConfig(config, "BROWSER_VERSION", 2, 2)
        self.osVersion = self.getConfig(config, "OS_VERSION", 1, 2)
        # cookie
        self.isAutoGetCookie = self.getConfig(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if self.isAutoGetCookie == 0:
            self.cookiePath = self.getConfig(config, "COOKIE_PATH", "", 0)
        else:
            self.cookiePath = self.getDefaultBrowserCookiePath(self.osVersion, self.browerVersion)
        self.printMsg("配置文件读取完成")
            
    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not os.path.exists(stepLogDir):
                self.printStepMsg("步骤日志目录不存在，创建文件夹：" + stepLogDir)
                if not self.createDir(stepLogDir):
                    self.printErrorMsg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                    self.processExit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not os.path.exists(traceLogDir):
                self.printStepMsg("调试日志目录不存在，创建文件夹：" + traceLogDir)
                if not self.createDir(traceLogDir):
                    self.printErrorMsg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                    self.processExit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not os.path.exists(errorLogDir):
            self.printStepMsg("错误日志目录不存在，创建文件夹：" + errorLogDir)
            if not self.createDir(errorLogDir):
                self.printErrorMsg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
                self.processExit()
        # 图片下载目录
        if os.path.exists(self.imageDownloadPath):
            # 路径是目录
            if os.path.isdir(self.imageDownloadPath):
                # 目录不为空
                if os.listdir(self.imageDownloadPath):
                    isDelete = False
                    while not isDelete:
                        input = raw_input(self.getTime() + " 图片保存目录：" + self.imageDownloadPath + " 已存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                        try:
                            input = input.lower()
                            if input in ["y", "yes"]:
                                isDelete = True
                            elif input in ["n", "no"]:
                                self.processExit()
                        except Exception, e:
                            self.printErrorMsg(str(e))
                            pass
                    self.printStepMsg("删除图片保存目录：" + self.imageDownloadPath)
                    shutil.rmtree(self.imageDownloadPath, True)
                    # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                    while os.path.exists(self.imageDownloadPath):
                        shutil.rmtree(self.imageDownloadPath, True)
                        time.sleep(5)
            else:
                self.printStepMsg("图片保存目录：" + self.imageDownloadPath + "已存在相同名字的文件，自动删除")
                os.remove(self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.printErrorMsg("创建图片下载目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.processExit()
        self.printStepMsg("创建图片保存目录：" + self.imageDownloadPath)
        # 设置代理
        if self.isProxy == 1:
            self.proxy(self.proxyIp, self.proxyPort, "http")
        # 设置系统cookies (fire fox)
        if not self.cookie(self.cookiePath, self.browerVersion):
            self.printErrorMsg("导入浏览器cookies失败，程序结束！")
            self.processExit()
        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.userIdListFilePath):
            userListFile = open(self.userIdListFilePath, 'r')
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfo = userInfo.replace("\r", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.printErrorMsg("用户ID存档文件：" + self.userIdListFilePath + "不存在，程序结束！")
            self.processExit()
        newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        newUserIdListFile = open(newUserIdListFilePath, 'w')
        newUserIdListFile.close()

        newUserIdList = copy.deepcopy(userIdList)
        for newUserId in newUserIdList:
            # 如果没有名字，则名字用uid代替
            if len(newUserIdList[newUserId]) < 2:
                newUserIdList[newUserId].append(newUserIdList[newUserId][0])
            # 如果没有初试image count，则为0
            if len(newUserIdList[newUserId]) < 3:
                newUserIdList[newUserId].append("0")
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(newUserIdList[newUserId]) < 4:
                newUserIdList[newUserId].append("")
            else:
                newUserIdList[newUserId][3] = ""
            # 处理成员队伍信息
            if len(newUserIdList[newUserId]) < 5:
                newUserIdList[newUserId].append("")
        allImageCount = 0
        for userId in sorted(userIdList.keys()):
            userName = newUserIdList[userId][1]
            self.printStepMsg("UID: " + str(userId) + "，Name: " + userName)
            # 初始化数据
            pageCount = 1
            imageCount = 1
            totalImageCount = 0
            isPass = False
            if len(userIdList[userId]) < 3 or userIdList[userId][3] == '':
                isError = False
            else:
                isError = True
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录\
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userName
            if os.path.exists(imagePath):
                shutil.rmtree(imagePath, True)
            if not self.createDir(imagePath):
                self.printErrorMsg("创建图片下载目录：" + imagePath + " 失败，程序结束！")
                self.processExit()
            # 日志文件插入信息
            while 1:
                photoAlbumUrl = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (userId, self.IMAGE_COUNT_PER_PAGE, pageCount)
                self.trace("相册专辑地址：" + photoAlbumUrl)
                photoPageData = self.visit(photoAlbumUrl)
                self.trace("返回JSON数据：" + photoPageData)
                try:
                    page = json.read(photoPageData)
                except:
                    self.printErrorMsg("返回信息：" + str(photoPageData) + " 不是一个JSON数据, user id: " + str(userId))
                    break
                if not isinstance(page, dict):
                    self.printErrorMsg("JSON数据：" + str(page) + " 不是一个字典, user id: " + str(userId))
                    break
                if not page.has_key("data"):
                    self.printErrorMsg("在JSON数据：" + str(page) + " 中没有找到'data'字段, user id: " + str(userId))
                    break
                if totalImageCount == 0:
                    if page["data"].has_key("total"):
                        totalImageCount = page["data"]["total"]
                    else:
                        self.printErrorMsg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(userId))
                        isPass = True
                        break
                if not isinstance(page["data"], dict):
                    self.printErrorMsg("JSON数据['data']：" + str(page["data"]) + " 不是一个字典, user id: " + str(userId))
                    break
                if not page["data"].has_key("photo_list"):
                    self.printErrorMsg("在JSON数据：" + str(page["data"]) + " 中没有找到'photo_list'字段, user id: " + str(userId))
                    break
                for imageInfo in page["data"]["photo_list"]:
                    if not isinstance(imageInfo, dict):
                        self.printErrorMsg("JSON数据['photo_list']：" + str(imageInfo) + " 不是一个字典, user id: " + str(userId))
                        continue
                    if imageInfo.has_key("pic_host"):
                        imageUrl = imageInfo["pic_host"]
                    else:
                        imageUrl = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                    if imageInfo.has_key("pic_name"):
                        # 将第一张image的URL保存到新id list中
                        if newUserIdList[userId][3] == "":
                            newUserIdList[userId][3] = imageInfo["pic_name"]
                        # 检查是否已下载到前一次的图片
                        if len(userIdList[userId]) >= 4:
                            if imageInfo["pic_name"] == userIdList[userId][3]:
                                isPass = True
                                isError = False
                                break
                        imageUrl += "/large/" + imageInfo["pic_name"]
                    else:
                        self.printErrorMsg("在JSON数据：" + str(imageInfo) + " 中没有找到'pic_name'字段, user id: " + str(userId))
                    self.printStepMsg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                    while True:
                        imgByte = self.doGet(imageUrl)
                        if imgByte:
                            md5Digest = md5.new(imgByte).hexdigest()
                            # 处理获取的文件为weibo默认获取失败的图片
                            if md5Digest == 'd29352f3e0f276baaf97740d170467d7' or md5Digest == '7bd88df2b5be33e1a79ac91e7d0376b5':
                                self.printStepMsg("源文件获取失败，重试")
                            else:
                                fileType = imageUrl.split(".")[-1]
                                if fileType.find('/') != -1:
                                    fileType = 'jpg'
                                imageFile = open(imagePath + "\\" + str("%04d" % imageCount) + "." + fileType, "wb")
                                imageFile.write(imgByte)
                                self.printStepMsg("下载成功")
                                imageFile.close()
                                imageCount += 1
                                break
                        else:
                            self.printErrorMsg("下载图片失败，用户ID：" + str(userId) + "，图片地址：" + imageUrl)
                            break 
                    # 达到配置文件中的下载数量，结束
                    if self.getImageCount > 0 and imageCount > self.getImageCount:
                        isPass = True
                        break
                if isPass:
                    break
                if totalImageCount / self.IMAGE_COUNT_PER_PAGE > pageCount - 1:
                    pageCount += 1
                else:
                    # 全部图片下载完毕
                    break
            
            self.printStepMsg(userName + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userId][2] = str(int(newUserIdList[userId][2]) + imageCount - 1)
            allImageCount += imageCount - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + userName
                    if os.path.exists(destPath):
                        if os.path.isdir(destPath):
                            self.printStepMsg("图片保存目录：" + destPath + " 已存在，删除中")
                            self.removeDirFiles(destPath)
                        else:
                            self.printStepMsg("图片保存目录：" + destPath + "已存在相同名字的文件，自动删除")
                            os.remove(destPath)
                    self.printStepMsg("创建图片保存目录：" + destPath)
                    if not self.createDir(destPath):
                        self.printErrorMsg("创建图片保存目录： " + destPath + " 失败，程序结束！")
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
                    self.printStepMsg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self.printErrorMsg(userName + "图片数量异常，请手动检查")
                
            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, 'a')
            newUserIdListFile.write("\t".join(newUserIdList[userId]) + "\n")
            newUserIdListFile.close()

        # 排序并保存新的idList.txt
        tempList = []
        tempUserIdList = sorted(newUserIdList.keys())
        for index in tempUserIdList:
            tempList.append("\t".join(newUserIdList[index]))
        newUserIdListString = "\n".join(tempList)
        newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        self.printStepMsg("保存新存档文件：" + newUserIdListFilePath)
        newUserIdListFile = open(newUserIdListFilePath, 'w')
        newUserIdListFile.write(newUserIdListString)
        newUserIdListFile.close()
        
        stopTime = time.time()
        self.printStepMsg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(allImageCount) + "张")

if __name__ == '__main__':
    weibo().main()
