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
import re
import shutil
import time


class GooglePlus(common.Tool):

    def __init__(self):
        super(GooglePlus, self).__init__()
        self.print_msg("配置文件读取完成")

    def _trace(self, msg):
        super(GooglePlus, self).trace(msg, self.isShowError, self.traceLogPath)

    def _print_error_msg(self, msg):
        super(GooglePlus, self).print_error_msg(msg, self.isShowError, self.errorLogPath)

    def _print_step_msg(self, msg):
        super(GooglePlus, self).print_step_msg(msg, self.isShowError, self.stepLogPath)

    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            step_log_dir = os.path.dirname(self.stepLogPath)
            if not self.make_dir(step_log_dir, 0):
                self._print_error_msg("创建步骤日志目录：" + step_log_dir + " 失败，程序结束！")
                self.process_exit()
            trace_log_dir = os.path.dirname(self.traceLogPath)
            if not self.make_dir(trace_log_dir, 0):
                self._print_error_msg("创建调试日志目录：" + trace_log_dir + " 失败，程序结束！")
                self.process_exit()
        error_log_dir = os.path.dirname(self.errorLogPath)
        if not self.make_dir(error_log_dir, 0):
            self._print_error_msg("创建错误日志目录：" + error_log_dir + " 失败，程序结束！")
            self.process_exit()

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self._print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.set_proxy(self.proxyIp, self.proxyPort, "https")

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
            self._print_error_msg("用户ID存档文件: " + self.userIdListFilePath + "不存在，程序结束！")
            self.process_exit()
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
            # 处理成员队伍信息
            if len(newUserIdList[newUserId]) < 5:
                newUserIdList[newUserId].append("")

        totalImageCount = 0
        # 循环下载每个id
        for userId in sorted(userIdList.keys()):
            userName = newUserIdList[userId][1]
            self._print_step_msg("ID: " + str(userId) + ", 名字: " + userName)
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
            if not self.make_dir(imagePath, 1):
                self._print_error_msg("创建图片下载目录： " + imagePath + " 失败，程序结束！")
                self.process_exit()

            # 图片下载
#            photoAlbumUrl = "https://plus.google.com/photos/%s/albums/posts?banner=pwa" % (userId)
            photoAlbumUrl = 'https://plus.google.com/_/photos/pc/read/'
            now = time.time() * 100
            key = ''
            postData = 'f.req=[["posts",null,null,"synthetic:posts:%s",3,"%s",null],[%s,1,null],"%s",null,null,null,null,null,null,null,2]&at=AObGSAj1ll9iGT-1d05vTuxV5yygWelh9g:%s&' % (userId, userId, self.getImageUrlCount, key, now)
            self._trace("信息首页地址：" + photoAlbumUrl)
            photoAlbumPage = self.do_get(photoAlbumUrl, postData)
            if photoAlbumPage:
                messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId)
                isOver = False
                while messageIndex != -1:
                    messageStart = photoAlbumPage.find("http", messageIndex)
                    messageStop = photoAlbumPage.find('"', messageStart)
                    messageUrl = photoAlbumPage[messageStart:messageStop]
                    messageUrl.replace('\u003d', '=')
                    # 将第一张image的URL保存到新id list中
                    if newUserIdList[userId][3] == "":
                        # 有可能拿到带authkey的，需要去掉
                        # https://picasaweb.google.com/116300481938868290370/2015092603?authkey\u003dGv1sRgCOGLq-jctf-7Ww#6198800191175756402
                        try:
                            temp = re.findall('(.*)\?.*(#.*)', messageUrl)
                            newUserIdList[userId][3] = temp[0][0] + temp[0][1]
                        except:
                            newUserIdList[userId][3] = messageUrl
                    # 检查是否已下载到前一次的图片
                    if len(userIdList[userId]) >= 4 and userIdList[userId][3].find("picasaweb.google.com/") != -1:
                        if messageUrl == userIdList[userId][3]:
                            isError = False
                            break
                    self._trace("message URL:" + messageUrl)
                    # 判断是否重复
                    if messageUrl in messageUrlList:
                        messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex + 1)
                        continue
                    messageUrlList.append(messageUrl)
                    messagePage = self.do_get(messageUrl)
                    if not messagePage:
                        self._print_error_msg("无法获取信息页: " + messageUrl)
                        messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex + 1)
                        continue
                    flag = messagePage.find("<div><a href=")
                    while flag != -1:
                        imageIndex = messagePage.find("<img src=", flag, flag + 200)
                        if imageIndex == -1:
                            self._print_error_msg("信息页：" + messageUrl + " 中没有找到标签'<img src='")
                            break
                        imageStart = messagePage.find("http", imageIndex)
                        imageStop = messagePage.find('"', imageStart)
                        imageUrl = messagePage[imageStart:imageStop]
                        self._trace("image URL:" + imageUrl)
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
                        self._print_step_msg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                        imgByte = self.do_get(imageUrl)
                        if imgByte:
                            # 文件类型
                            if imageUrl.rfind('/') < imageUrl.rfind('.'):
                                fileType = imageUrl.split(".")[-1]
                            else:
                                fileType = 'jpg'
                            # 保存图片
                            imageFile = open(imagePath + "\\" + str("%04d" % imageCount) + "." + fileType, "wb")
                            imageFile.write(imgByte)
                            self._print_step_msg("下载成功")
                            imageFile.close()
                            imageCount += 1
                        else:
                            self._print_error_msg("获取第" + str(imageCount) + "张图片信息失败：" + str(userId) + ": " + imageUrl)
                        # 达到配置文件中的下载数量，结束
                        if len(userIdList[userId]) >= 4 and userIdList[userId][3] != '' and self.getImageCount > 0 and imageCount > self.getImageCount:
                            isOver = True
                            break
                        flag = messagePage.find("<div><a href=", flag + 1)
                    if isOver:
                        break
                    messageIndex = photoAlbumPage.find('[["https://picasaweb.google.com/' + userId, messageIndex + 1)
            else:
                self._print_error_msg("无法获取相册首页: " + photoAlbumUrl + ' ' + userName)

            self._print_step_msg(userName + "下载完毕，总共获得" + str(imageCount - 1) + "张图片")
            newUserIdList[userId][2] = str(int(newUserIdList[userId][2]) + imageCount - 1)
            totalImageCount += imageCount - 1

            # 排序
            if self.isSort == 1:
                imageList = sorted(os.listdir(imagePath), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(imageList) >= 1:
                    destPath = self.imageDownloadPath + "\\" + newUserIdList[userId][4] + "\\" + userName
                    if not self.make_dir(destPath, 1):
                        self._print_error_msg("创建图片子目录： " + destPath + " 失败，程序结束！")
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
                    self._print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(imagePath, True)

            if isError:
                self._print_error_msg(userName + "图片数量异常，请手动检查")

            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, "a")
            newUserIdListFile.write("\t".join(newUserIdList[userId]) + "\n")
            newUserIdListFile.close()

        stopTime = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(totalImageCount) + "张")

if __name__ == "__main__":
    GooglePlus().main()
