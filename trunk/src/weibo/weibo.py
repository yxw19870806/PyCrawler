# -*- coding:utf-8  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json
import codecs
import copy
import os
import random
import shutil
import time

class weibo(common.Tool):
    
    def visit(self, url):
        tempPage = self.doGet(url)
        if tempPage:
            redirectUrlIndex = tempPage.find("location.replace")
            if redirectUrlIndex != -1:
                redirectUrlStart = tempPage.find('"', redirectUrlIndex) + 1
                redirectUrlStop = tempPage.find('"', redirectUrlStart)
                redirectUrl = tempPage[redirectUrlStart:redirectUrlStop]
                return str(self.doGet(redirectUrl))
            elif tempPage.find(u"用户名或密码错误") != -1:
                self.printErrorMsg(u"登陆状态异常，请在浏览器中重新登陆微博账号", self.isShowError, self.isLog)
                self.processExit()
            else:
                try:
                    tempPage = tempPage.decode("utf-8")
                    if tempPage.find(u"用户名或密码错误") != -1:
                        self.printErrorMsg(u"登陆状态异常，请在浏览器中重新登陆微博账号", self.isShowError, self.isLog)
                        self.processExit()
                except Exception, e:
                    self.printErrorMsg(str(e), self.isShowError, self.isLog)
                return str(tempPage)
        return False

    def __init__(self):
        processPath = os.getcwd()
        configFile = codecs.open(processPath + "\\..\\common\\config.ini", 'r', 'GBK')
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
        self.memberUIdListFilePath = self.getConfig(config, "MEMBER_UID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
        # 每次请求获取的图片数量
        self.IMAGE_COUNT_PER_PAGE = 20
        # 配置文件获取程序配置
        self.isLog = self.getConfig(config, "IS_LOG", 1, 2)
        self.isShowError = self.getConfig(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.getConfig(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.getConfig(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.getConfig(config, "IS_SORT", 1, 2)
        self.getImageCount = self.getConfig(config, "GET_IMAGE_COUNT", 1, 2)
        self.isProxy = self.getConfig(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        # 操作系统&浏览器
        self.browerVersion = self.getConfig(config, "BROWSER_VERSION", 2, 2)
        self.osVersion = self.getConfig(config, "OS_VERSION", 1, 2)
        # cookie
        self.isAutoGetCookie = self.getConfig(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if self.isAutoGetCookie == 0:
            self.cookiePath = self.getConfig(config, "COOKIE_PATH", "", 0)
        else:
            self.cookiePath = self.getDefaultBrowserCookiePath(self.osVersion, self.browerVersion)
        self.printMsg(u"配置文件读取完成")
            
    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not os.path.exists(stepLogDir):
                if not self.createDir(stepLogDir):
                    self.printErrorMsg(u"创建步骤日志目录：" + stepLogDir + u" 失败，程序结束！", self.isShowError, self.isLog)
                    self.processExit()
                self.printStepMsg(u"步骤日志目录不存在，创建文件夹: " + stepLogDir, self.isShowError, self.isLog)
            errorLogDir = os.path.dirname(self.errorLogPath)
            if not os.path.exists(errorLogDir):
                if not self.createDir(errorLogDir):
                    self.printErrorMsg(u"创建错误日志目录：" + errorLogDir + u" 失败，程序结束！", self.isShowError, self.isLog)
                    self.processExit()
                self.printStepMsg(u"错误日志目录不存在，创建文件夹: " + errorLogDir, self.isShowError, self.isLog)
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not os.path.exists(traceLogDir):
                if not self.createDir(traceLogDir):
                    self.printErrorMsg(u"创建调试日志目录：" + traceLogDir + u" 失败，程序结束！", self.isShowError, self.isLog)
                    self.processExit()
                self.printStepMsg(u"调试日志目录不存在，创建文件夹: " + traceLogDir, self.isShowError, self.isLog)
        if os.path.exists(self.imageDownloadPath):
            if os.path.isdir(self.imageDownloadPath):
                isDelete = False
                while not isDelete:
                    input = raw_input(u"图片保存目录：" + self.imageDownloadPath + u" 已存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                    try:
                        input = input.lower()
                        if input in ["y", "yes"]:
                            isDelete = True
                        elif input in ["n", "no"]:
                            self.processExit()
                    except Exception, e:
                        self.printErrorMsg(str(e), self.isShowError, self.isLog)
                        pass
                self.printStepMsg(u"删除图片保存目录: " + self.imageDownloadPath, self.isShowError, self.isLog)
                shutil.rmtree(self.imageDownloadPath, True)
                # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                while os.path.exists(self.imageDownloadPath):
                    time.sleep(5)
            else:
                self.printStepMsg(u"图片保存目录: " + self.imageDownloadPath + u"已存在相同名字的文件，自动删除", self.isShowError, self.isLog)
                os.remove(self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.printErrorMsg(u"创建图片下载目录：" + self.imageDownloadPath + u" 失败，程序结束！", self.isShowError, self.isLog)
            self.processExit()
        self.printStepMsg(u"创建图片保存目录: " + self.imageDownloadPath, self.isShowError, self.isLog)
        # 设置代理
        if self.isProxy == 1:
            self.proxy(self.proxyIp, self.proxyPort, "http")
        # 设置系统cookies (fire fox)
        if not self.cookie(self.cookiePath, self.browerVersion):
            self.printErrorMsg(u"导入浏览器cookies失败，程序结束！", self.isShowError, self.isLog)
            self.processExit()
        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.memberUIdListFilePath):
            userListFile = codecs.open(self.memberUIdListFilePath, 'r', 'GBK')
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.printErrorMsg(u"用户ID存档文件: " + self.memberUIdListFilePath + u"不存在，程序结束！", self.isShowError, self.isLog)
            self.processExit()
        newMemberUidListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.memberUIdListFilePath)[-1]
        newMemberUidListFile = codecs.open(newMemberUidListFilePath, 'w', 'GBK')
        newMemberUidListFile.close()

        newMemberUidList = copy.deepcopy(userIdList)
        for newUserId in newMemberUidList:
            # 如果没有名字，则名字用uid代替
            if len(newMemberUidList[newUserId]) < 2:
                newMemberUidList[newUserId].append(newMemberUidList[newUserId][0])
            # 如果没有初试image count，则为0
            if len(newMemberUidList[newUserId]) < 3:
                newMemberUidList[newUserId].append("0")
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(newMemberUidList[newUserId]) < 4:
                newMemberUidList[newUserId].append("")
            else:
                newMemberUidList[newUserId][3] = ""
            # 处理member 队伍信息
            if len(newMemberUidList[newUserId]) < 5:
                newMemberUidList[newUserId].append("")
        allImageCount = 0
        for userId in sorted(userIdList.keys()):
            userName = newMemberUidList[userId][1]
            self.printStepMsg("UID: " + str(userId) + "，Member: " + userName, self.isShowError, self.isLog)
            # 初始化数据
            pageCount = 1
            imageCount = 1
            totalImageCount = 0
            isPass = False
            isError = False
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userName
            if os.path.exists(imagePath):
                shutil.rmtree(imagePath, True)
            if not self.createDir(imagePath):
                self.printErrorMsg(u"创建图片下载目录：" + imagePath + u" 失败，程序结束！", self.isShowError, self.isLog)
                self.processExit()
            # 日志文件插入信息
            while 1:
                photoAlbumUrl = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (userId, self.IMAGE_COUNT_PER_PAGE, pageCount)
                self.trace("相册专辑地址：" + photoAlbumUrl, self.isShowError, self.isLog)
                photoPageData = self.visit(photoAlbumUrl)
                self.trace("返回JSON数据：" + photoPageData, self.isShowError, self.isLog)
                try:
                    page = json.read(photoPageData)
                except:
                    self.printErrorMsg(u"返回信息：" + str(photoPageData) + u" 不是一个JSON数据", self.isShowError, self.isLog)
                    break
#                 self.processExit()
                if not isinstance(page, dict):
                    self.printErrorMsg(u"JSON数据：" + str(page) + u" 不是一个字典", self.isShowError, self.isLog)
                    break
                if not page.has_key("data"):
                    self.printErrorMsg(u"在JSON数据：" + str(page) + u" 中没有找到'data'字段", self.isShowError, self.isLog)
                    break
                if totalImageCount == 0:
                    if page["data"].has_key("total"):
                        totalImageCount = page["data"]["total"]
                    else:
                        self.printErrorMsg(u"在JSON数据：" + str(page) + u" 中没有找到'total'字段", self.isShowError, self.isLog)
                        isPass = True
                        break
                if not isinstance(page["data"], dict):
                    self.printErrorMsg(u"JSON数据['data']：" + str(page["data"]) + u" 不是一个字典", self.isShowError, self.isLog)
                    break
                if not page["data"].has_key("photo_list"):
                    self.printErrorMsg(u"在JSON数据：" + str(page["data"]) + u" 中没有找到'photo_list'字段", self.isShowError, self.isLog)
                    break
                for imageInfo in page["data"]["photo_list"]:
                    if not isinstance(imageInfo, dict):
                        self.printErrorMsg(u"JSON数据['photo_list']：" + str(imageInfo) + u" 不是一个字典", self.isShowError, self.isLog)
                        continue
                    if imageInfo.has_key("pic_host"):
                        imageUrl = imageInfo["pic_host"]
                    else:
                        imageUrl = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                    if imageInfo.has_key("pic_name"):
                        # 将第一张image的URL保存到新id list中
                        if newMemberUidList[userId][3] == "":
                            newMemberUidList[userId][3] = imageInfo["pic_name"]
                        # 检查是否已下载到前一次的图片
                        if len(userIdList[userId]) >= 4:
                            if imageInfo["pic_name"] == userIdList[userId][3]:
                                isPass = True
                                break
                        imageUrl += "/large/" + imageInfo["pic_name"]
                    else:
                        self.printErrorMsg(u"在JSON数据：" + str(imageInfo) + u" 中没有找到'pic_name'字段", self.isShowError, self.isLog)
                    self.printStepMsg(u"开始下载第" + str(imageCount) + u"张图片：" + imageUrl, self.isShowError, self.isLog)
                    imgByte = self.doGet(imageUrl)
                    if imgByte:
                        fileType = imageUrl.split(".")[-1]
                        filename = str("%04d" % imageCount)
                        imageFile = open(imagePath + "\\" + str(filename) + "." + fileType, "wb")
                        imageFile.write(imgByte)
                        imageFile.close()
                        self.printStepMsg(u"下载成功", self.isShowError, self.isLog)
                        imageCount += 1
                    else:
                        self.printErrorMsg(u"下载图片失败，用户ID：" + str(userId) + u"，图片地址: " + imageUrl, self.isShowError, self.isLog)
                if isPass:
                    break
                if totalImageCount / self.IMAGE_COUNT_PER_PAGE > pageCount - 1:
                    pageCount += 1
                else:
                    # 全部图片下载完毕
                    break
            
            if len(userIdList[userId]) >= 4 and userIdList[userId][3] != "" and int(newMemberUidList[userId][2]) != 0 and (imageCount * 2) > int(newMemberUidList[userId][2]):
                isError = 1
            if int(newMemberUidList[userId][2]) == 0 and imageCount - 1 != totalImageCount:
                isError = 2
            
            self.printStepMsg(userName + u"下载完毕，总共获得" + str(imageCount - 1) + u"张图片", self.isShowError, self.isLog)
            newMemberUidList[userId][2] = str(int(newMemberUidList[userId][2]) + imageCount - 1)
            allImageCount += imageCount - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + userName
                    if os.path.exists(destPath):
                        if os.path.isdir(destPath):
                            self.printStepMsg(u"图片保存目录: " + destPath + u" 已存在，删除中", self.isShowError, self.isLog)
                            self.removeDirFiles(destPath)
                        else:
                            self.printStepMsg(u"图片保存目录: " + destPath + u"已存在相同名字的文件，自动删除", self.isShowError, self.isLog)
                            os.remove(destPath)
                    self.printStepMsg(u"创建图片保存目录: " + destPath, self.isShowError, self.isLog)
                    if not self.createDir(destPath):
                        self.printErrorMsg(u"创建图片保存目录： " + destPath + u" 失败，程序结束！", self.isShowError, self.isLog)
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
                    self.printStepMsg(u"图片从下载目录移动到保存目录成功", self.isShowError, self.isLog)
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError == 1:
                self.printErrorMsg(userName + u"图片数量异常，请手动检查", self.isShowError, self.isLog)
            elif isError == 2:
                self.printErrorMsg(userName + u"图片数量" + str(imageCount) + u"张，小于相册图片数量" + str(totalImageCount) + u"张，请手动检查", self.isShowError, self.isLog)

            # 保存最后的信息
            newMemberUidListFile = codecs.open(newMemberUidListFilePath, 'a', 'GBK')
            newMemberUidListFile.write("\t".join(newMemberUidList[userId]) + "\n")
            newMemberUidListFile.close()

        # 排序并保存新的idList.txt
        tempList = []
        tempUserIdList = sorted(newMemberUidList.keys())
        for index in tempUserIdList:
            tempList.append("\t".join(newMemberUidList[index]))
        newMemberUidListString = "\n".join(tempList)
        newMemberUidListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.memberUIdListFilePath)[-1]
        self.printStepMsg(u"保存新存档文件：" + newMemberUidListFilePath, self.isShowError, self.isLog)
        newMemberUidListFile = codecs.open(newMemberUidListFilePath, 'w', 'GBK')
        newMemberUidListFile.write(newMemberUidListString)
        newMemberUidListFile.close()
        
        stopTime = time.time()
        self.printStepMsg(u"存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + u"秒，共计图片" + str(allImageCount) + u"张", self.isShowError, self.isLog)

if __name__ == '__main__':
    weibo().main()
