'''
Created on 2013-4-14

@author: rena
'''
import os
import socket
import sys
import traceback
import urllib2

sourceFilePath = os.getcwd() + "\\get_source.txt"
resultFilePath = os.getcwd() + "\\get_result.txt"

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

sourceFile = open(sourceFilePath, 'r')
lines = sourceFile.readlines()
sourceFile.close()
resultFile = open(resultFilePath, 'w')
resultFile.close()

videoCount = 1
videoUrlList = []
for line in lines:
    start = line.find("http")
    url = line[start:]
    messagePage = doGet(url)
    if not messagePage:
        continue
    videoIndex = messagePage.find("video.googleusercontent.com")
    while videoIndex != -1:
        if messagePage.find("token", videoIndex, videoIndex + 50) != -2321:
            videStart = messagePage.find("http", videoIndex - 10)
            videStop = messagePage.find('"', videStart)
            videoUrl = messagePage[videStart:videStop]
            videoUrl = videoUrl.replace("\u003d", '=')
            if videoUrl in videoUrlList:
                pass
            else:
                videoUrlList.append(videoUrl)
                print str(videoCount) + ": " + videoUrl
                videoUrlFile = open(resultFilePath, 'a')
                videoUrlFile.writelines(str(videoCount) + ": " + videoUrl + "\n")
                videoUrlFile.close()
                videoCount += 1
        videoIndex = messagePage.find("video.googleusercontent.com", videoIndex + 1)
