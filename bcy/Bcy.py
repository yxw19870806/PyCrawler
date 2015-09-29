# -*- coding:UTF-8  -*-
'''
Created on 2015-6-23

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

import copy
import os
import re
import time

from common import common, json


class Bcy(common.Tool):

    def __init__(self):
        super(Bcy, self).__init__()
        self.print_msg("配置文件读取完成")

    def _trace(self, msg):
        super(Bcy, self).trace(msg, self.is_show_error, self.traceLogPath)
    
    def _print_error_msg(self, msg):
        super(Bcy, self).print_error_msg(msg, self.is_show_error, self.errorLogPath)
        
    def _print_step_msg(self, msg):
        super(Bcy, self).print_step_msg(msg, self.is_show_error, self.stepLogPath)

    def main(self):
        startTime = time.time()

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self._print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.isProxy == 1 or self.isProxy == 2:
            self.set_proxy(self.proxyIp, self.proxyPort, "https")

        # 设置系统cookies (fire fox)
        if not self.set_cookie(self.cookiePath, self.browserVersion):
            self._print_error_msg("导入浏览器cookies失败，程序结束！")
            self.process_exit()

        # 寻找idlist，如果没有结束进程
        userIdList = {}
        if os.path.exists(self.userIdListFilePath):
            userListFile = open(self.userIdListFilePath, "r")
            allUserList = userListFile.readlines()
            userListFile.close()
            for userInfo in allUserList:
                if len(userInfo) < 3:
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
            # 如果没有数量，则为0
            if len(newUserIdList[newUserId]) < 2:
                newUserIdList[newUserId].append("0")
            if newUserIdList[newUserId][1] == '':
                newUserIdList[newUserId][1] = 0
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(newUserIdList[newUserId]) < 3:
                newUserIdList[newUserId].append("")
            else:
                newUserIdList[newUserId][2] = ""

        totalImageCount = 0
        # 循环下载每个id
        for userId in sorted(userIdList.keys()):
            if len(userIdList[userId]) >= 2 and userIdList[userId][1] != '':
                cn = userIdList[userId][1]
            else:
                cn = userId
            self._print_step_msg("CN: " + cn)
            cpId = int(userId) - 100876
            pageCount = 1
            maxPageCount = -1
            needMakeDownloadDir = True
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(userIdList[userId]) > 3 and userIdList[userId][2] != '':
                isError = True
            else:
                isError = False
            isPass = False

            while 1:
                photoAlbumUrl = 'http://bcy.net/coser/ajaxShowMore?type=all&cp_id=%s&p=%s' % (cpId, pageCount)
                photoAlbumPage = self.do_get(photoAlbumUrl)

                try:
                    photoAlbumPage = json.read(photoAlbumPage)
                except:
                    self._print_error_msg("返回信息不是一个JSON数据, user id: " + str(userId))
                    break

                # 总共多少页
                if maxPageCount == -1:
                    try:
                        maxPageData = photoAlbumPage['data']['page']
                    except:
                        self._print_error_msg("在JSON数据：" + str(photoAlbumPage) + " 中没有找到'page'字段, user id: " + str(userId))
                        break
                    if not maxPageData:
                        maxPageCount = 1
                    else:
                        pageList = re.findall(u'<a href=\\"\\/coser\\/ajaxShowMore\?type=all&cp_id=' + str(cpId) + '&p=(\d)', maxPageData)
                        maxPageCount = int(max(pageList))

                try:
                    photoAlbumPageData = photoAlbumPage['data']['data']
                except:
                    self._print_error_msg("在JSON数据：" + str(photoAlbumPage) + " 中没有找到'data'字段, user id: " + str(userId))
                    break

                for data in photoAlbumPageData:
                    try:
                        rpId = data['rp_id']
                        title = data['title'].encode('utf-8').strip()
                        # 过滤一些无法作为文件夹路径的符号
                        filter_list = [':', '\\', '/', '.', '*', '?', '"', '<', '>', '|']
                        for filter_char in filter_list:
                            title.replace(filter_char, '')
                    except:
                        self._print_error_msg("在JSON数据：" + str(data) + " 中没有找到'ur_id'或'title'字段, user id: " + str(userId))
                        break

                    if newUserIdList[userId][2] == "":
                        newUserIdList[userId][2] = rpId
                    # 检查是否已下载到前一次的图片
                    if len(userIdList[userId]) >= 3:
                        if int(rpId) <= int(userIdList[userId][2]):
                            isError = False
                            isPass = True
                            break

                    self._print_step_msg("rp: " + rpId)

                    # CN目录
                    imagePath = self.imageDownloadPath + "\\" + cn

                    if needMakeDownloadDir:
                        if not self.make_dir(imagePath, 1):
                            self._print_error_msg("创建CN目录： " + imagePath + " 失败，程序结束！")
                            self.process_exit()
                        needMakeDownloadDir = False

                    # 正片目录
                    if title != '':
                        rpPath = imagePath + "\\" + rpId + ' ' + title
                    else:
                        rpPath = imagePath + "\\" + rpId
                    if not self.make_dir(rpPath, 1):
                         # 目录出错，把title去掉后再试一次，如果还不行退出
                        self._print_error_msg("创建正片目录： " + rpPath + " 失败，尝试不使用title！")
                        rpPath = imagePath + "\\" + rpId
                        if not self.make_dir(rpPath, 1):
                            self._print_error_msg("创建正片目录： " + rpPath + " 失败，程序结束！")
                            self.process_exit()

                    rpUrl = 'http://bcy.net/coser/detail/%s/%s' % (cpId, rpId)
                    rpPage = self.do_get(rpUrl)
                    if rpPage:
                        imageCount = 0
                        imageIndex = rpPage.find("src='")
                        while imageIndex != -1:
                            imageStart = rpPage.find("http", imageIndex)
                            imageStop = rpPage.find("'", imageStart)
                            imageUrl = rpPage[imageStart:imageStop]
                            # 禁用指定分辨率
                            imageUrl = "/".join(imageUrl.split("/")[0:-1])
                            imageCount += 1
                            self._print_step_msg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                            if imageUrl.rfind('/') < imageUrl.rfind('.'):
                                fileType = imageUrl.split(".")[-1]
                            else:
                                fileType = 'jpg'
                            if self.save_image(imageUrl, rpPath + "\\" + str("%03d" % imageCount) + "." + fileType):
                                self._print_step_msg("下载成功")
                            imageIndex = rpPage.find("src='", imageIndex + 1)
                        if imageCount == 0:
                            self._print_error_msg(cn + ": "  + rpId + " 没有任何图片")
                        totalImageCount += imageCount
                if isPass:
                    break
                if pageCount >= maxPageCount:
                    break
                pageCount += 1

            self._print_step_msg(cn + "下载完毕")

            if isError:
                self._print_error_msg(userId + "图片数量异常，请手动检查")

            # 保存最后的信息
            newUserIdListFile = open(newUserIdListFilePath, "a")
            newUserIdListFile.write("\t".join(newUserIdList[userId]) + "\n")
            newUserIdListFile.close()

        stopTime = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(totalImageCount) + "张")

if __name__ == "__main__":
    Bcy().main()
