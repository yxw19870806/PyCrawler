#-*- coding:utf-8  -*-
'''
Created on 2013-5-6

@author: haruka
'''

import os
import shutil
import socket
import sys
import traceback
import urllib2

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
            print "url: " + url
            traceback.print_exc()
        count += 1
        if count > 10:
            print "can not connection " + url
            return False

def download(imageUrl, imagePath, imageCount):
    imgByte = doGet(imageUrl)
    if imgByte:
        fileType = imageUrl.split(".")[-1]
        imageFile = open(imagePath + "\\" + str("%03d" % imageCount) + "." + fileType, "wb")
        print "start download " + str(imageCount) + ": " + imageUrl
        imageFile.write(imgByte)
        imageFile.close()
        print "download succeed"
    else:
        print "down load image error: " + imageUrl
                    
if socket.gethostbyname(socket.gethostname()).find("192.168.") != -1:
    proxyIp = "127.0.0.1"
    proxyPort = "8087"
    proxyHandler = urllib2.ProxyHandler({'https':"http://" + proxyIp + ":" + proxyPort})
    opener = urllib2.build_opener(proxyHandler)
    urllib2.install_opener(opener)

rootPath = os.getcwd() + "\\shinoda"

# 下载
url = "http://blog.mariko-shinoda.net/index%s.html"
indexCount = 1
allImageCount = 1
while True:
    imageCount = 1
    imagePath = rootPath + "\\" + str("%03d" % indexCount)
    
    if indexCount > 1:
        indexPage = doGet(url % ("_" + str(indexCount)))
    else:
        indexPage = doGet(url % (""))
#    f = open("test.txt", 'w')
#    f.write(indexPage)
#    f.close()
#    sys.exit()
    if indexPage:
        if not os.path.exists(imagePath):
            os.makedirs(imagePath)
        # old image:
        imageIndex = 0
        while True:
            imageIndex = indexPage.find('<a href="http://mariko-shinoda.up.seesaa.net', imageIndex)
            if imageIndex == -1:
                break
            imageStart = indexPage.find("http", imageIndex) 
            imageStop = indexPage.find('"', imageStart)
            imageUrl = indexPage[imageStart:imageStop]
            if imageUrl.find("data") == -1:
                download(imageUrl, imagePath, imageCount)
                imageCount += 1
                allImageCount += 1
            imageIndex += 1
        # new image:
        imageIndex = 0
        while True:
            imageIndex = indexPage.find('<img src="http://blog.mariko-shinoda.net', imageIndex)
            if imageIndex == -1:
                break
            imageStart = indexPage.find("http", imageIndex) 
            imageStop = indexPage.find('"', imageStart)
            imageUrl = indexPage[imageStart:imageStop]
            if imageUrl.find("data") == -1:
                download(imageUrl, imagePath, imageCount)
                imageCount += 1
                allImageCount += 1
            imageIndex += 1          
    else:
        print "down load over!, count: " + str(allImageCount)
        sys.exit()
    indexCount += 1

# 排序
destPath = rootPath + "\\all"
allImageCount = 1
if not os.path.exists(destPath):
    os.makedirs(destPath)
for index1 in sorted(os.listdir(rootPath), reverse=True):
    for fileName in sorted(os.listdir(rootPath + "\\" + index1), reverse=True):
        imagePath = rootPath + "\\" + index1 + "\\" + fileName
        fileType = fileName.split(".")[-1]
        shutil.copyfile(imagePath, destPath + "\\" + str("%05d" % allImageCount) + "." + fileType)
        allImageCount += 1
print "sorted over!, count: " + str(allImageCount)

