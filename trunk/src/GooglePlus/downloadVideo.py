# -*- coding:utf-8  -*-
'''
Created on 2013-4-14

@author: rena
'''

import os
import sys
import time
import traceback
import urllib2

class downloadVideo():
    
    def getTime(self):
        return time.strftime('%H:%M:%S', time.localtime(time.time()))
    
    def printMsg(self, msg):
        msg = self.getTime() + " " + msg
        print msg
        
    def proxy(self):
        proxyHandler = urllib2.ProxyHandler({'https':"http://" + self.proxyIp + ":" + self.proxyPort})
        opener = urllib2.build_opener(proxyHandler)
        urllib2.install_opener(opener)
        self.printMsg("proxy set succeed")
        
    def doGet(self, url):
        if url.find("http") == -1:
            return None
        count = 0
        while 1:
            try:
                request = urllib2.Request(url)
                if sys.version_info < (2, 7):
                    response = urllib2.urlopen(request)
                else:
                    response = urllib2.urlopen(request, timeout=20)
                return response.read()
            except Exception, e:
                self.printMsg(str(e))
                traceback.print_exc()
            count += 1
            if count > 10:
                self.printMsg("can not connection " + url)
                return False

    # mode 0 : 直接赋值
    # mode 1 : 字符串拼接
    # mode 2 : 取整
    def getConfig(self, config, key, defaultValue, mode, addValue=None):
        value = None
        if config.has_key(key):
            if mode == 0:
                value = config[key]
            elif mode == 1:
                value = addValue + config[key]
            elif mode == 2:
                try:
                    value = int(config[key])
                except:
                    self.printMsg("'" + key + "' must is a number in config.ini, default value")
                    value = 1
        else:
            self.printMsg("Not found '" + key + "' in config.ini, default value")
            value = defaultValue
        return value
    
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
        self.allVideoFilePath = self.getConfig(config, "ALL_VIDEO_FILE_NAME", processPath + "\\info\\allVideo.txt", 1, processPath + "\\")
        self.newVideoFilePath = self.getConfig(config, "NEW_VIDEO_FILE_NAME", processPath + "\\info\\video_download.txt", 1, processPath + "\\")
        self.resultFilePath = self.getConfig(config, "GET_VIDEO_DOWNLOAD_URL_FILE_NAME", processPath + "\\info\\get_result.html", 1, processPath + "\\")
        self.idListFilePath = self.getConfig(config, "MEMBER_UID_LIST_FILE_NAME", processPath + "\\info\\idlist.txt", 1, processPath + "\\")
        self.isProxy = self.getConfig(config, "IS_PROXY", 1, 2)
        self.proxyIp = self.getConfig(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.getConfig(config, "PROXY_PORT", "8087", 0)
        self.printMsg("config init succeed")
        
    def main(self):
        # 设置代理
        if self.isProxy == 1:
            self.proxy()
        allVideoList = {}
        newVideoList = {}
        username = ""
        # 解析保存已经获得的url地址的文件
        allFile = open(self.allVideoFilePath, 'r')
        lines = allFile.readlines()
        allFile.close()
        for line in lines:
            line = line.replace("\n", "")
            if line.find("https:") != -1:
                url = line[line.find("https:"):]
                allVideoList[username].append(url)
            elif line.find("****************************************************************************************************") != -1:
                username = ""
            else:
                username = line
                if username in allVideoList:
                    pass
                else:
                    allVideoList[username] = []
        
        # 解析需要下载的url地址的文件
        newFile = open(self.newVideoFilePath, 'r')
        lines = newFile.readlines()
        newFile.close()
        for line in lines:
            line = line.replace("\n", "")
            if line.find("https:") != -1:
                url = line[line.find("https:"):]
                newVideoList[username][len(allVideoList[username]) + 1] = url
                allVideoList[username].append(url)
            elif line.find("****************************************************************************************************") != -1:
                username = ""
            elif line.replace(" ", "") == "":
                pass
            else:
                username = line
                if username in allVideoList:
                    pass
                else:
                    self.printMsg("new member: " + username)
                    allVideoList[username] = []
                if username in newVideoList:
                    pass
                else:
                    newVideoList[username] = {}
        
        # 获取需要下载视频的真实url地址
        resultFile = open(self.resultFilePath, 'w')
        resultFile.close()
        videoUrlList = []
        videoCount = 0
        for member in newVideoList:
            videoIdList = []
            memberPostPage = None
            for index in newVideoList[member]:
                url = newVideoList[member][index]
                messagePage = self.doGet(url)
                if not messagePage:
                    self.printMsg("can not get this page: " + url)
                    continue
                videoIndex = messagePage.find("video.googleusercontent.com")
                isFind = False
                while videoIndex != -1:
                    if messagePage.find("token", videoIndex, videoIndex + 50) != -11:
                        videStart = messagePage.find("http", videoIndex - 10)
                        videStop = messagePage.find('"', videStart)
                        videoUrl = messagePage[videStart:videStop]
                        videoUrl = videoUrl.replace("\u003d", '=')
                        if not videoUrl in videoUrlList:
                            videoUrlList.append(videoUrl)
                            self.printMsg(member.split(" ")[1] + " " + str(index) + ": " + videoUrl)
                            resultFile = open(self.resultFilePath, 'a')
                            resultFile.writelines("<a href=" + videoUrl + ">" + str(member + "_" + "%03d" % index) + "</a><br>\n")
                            resultFile.close()
                            videoCount += 1
                            isFind = True
                    videoIndex = messagePage.find("video.googleusercontent.com", videoIndex + 1)
                if not isFind:
                    videoIdIndex = messagePage.find("redirector.googlevideo.com")
                    while videoIdIndex != -1:
                        videoIdStart = messagePage.find("?id=", videoIdIndex)
                        videoIdStop = messagePage.find("&", videoIdStart)
                        videoId = messagePage[videoIdStart + 8:videoIdStop]
                        if not (videoId in videoIdList):
                            videoIdList.append(videoId)
                            if memberPostPage == None:
                                memberPostPage = self.doGet("https://plus.google.com/photos/" + member.split(" ")[0] + "/albums/posts")
                            videStart = memberPostPage.find("http", (memberPostPage.find("video.googleusercontent.com", memberPostPage.find(videoId))) - 10)
                            videStop = memberPostPage.find('"' , videStart)
                            videoUrl = memberPostPage[videStart:videStop]
                            videoUrl = videoUrl.replace("\u003d", '=')
                            if not videoUrl in videoUrlList:
                                videoUrlList.append(videoUrl)
                                self.printMsg(member.split(" ")[1] + " " + str(index) + ": " + videoUrl)
                                resultFile = open(self.resultFilePath, 'a')
                                resultFile.writelines("<a href=" + videoUrl + ">" + str(member + "_" + "%03d" % index) + "</a><br>\n")
                                resultFile.close()
                                videoCount += 1
                        videoIdIndex = messagePage.find("redirector.googlevideo.com", videoIdIndex + 1)
        self.printMsg("get " + str(videoCount) + " videos")
        
        #获取member保存路径
        
        # 保存所有url地址到新文件
        newAllVideoFilePath = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + "allVideo.txt"
        testFile = open(newAllVideoFilePath, 'w')
        for member in allVideoList:
            testFile.writelines(member + "\n")
            for videoIndex in range(len(allVideoList[member])):
                testFile.writelines(str(videoIndex + 1) + ": " + allVideoList[member][videoIndex] + "\n")
            testFile.writelines("****************************************************************************************************\n")
        testFile.close()

if __name__ == '__main__':
    downloadVideo().main()
