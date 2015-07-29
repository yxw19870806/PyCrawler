# -*- coding:utf-8  -*-
'''
Created on 2013-12-15

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
濡傛湁闂鎴栧缓璁鑱旂郴
'''

from common import common
import os
import shutil
import time

class twintail(common.Tool):

    def trace(self, msg):
        super(twintail, self).trace(msg, self.isShowError, self.traceLogPath)
    
    def print_error_msg(self, msg):
        super(twintail, self).print_error_msg(msg, self.isShowError, self.errorLogPath)
        
    def print_step_msg(self, msg):
        super(twintail, self).print_step_msg(msg, self.isShowError, self.stepLogPath)
        
    def __init__(self):
        processPath = os.getcwd()
        configFile = open(processPath + "\\..\\common\\config.ini", "r")
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
                    self.print_msg(str(e))
                    pass
        # 绋嬪簭閰嶇疆
        self.isLog = self.get_config(config, "IS_LOG", 1, 2)
        self.isShowError = self.get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.isDebug = self.get_config(config, "IS_DEBUG", 1, 2)
        self.isShowStep = self.get_config(config, "IS_SHOW_STEP", 1, 2)
        # 浠ｇ悊
        self.isProxy = self.get_config(config, "IS_PROXY", 2, 2)
        self.proxyIp = self.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxyPort = self.get_config(config, "PROXY_PORT", "8087", 0)
        # 鏂囦欢璺緞
        self.errorLogPath = self.get_config(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        self.traceLogPath = self.get_config(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
        self.stepLogPath = self.get_config(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
        self.imageDownloadPath = self.get_config(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.print_msg("閰嶇疆鏂囦欢璇诲彇瀹屾垚")
            
    def main(self):
        # 鏃ュ織鏂囦欢淇濆瓨鐩綍
        if self.isLog == 1:
            stepLogDir = os.path.dirname(self.stepLogPath)
            if not self.createDir(stepLogDir):
                self.print_error_msg("鍒涘缓姝ラ鏃ュ織鐩綍锛�" + stepLogDir + " 澶辫触锛岀▼搴忕粨鏉燂紒")
                self.process_exit()
            self.print_step_msg("姝ラ鏃ュ織鐩綍涓嶅瓨鍦紝鍒涘缓鏂囦欢澶癸細" + stepLogDir)
            traceLogDir = os.path.dirname(self.traceLogPath)
            if not self.createDir(traceLogDir):
                self.print_error_msg("鍒涘缓璋冭瘯鏃ュ織鐩綍锛�" + traceLogDir + " 澶辫触锛岀▼搴忕粨鏉燂紒")
                self.process_exit()
            self.print_step_msg("璋冭瘯鏃ュ織鐩綍涓嶅瓨鍦紝鍒涘缓鏂囦欢澶癸細" + traceLogDir)
        errorLogDir = os.path.dirname(self.errorLogPath)
        if not self.createDir(errorLogDir):
            self.print_error_msg("鍒涘缓閿欒鏃ュ織鐩綍锛�" + errorLogDir + " 澶辫触锛岀▼搴忕粨鏉燂紒")
            self.process_exit()
        if os.path.exists(self.imageDownloadPath):
            # 璺緞鏄洰褰�
            if os.path.isdir(self.imageDownloadPath):
                # 鐩綍涓嶄负绌�
                if os.listdir(self.imageDownloadPath):
                    isDelete = False
                    while not isDelete:
                        # 鎵嬪姩杈撳叆鏄惁鍒犻櫎鏃ф枃浠跺す涓殑鐩綍
                        input = raw_input(self.get_time() + " 鍥剧墖淇濆瓨鐩綍锛�" + self.imageDownloadPath + " 宸茬粡瀛樺湪锛屾槸鍚﹂渶瑕佸垹闄よ鏂囦欢澶瑰苟缁х画绋嬪簭锛�(Y)es or (N)o: ")
                        try:
                            input = input.lower()
                            if input in ["y", "yes"]:
                                isDelete = True
                            elif input in ["n", "no"]:
                                self.process_exit()
                        except Exception, e:
                            self.print_error_msg(str(e))
                            pass
                    self.print_step_msg("鍒犻櫎鍥剧墖淇濆瓨鐩綍锛�" + self.imageDownloadPath)
                    # 鍒犻櫎鐩綍
                    shutil.rmtree(self.imageDownloadPath, True)
                    # 淇濇姢锛岄槻姝㈡枃浠惰繃澶氬垹闄ゆ椂闂磋繃闀匡紝5绉掓鏌ヤ竴娆℃枃浠跺す鏄惁宸茬粡鍒犻櫎
                    while os.path.exists(self.imageDownloadPath):
                        shutil.rmtree(self.imageDownloadPath, True)
                        time.sleep(5)
            else:
                self.print_step_msg("鍥剧墖淇濆瓨鐩綍锛�" + self.imageDownloadPath + "宸插瓨鍦ㄧ浉鍚屽悕瀛楃殑鏂囦欢锛岃嚜鍔ㄥ垹闄�")
                os.remove(self.imageDownloadPath)
        self.print_step_msg("鍒涘缓鍥剧墖淇濆瓨鐩綍锛�" + self.imageDownloadPath)
        if not self.createDir(self.imageDownloadPath):
            self.print_error_msg("鍒涘缓鍥剧墖淇濆瓨鐩綍锛�" + self.imageDownloadPath + " 澶辫触锛岀▼搴忕粨鏉燂紒")
            self.process_exit()
        # 璁剧疆浠ｇ悊
        if self.isProxy == 1 or self.isProxy == 2:
            self.set_proxy(self.proxyIp, self.proxyPort, "http")
        
        url = "http://twintail-japan.com/campus/contents/%s.html"
        imageUrl = "http://twintail-japan.com/campus/contents/%s"
        allImageCount = 0
        for pageNumber in range(69, 80):
            page = self.do_get(url % pageNumber)
            page = page.decode('utf-8')
            if not page:
                self.print_msg("涓嬭浇缁撴潫")
                self.process_exit()
            nameStart = page.find(u"鍚嶅墠 /")
            nameStop = page.find("(", nameStart)
            name = page[nameStart + 4:nameStop].replace(" ", "").replace("\n", "").encode('GBK')
            print nameStart,nameStop,name
            self.trace("椤甸潰鍦板潃:" + url % pageNumber)
            self.print_msg("鍚嶅瓧锛�" + name)
            imagePath = self.imageDownloadPath + "\\" + ("%02d" % pageNumber) + " " + name
            if os.path.exists(imagePath):
                shutil.rmtree(imagePath, True)
            if not self.createDir(imagePath):
                self.print_error_msg("鍒涘缓鍥剧墖涓嬭浇鐩綍锛�" + imagePath + " 澶辫触锛岀▼搴忕粨鏉燂紒")
                self.process_exit()
            imageCount = 1
            if page == False:
                break
            imageStart = page.find("<span>")
            while imageStart != -1:
                imageStop = page.find("</span>", imageStart)
                imageUrlPath = page[imageStart + 6:imageStop].encode('GBK')
                imgByte = self.do_get(imageUrl % imageUrlPath)
                if imgByte:
                    fileType = (imageUrl % imageUrlPath).split(".")[-1]
                    imageFile = open(imagePath + "\\" + str("%02d" % imageCount) + "." + fileType, "wb")
                    self.print_msg("寮�濮嬩笅杞界" + str(imageCount) + "寮犲浘鐗囷細" + imageUrl % imageUrlPath)
                    imageFile.write(imgByte)
                    imageFile.close()
                    self.print_msg("涓嬭浇鎴愬姛")
                    imageCount += 1
                imageStart = page.find("<span>", imageStart + 1)
            allImageCount += imageCount

if __name__ == "__main__":
    twintail().main()
