# -*- coding:utf-8  -*-
'''
Created on 2013-4-14

@author: rena
'''
import os
import socket
import sys
import time
import traceback
import urllib2

allFilePath = os.getcwd() + "\\info\\allVideo.txt"
newFilePath = os.getcwd() + "\\info\\video_download.txt"
newResultFilePath = os.getcwd() + "\\info\\get_result.html"
allResultFilePath = os.getcwd() + "\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + "allVideo.txt"

if socket.gethostbyname(socket.gethostname()).find("192.168.") != -1:
    proxyIp = "127.0.0.1"
    proxyPort = "8087"
    proxyHandler = urllib2.ProxyHandler({'https':"http://" + proxyIp + ":" + proxyPort})
    opener = urllib2.build_opener(proxyHandler)
    urllib2.install_opener(opener)

def doGet(url):
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
            print e
            traceback.print_exc()
        count += 1
        if count > 10:
            return False

allVideoList = {}
newVideoList = {}
username = ""

# 解析保存已经获得的url地址的文件
allFile = open(allFilePath, 'r')
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
newFile = open(newFilePath, 'r')
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
            print "new member: " + username
            allVideoList[username] = []
        if username in newVideoList:
            pass
        else:
            newVideoList[username] = {}

# 获取需要下载视频的真实url地址
resultFile = open(newResultFilePath, 'w')
resultFile.close()
videoUrlList = []
videoCount = 0
 
for member in newVideoList:
    videoIdList = []
    memberPostPage = None
    for index in newVideoList[member]:
        url = newVideoList[member][index]
        messagePage = doGet(url)
        if not messagePage:
            print "can not get this page: " + url
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
                    print member.split(" ")[1] + " " + str(index) + ": " + videoUrl
                    resultFile = open(newResultFilePath, 'a')
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
                        memberPostPage = doGet("https://plus.google.com/photos/" + member.split(" ")[0] + "/albums/posts")
                    videStart = memberPostPage.find("http", (memberPostPage.find("video.googleusercontent.com", memberPostPage.find(videoId))) - 10)
                    videStop = memberPostPage.find('"' , videStart)
                    videoUrl = memberPostPage[videStart:videStop]
                    videoUrl = videoUrl.replace("\u003d", '=')
                    if not videoUrl in videoUrlList:
                        videoUrlList.append(videoUrl)
                        print member.split(" ")[1] + " " + str(index) + ": " + videoUrl
                        resultFile = open(newResultFilePath, 'a')
                        resultFile.writelines("<a href=" + videoUrl + ">" + str(member + "_" + "%03d" % index) + "</a><br>\n")
                        resultFile.close()
                        videoCount += 1
                videoIdIndex = messagePage.find("redirector.googlevideo.com", videoIdIndex + 1)
print str(videoCount) + " videos"

# 保存所有url地址到新文件
testFile = open("test.txt", 'w')
for i in allVideoList:
    testFile.writelines(i + "\n")
    for j in range(len(allVideoList[i])):
        testFile.writelines(str(j + 1) + ": " + allVideoList[i][j] + "\n")
    testFile.writelines("****************************************************************************************************\n")
testFile.close()
