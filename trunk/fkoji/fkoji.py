# -*- coding:UTF-8  -*-
'''
Created on 2014-2-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''
from common import common
from common import BeautifulSoup
import os
import shutil
import sys
import time
                
class fkoji(common.Tool):
    
    def _trace(self, msg):
        super(fkoji, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def _print_error_msg(self, msg):
        super(fkoji, self).print_error_msg(msg, self.isShowError, self.errorLogPath)
        
    def _print_step_msg(self, msg):
        super(fkoji, self).print_step_msg(msg, self.isShowError, self.stepLogPath)
         
    def __init__(self):
        config = self.analyze_config( os.getcwd() + "\\..\\common\\config.ini")
        # 程序配置
        self.isLog = self.get_config(config, "IS_LOG", 1, 2)
        self.isShowError = self.get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.get_config(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.get_config(config, "IS_SHOW_STEP", 1, 2)
        self.isSort = self.get_config(config, "IS_SORT", 1, 2)
        self.getImagePageCount = self.get_config(config, "GET_IMAGE_PAGE_COUNT", 1, 2)
        # 代理
        self.isProxy = self.get_config(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.get_config(config, "PROXY_PORT", "8087", 0)
        # 文件路径
        self.errorLogPath = self.get_config(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        if self.isLog == 0:
            self.traceLogPath = ""
            self.stepLogPath = ""
        else:
            self.traceLogPath = self.get_config(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.stepLogPath = self.get_config(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.get_config(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.imageTempPath = self.get_config(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)
        self.print_msg("配置文件读取完成")

    def main(self):
        startTime = time.time()
        # 判断各种目录是否存在
        # 日志文件保存目录
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.make_dir(stepLogDir, 0):
                self._print_error_msg("创建步骤日志目录：" + stepLogDir + " 失败，程序结束！")
                self.process_exit()
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.make_dir(traceLogDir, 0):
                self._print_error_msg("创建调试日志目录：" + traceLogDir + " 失败，程序结束！")
                self.process_exit()
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.make_dir(errorLogDir, 0):
            self._print_error_msg("创建错误日志目录：" + errorLogDir + " 失败，程序结束！")
            self.process_exit()

         # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.imageDownloadPath)
        if not self.make_dir(self.imageDownloadPath, 2):
            self._print_error_msg("创建图片根目录：" + self.imageDownloadPath + " 失败，程序结束！")
            self.process_exit()

        # 图片下载临时目录
        if self.isSort == 1:
            self._print_step_msg("创建图片下载目录：" + self.imageTempPath)
            if not self.make_dir(self.imageTempPath, 2):
                self._print_error_msg("创建图片下载目录：" + self.imageTempPath + " 失败，程序结束！")
                self.process_exit()

        # 设置代理
        if self.isProxy == 1:
            self.set_proxy(self.proxyIp, self.proxyPort, "http")

        # 寻找fkoji.save，如果没有结束进程
        saveFilePath = "fkoji.save"
        lastImageUrl = ""
        imageStartIndex = 0
        userIdList = {}
        if os.path.exists(saveFilePath):
            saveFile = open(saveFilePath, "r")
            lines = saveFile.readlines()
            saveFile.close()
            if len(lines) >= 1:
                info = lines[0].split("\t")
                if len(info) >= 2:
                    imageStartIndex = int(info[0])
                    lastImageUrl = info[1].replace("\xef\xbb\xbf", "").replace("\n", "").replace(" ", "")
                for line in lines[1:]:
                    line = line.lstrip().rstrip().replace(" ", "")
                    info = line.split("\t")
                    if len(info) >= 2:
                        userIdList[info[0]] = info[1]

        # 下载
        url = "http://jigadori.fkoji.com/?p=%s"
        pageIndex = 1
        imageCount = 1
        isOver = False
        newLastImageUrl = ""
        imageUrlList = []
        if self.isSort == 1:
            imagePath = self.imageTempPath
        else:
            imagePath = self.imageDownloadPath
        while True:
            if isOver:
                break
            # 达到配置文件中的下载数量，结束
            if self.getImagePageCount != 0 and pageIndex > self.getImagePageCount:
                break
            indexUrl = url % str(pageIndex)
            self._trace("网页地址：" + indexUrl)
            indexPage = self.do_get(indexUrl)
            indexPage = BeautifulSoup.BeautifulSoup(indexPage)
     
            photoList = indexPage.body.findAll("div", "photo")
            # 已经下载到最后一页
            if not photoList:
                break
            for photoInfo in photoList:
                if isinstance(photoInfo, BeautifulSoup.NavigableString):
                    continue
                tags = photoInfo.findAll("span")
                # 找userId
                for tag in tags:
                    subTag = tag.next.next
                    if isinstance(subTag, BeautifulSoup.NavigableString):
                        if subTag.find("@") == 0:
                            userId = subTag[1:].encode("GBK")
                # 找图片
                tags = photoInfo.findAll("img")
                for tag in tags:
                    tagAttrs = dict(tag.attrs)
                    if tagAttrs.has_key("src") and tagAttrs.has_key("alt"):
                        imageUrl = str(tagAttrs["src"]).replace(" ", "").encode("GBK")
                        if newLastImageUrl == "":
                            newLastImageUrl = imageUrl
                        # 检查是否已下载到前一次的图片
                        if lastImageUrl == imageUrl:
                            isOver = True
                            break
                        self._trace("id: " + userId + "，地址: " + imageUrl)
                        if imageUrl in imageUrlList:
                            continue
                        # 文件类型
                        fileType = imageUrl.split(".")[-1]
                        if fileType.find('/') != -1:
                            fileType = 'jpg'
                        imageFile = open(imagePath + "\\" + str("%05d" % imageCount) + "_" + str(userId) + "." + fileType, "wb")
                        self._print_step_msg("开始下载第" + str(imageCount) + "张图片：" + imageUrl)
                        imgByte = self.do_get(imageUrl)
                        if imgByte:
                            imageFile.write(imgByte)
                            self._print_step_msg("下载成功")
                        else:
                            self._print_error_msg("获取图片" + str(imageCount) + "信息失败：" + imageUrl)
                        imageFile.close()
                        imageCount += 1
                if isOver:
                    break
            pageIndex += 1   
        self._print_step_msg("下载完毕")

        # 排序复制到保存目录
        if self.isSort == 1:
            isCheckOk = False
            while not isCheckOk:
                # 等待手动检测所有图片结束
                input = raw_input(self.get_time() + " 已经下载完毕，是否下一步操作？ (Y)es or (N)o: ")
                try:
                    input = input.lower()
                    if input in ["y", "yes"]:
                        isCheckOk = True
                    elif input in ["n", "no"]:
                        self.process_exit()
                except:
                    pass
            if not self.make_dir(self.imageDownloadPath + "\\all", 1):
                self._print_error_msg("创建目录：" + self.imageDownloadPath + "\\all" + " 失败，程序结束！")
                self.process_exit()

            for fileName in sorted(os.listdir(self.imageTempPath), reverse=True):
                imageStartIndex += 1
                imagePath = self.imageTempPath + "\\" + fileName
                fileNameList = fileName.split(".")
                fileType = fileNameList[-1]
                userId = "_".join(".".join(fileNameList[:-1]).split("_")[1:])
                # 所有
                self.copy_files(imagePath, self.imageDownloadPath + "\\all\\" + str("%05d" % imageStartIndex) + "_" + userId + "." + fileType)
                # 单个
                eachUserPath = self.imageDownloadPath + "\\" + userId
                if not os.path.exists(eachUserPath):
                    if not self.make_dir(eachUserPath, 1):
                        self._print_error_msg("创建目录：" + eachUserPath + " 失败，程序结束！")
                        self.process_exit()

                if userIdList.has_key(userId):
                    userIdList[userId] = int(userIdList[userId]) + 1
                else:
                    userIdList[userId] = 1
                self.copy_files(imagePath, eachUserPath + "\\" + str("%05d" % userIdList[userId]) + "." + fileType)
            self._print_step_msg("图片从下载目录移动到保存目录成功")
            # 删除下载临时目录中的图片
            shutil.rmtree(self.imageTempPath, True)
            
        # 保存新的存档文件
        newSaveFilePath = os.getcwd() + "\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(saveFilePath)[-1]
        self._print_step_msg("保存新存档文件: " + newSaveFilePath)
        newSaveFile = open(newSaveFilePath, "w")
        newSaveFile.write(str(imageStartIndex) + "\t" + newLastImageUrl + "\n")
        tempList = []
        tempUserIdList = sorted(userIdList.keys())
        for userId in tempUserIdList:
            tempList.append(userId + "\t" + str(userIdList[userId]))
        newUserIdListString = "\n".join(tempList)
        newSaveFile.write(newUserIdListString)
        newSaveFile.close()
        stopTime = time.time()
        self._print_step_msg("成功下载最新图片，耗时" + str(int(stopTime - startTime)) + "秒，共计图片" + str(imageCount - 1) + "张")

if __name__ == "__main__":
    fkoji().main()
