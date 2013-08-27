# -*- coding:utf-8  -*-
'''
Created on 2013-7-16

@author: Administrator
'''

IS_SET_TIMEOUT = False

class Tool():
    
    # http请求
    def doGet(self, url):
        import sys
        import traceback
        import urllib2
        global IS_SET_TIMEOUT
        if url.find("http") == -1:
            return None
        count = 0
        while 1:
            try:
                request = urllib2.Request(url)
                # 设置头信息
                request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0 FirePHP/0.7.2')
                if sys.version_info < (2, 7):
                    if not IS_SET_TIMEOUT:
                        urllib2.socket.setdefaulttimeout(20)
                        IS_SET_TIMEOUT = True
                    response = urllib2.urlopen(request)
                else:
                    response = urllib2.urlopen(request, timeout=20)
                return response.read()
            except Exception, e:
                # 代理无法访问
                if str(e).find("[Errno 10061] ") != -1:
                    input = raw_input("please check your proxy setting! Type in (Y)es to continue or (N)o to exit process!: ").lower()
                    if input in ["y", "yes"]:
                        pass
                    elif input in ["n", "no"]:
                        sys.exit()
                # 超时
                elif str(e).find("timed out") != -1:
                    self.printMsg("time out, try again")
                else:
                    self.printMsg(str(e))
                    traceback.print_exc()
            count += 1
            if count > 10:
                self.printMsg("can not connection " + url)
                return False
    
    # 使用系统cookies
    def cookie(self, filePath):
        import cookielib
        import cStringIO
        import os
        import urllib2
        from pysqlite2 import dbapi2 as sqlite
        if not os.path.exists(filePath):
            self.printMsg(filePath + " not exist")
            return False
        con = sqlite.connect(filePath)
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        ftstr = ["FALSE", "TRUE"]
        s = cStringIO.StringIO()
        s.write("# Netscape HTTP Cookie File\n")
        for item in cur.fetchall():
            a = "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (item[0], ftstr[item[0].startswith('.')], item[1], ftstr[item[2]], item[3], item[4], item[5])
            s.write(a)
        s.seek(0)
        cookieJar = cookielib.MozillaCookieJar()
        cookieJar._really_load(s, '', True, True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        urllib2.install_opener(opener)
        return True
    
    # 设置代理
    def proxy(self, ip, port):
        import urllib2
        proxyHandler = urllib2.ProxyHandler({'https':"http://" + ip + ":" + port})
        opener = urllib2.build_opener(proxyHandler)
        urllib2.install_opener(opener)
        self.printMsg("proxy set succeed")
                
    # 获取配置文件
    # config : 字典格式，如：{key1:value1, key2:value2}
    # mode 0 : 直接赋值
    # mode 1 : 字符串拼接
    # mode 2 : 取整
    # prefix: 前缀，只有在mode=1时有效
    # postfix: 后缀，只有在mode=1时有效
    def getConfig(self, config, key, defaultValue, mode, prefix=None, postfix=None):
        value = None
        if config.has_key(key):
            if mode == 0:
                value = config[key]
            elif mode == 1:
                value = config[key]
                if prefix != None:
                    value = prefix + value
                if postfix != None:
                    value = value + postfix
            elif mode == 2:
                try:
                    value = int(config[key])
                except:
                    self.printMsg("'" + key + "' must is a number in config.ini, default value")
                    value = defaultValue
        else:
            self.printMsg("Not found '" + key + "' in config.ini, default value")
            value = defaultValue
        return value
    
    def printMsg(self, msg, isTime=True):
        if isTime:
            msg = self.getTime() + " " + msg
        print msg
    
    def getTime(self):
        import time
        return time.strftime('%H:%M:%S', time.localtime(time.time()))
    
    def writeFile(self, msg, filePath):
        logFile = open(filePath, 'a')
        logFile.write(msg + "\n")
        logFile.close()
    
    def createDir(self, path):
        import os
        count = 0
        while 1:
            try:
                if count >= 5:
                    return False
                os.makedirs(path)
                if os.path.isdir(path):
                    return True
                count += 1
            except:
                pass
        
    def removeDirFiles(self, dirPath): 
        import os
        for fileName in os.listdir(dirPath): 
            targetFile = os.path.join(dirPath, fileName) 
            if os.path.isfile(targetFile): 
                os.remove(targetFile)
                
    def processExit(self):
        import sys
        sys.exit()
