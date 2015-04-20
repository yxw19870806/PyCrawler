# -*- coding:UTF-8  -*-
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

class Weibo(common.Tool):
    
    def trace(self, msg):
        super(Weibo, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def printErrorMsg(self, msg):
        super(Weibo, self).printErrorMsg(msg, self.isShowError, self.errorLogPath)
        
    def printStepMsg(self, msg):
        super(Weibo, self).printStepMsg(msg, self.isShowError, self.stepLogPath)
        
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
        self.imageDownloadPath = self.getConfig(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.getConfig(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.userIdListFilePath = self.getConfig(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
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
            
    def main(self, userIdListFilePath = '', imageDownloadPath = '', imageTempPath = ''):
        if userIdListFilePath != '':
            self.userIdListFilePath = userIdListFilePath
        if imageDownloadPath != '':
            self.imageDownloadPath = imageDownloadPath
        if imageTempPath != '':
            self.imageTempPath = imageTempPath
        startTime = time.time()
        # 判断各种目录是否存在
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.makeDir(stepLogDir):
                self.printErrorMsg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                self.processExit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.makeDir(traceLogDir):
                self.printErrorMsg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                self.processExit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.makeDir(errorLogDir):
            self.printErrorMsg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
            self.processExit()

        # 图片保存目录
        self.printStepMsg("创建图片根目录：" + self.imageDownloadPath)
        if not self.makeDir(self.imageDownloadPath, 2):
            self.printErrorMsg("创建图片根目录：" + errorLogDir + " 失败，程序结束！")
            self.processExit()

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

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userName
            if os.path.exists(imagePath):
                shutil.rmtree(imagePath, True)
            if not self.makeDir(imagePath, 1):
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
                        if imageInfo.has_key("pic_host"):
                            imageHost = imageInfo["pic_host"]
                        else:
                            imageHost = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                        tryCoount = 0
                        while True:
                            if tryCoount > 1:
                                imageHost = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                            imageUrl = imageHost + "/large/" + imageInfo["pic_name"]
                            if tryCoount == 0:
                                self.printStepMsg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                            else:
                                self.printStepMsg("重试下载第" + str(imageCount) + "张图片：" + imageUrl)
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
                                tryCoount += 1
                            if tryCoount >= 5:
                                self.printErrorMsg("下载图片失败，用户ID：" + str(userId) + ", 第" + str(imageCount) +  "张，图片地址：" + imageUrl)
                                break
                            
                    else:
                        self.printErrorMsg("在JSON数据：" + str(imageInfo) + " 中没有找到'pic_name'字段, user id: " + str(userId))
                           
                    # 达到配置文件中的下载数量，结束
                    if len(userIdList[userId]) >= 4 and userIdList[userId][3] != '' and self.getImageCount > 0 and imageCount > self.getImageCount:
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
#         tempList = []
#         tempUserIdList = sorted(newUserIdList.keys())
#         for index in tempUserIdList:
#             tempList.append("\t".join(newUserIdList[index]))
#         newUserIdListString = "\n".join(tempList)
#         newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
#         self.printStepMsg("保存新存档文件：" + newUserIdListFilePath)
#         newUserIdListFile = open(newUserIdListFilePath, 'w')
#         newUserIdListFile.write(newUserIdListString)
#         newUserIdListFile.close()
        
        stopTime = time.time()
        self.printStepMsg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(allImageCount) + "张")

if __name__ == '__main__':
    Weibo().main(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\weibo1", os.getcwd() +  "\\photo\\weibo1\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\weibo2", os.getcwd() +  "\\photo\\weibo2\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\weibo3", os.getcwd() +  "\\photo\\weibo3\\tempImage")

