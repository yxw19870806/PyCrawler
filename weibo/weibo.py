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
    
    def print_error_msg(self, msg):
        super(Weibo, self).print_error_msg(msg, self.isShowError, self.errorLogPath)
        
    def print_step_msg(self, msg):
        super(Weibo, self).print_step_msg(msg, self.isShowError, self.stepLogPath)
        
    def visit(self, url):
        tempPage = self.do_get(url)
        if tempPage:
            redirectUrlIndex = tempPage.find("location.replace")           
            if redirectUrlIndex != -1:
                redirectUrlStart = tempPage.find("'", redirectUrlIndex) + 1
                redirectUrlStop = tempPage.find("'", redirectUrlStart)
#                 redirectUrlStart = tempPage.find('"', redirectUrlIndex) + 1
#                 redirectUrlStop = tempPage.find('"', redirectUrlStart)
                redirectUrl = tempPage[redirectUrlStart:redirectUrlStop]
                return str(self.do_get(redirectUrl))
            elif tempPage.find("用户名或密码错误") != -1:
                self.print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                self.process_exit()
            else:
                try:
                    tempPage = tempPage.decode("utf-8")
                    if tempPage.find("用户名或密码错误") != -1:
                        self.print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                        self.process_exit()
                except Exception, e:
                    pass
                return str(tempPage)
        return False

    def __init__(self):
        config = self.analyze_config( os.getcwd() + "\\..\\common\\config.ini")
        # 每次请求获取的图片数量
        self.IMAGE_COUNT_PER_PAGE = 20
        # 程序配置
        self.isLog = self.get_config(config, "IS_LOG", 1, 2)
        self.isShowError = self.get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.get_config(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.get_config(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.get_config(config, "IS_SORT", 1, 2)
        self.getImageCount = self.get_config(config, "GET_IMAGE_COUNT", 0, 2)
        # 代理设置
        self.isProxy = self.get_config(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.get_config(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.get_config(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ''
            self.stepLogPath = ''
        else:
            self.traceLogPath = self.get_config(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.get_config(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.get_config(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.get_config(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.userIdListFilePath = self.get_config(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)
        # 操作系统&浏览器
        self.browerVersion = self.get_config(config, "BROWSER_VERSION", 2, 2)
        self.osVersion = self.get_config(config, "OS_VERSION", 1, 2)
        # cookie
        self.isAutoGetCookie = self.get_config(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if self.isAutoGetCookie == 0:
            self.cookiePath = self.get_config(config, "COOKIE_PATH", "", 0)
        else:
            self.cookiePath = self.get_default_browser_cookie_path(self.osVersion, self.browerVersion)
        self.print_msg("配置文件读取完成")
            
    def main(self, userIdListFilePath = '', imageDownloadPath = '', imageTempPath = ''):
        if userIdListFilePath != '':
            self.userIdListFilePath = userIdListFilePath
        if imageDownloadPath != '':
            self.imageDownloadPath = imageDownloadPath
        if imageTempPath != '':
            self.imageTempPath = imageTempPath
        startTime = time.time()

        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.make_dir(stepLogDir, 0):
                self.print_error_msg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                self.process_exit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.make_dir(traceLogDir, 0):
                self.print_error_msg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                self.process_exit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.make_dir(errorLogDir, 0):
            self.print_error_msg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
            self.process_exit()

        # 图片保存目录
        self.print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self.print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.isProxy == 1:
            self.set_proxy(self.proxyIp, self.proxyPort, "http")
        # 设置系统cookies (fire fox)
        if not self.set_cookie(self.cookiePath, self.browerVersion):
            self.print_error_msg("导入浏览器cookies失败，程序结束！")
            self.process_exit()

        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.userIdListFilePath):
            userListFile = open(self.userIdListFilePath, 'r')
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                if len(userInfo) < 5:
                    continue
                userInfo = userInfo.replace("\xef\xbb\xbf", "")
                userInfo = userInfo.replace(" ", "")
                userInfo = userInfo.replace("\n", "")
                userInfo = userInfo.replace("\r", "")
                userInfoList = userInfo.split("\t")
                userIdList[userInfoList[0]] = userInfoList
        else:
            self.print_error_msg("用户ID存档文件：" + self.userIdListFilePath + "不存在，程序结束！")
            self.process_exit()

        # 创建临时存档文件
        newUserIdListFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.userIdListFilePath)[-1]
        newUserIdListFile = open(newUserIdListFilePath, 'w')
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
            # 处理成员队伍信息
            if len(newUserIdList[newUserId]) < 5:
                newUserIdList[newUserId].append("")

        allImageCount = 0
        for userId in sorted(userIdList.keys()):
            userName = newUserIdList[userId][1]
            self.print_step_msg("UID: " + str(userId) + "，Name: " + userName)
            # 初始化数据
            pageCount = 1
            imageCount = 1
            isPass = False
            if len(userIdList[userId]) <= 3 or userIdList[userId][3] == '':
                isError = False
            else:
                isError = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.isSort == 1:
                imagePath = self.imageTempPath
            else:
                imagePath = self.imageDownloadPath + "\\" + userName
            if not self.make_dir(imagePath, 1):
                self.print_error_msg("创建图片下载目录：" + imagePath + " 失败，程序结束！")
                self.process_exit()

            # 日志文件插入信息
            while 1:
                photoAlbumUrl = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (userId, self.IMAGE_COUNT_PER_PAGE, pageCount)
                self.trace("相册专辑地址：" + photoAlbumUrl)
                photoPageData = self.visit(photoAlbumUrl)
                self.trace("返回JSON数据：" + photoPageData)
                try:
                    page = json.read(photoPageData)
                except:
                    self.print_error_msg("返回信息不是一个JSON数据, user id: " + str(userId))
                    break

                # 总的图片数
                try:
                    totalImageCount = page["data"]["total"]
                except:
                    self.print_error_msg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(userId))
                    break

                try:
                    photoList = page["data"]["photo_list"]
                except:
                    self.print_error_msg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(userId))
                    break

                for imageInfo in photoList:
                    if not isinstance(imageInfo, dict):
                        self.print_error_msg("JSON数据['photo_list']：" + str(imageInfo) + " 不是一个字典, user id: " + str(userId))
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
                        tryCount = 0
                        while True:
                            if tryCount > 1:
                                imageHost = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                            imageUrl = imageHost + "/large/" + imageInfo["pic_name"]
                            if tryCount == 0:
                                self.print_step_msg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                            else:
                                self.print_step_msg("重试下载第" + str(imageCount) + "张图片：" + imageUrl)
                            imgByte = self.do_get(imageUrl)
                            if imgByte:
                                md5Digest = md5.new(imgByte).hexdigest()
                                # 处理获取的文件为weibo默认获取失败的图片
                                if md5Digest == 'd29352f3e0f276baaf97740d170467d7' or md5Digest == '7bd88df2b5be33e1a79ac91e7d0376b5':
                                    self.print_step_msg("源文件获取失败，重试")
                                else:
                                    fileType = imageUrl.split(".")[-1]
                                    if fileType.find('/') != -1:
                                        fileType = 'jpg'
                                    imageFile = open(imagePath + "\\" + str("%04d" % imageCount) + "." + fileType, "wb")
                                    imageFile.write(imgByte)
                                    self.print_step_msg("下载成功")
                                    imageFile.close()
                                    imageCount += 1
                                break
                            else:
                                tryCount += 1
                            if tryCount >= 5:
                                self.print_error_msg("下载图片失败，用户ID：" + str(userId) + ", 第" + str(imageCount) +  "张，图片地址：" + imageUrl)
                                break
                            
                    else:
                        self.print_error_msg("在JSON数据：" + str(imageInfo) + " 中没有找到'pic_name'字段, user id: " + str(userId))
                           
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
            
            self.print_step_msg(userName + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userId][2] = str(int(newUserIdList[userId][2]) + imageCount - 1)
            allImageCount += imageCount - 1
            
            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + userName
                    if not self.make_dir(destPath, 1):
                        self.print_error_msg("创建图片子目录： " + destPath + " 失败，程序结束！")
                        self.process_exit()

                    # 倒叙排列
                    if len(userIdList[userId]) >= 3:
                        count = int(userIdList[userId][2]) + 1
                    else:
                        count = 1
                    for fileName in imageList:
                        fileType = fileName.split(".")[1]
                        self.copy_files(imagePath + "\\" + fileName, destPath + "\\" + str("%04d" % count) + "." + fileType)
                        count += 1
                    self.print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self.print_error_msg(userName + "图片数量异常，请手动检查")
                
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
#         self.print_step_msg("保存新存档文件：" + newUserIdListFilePath)
#         newUserIdListFile = open(newUserIdListFilePath, 'w')
#         newUserIdListFile.write(newUserIdListString)
#         newUserIdListFile.close()
        
        stopTime = time.time()
        self.print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(allImageCount) + "张")

if __name__ == '__main__':
    Weibo().main(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\weibo1", os.getcwd() +  "\\photo\\weibo1\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\weibo2", os.getcwd() +  "\\photo\\weibo2\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\weibo3", os.getcwd() +  "\\photo\\weibo3\\tempImage")
    Weibo().main(os.getcwd() + "\\info\\idlist_4.txt", os.getcwd() +  "\\photo\\weibo4", os.getcwd() +  "\\photo\\weibo4\\tempImage")

