# -*- coding:UTF-8  -*-
'''
Created on 2013-7-16

@author: Administrator
'''

import os
import sys
import time

IS_SET_TIMEOUT = False

class Tool(object):

    # http请求
    def doGet(self, url, post_data=None):
        import traceback
        import urllib2
        global IS_SET_TIMEOUT
        if url.find("http") == -1:
            return False
        count = 0
        while 1:
            try:
                if post_data:
                    request = urllib2.Request(url, post_data)
                else:
                    request = urllib2.Request(url)
                # 设置头信息
                request.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0 FirePHP/0.7.2')
                # 设置访问超时
                if sys.version_info < (2, 7):
                    if not IS_SET_TIMEOUT:
                        urllib2.socket.setdefaulttimeout(5)
                        IS_SET_TIMEOUT = True
                    response = urllib2.urlopen(request)
                else:
                    response = urllib2.urlopen(request, timeout=5)
                return response.read()
            except Exception, e:
                # 代理无法访问
                if str(e).find("[Errno 10061]") != -1:
                    input = raw_input("无法访问代理服务器，请检查代理设置。是否需要继续程序？(Y)es or (N)o：").lower()
                    if input in ["y", "yes"]:
                        pass
                    elif input in ["n", "no"]:
                        sys.exit()
                # 连接被关闭，等待1分钟后再尝试
                elif str(e).find("[Errno 10053] ") != -1:
                    self.printMsg("访问页面超时，重新连接请稍后")
                    time.sleep(60)
                # 超时
                elif str(e).find("timed out") != -1:
                    self.printMsg("访问页面超时，重新连接请稍后")
                else:
                    self.printMsg(str(e))
                    traceback.print_exc()
            count += 1
            if count > 50:
                self.printErrorMsg("无法访问页面：" + url)
                return False

    # 根据浏览器和操作系统，自动查找默认浏览器cookie路径
    # os_version=1: win7
    # os_version=2: xp
    # browser_type=1: IE
    # browser_type=2: firefox
    # browser_type=3: chrome
    def getDefaultBrowserCookiePath(self, os_version, browser_type):
        import getpass
        if browser_type == 1:
            if os_version == 1:
                return "C:\\Users\\%s\\AppData\\Roaming\\Microsoft\\Windows\\Cookies\\" % (getpass.getuser())
            elif os_version == 2:
                return "C:\\Documents and Settings\\%s\\Cookies\\" % (getpass.getuser())
        elif browser_type == 2:
            if os_version == 1:
                defaultBrowserPath = "C:\\Users\\%s\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\" % (getpass.getuser())
                for dirName in os.listdir(defaultBrowserPath):
                    if os.path.isdir(defaultBrowserPath + "\\" + dirName):
                        if os.path.exists(defaultBrowserPath + "\\" + dirName + "\\cookies.sqlite"):
                            return defaultBrowserPath + "\\" + dirName + "\\"
            elif os_version == 2:
                defaultBrowserPath = "C:\\Documents and Settings\\%s\\Local Settings\\Application Data\\Mozilla\\Firefox\\Profiles\\" % (getpass.getuser())
                for dirName in os.listdir(defaultBrowserPath):
                    if os.path.isdir(defaultBrowserPath + "\\" + dirName):
                        if os.path.exists(defaultBrowserPath + "\\" + dirName + "\\cookies.sqlite"):
                            return defaultBrowserPath + "\\" + dirName + "\\"                
        elif browser_type == 3:
            if os_version == 1:
                return "C:\\Users\%s\\AppData\\Local\\Google\\Chrome\\User Data\\Default" % (getpass.getuser())
            elif os_version == 2:
                return "C:\\Documents and Settings\\%s\\Local Settings\\Application Data\\Google\\Chrome\\User Data\Default\\" % (getpass.getuser())
        self.printMsg("浏览器类型：" + browser_type + "不存在")
        return None

    # 使用系统cookies
    # browser_type=1: IE
    # browser_type=2: firefox
    # browser_type=3: chrome
    def cookie(self, filePath, browser_type=1):
        import cookielib
        import cStringIO
        import urllib2
        from pysqlite2 import dbapi2 as sqlite
        if not os.path.exists(filePath):
            self.printMsg("cookie目录：" + filePath + " 不存在")
            return False
        ftstr = ["FALSE", "TRUE"]
        s = cStringIO.StringIO()
        s.write("# Netscape HTTP Cookie File\n")
        if browser_type == 1:
            for cookieName in os.listdir(filePath):
                if cookieName.find(".txt") == -1:
                    continue
                cookieFile = open(filePath + "\\" + cookieName, 'r')
                cookieInfo = cookieFile.read()
                cookieFile.close()
                for cookies in cookieInfo.split("*"):
                    cookieList = cookies.strip("\n").split("\n")
                    if len(cookieList) >= 8:
                        domain = cookieList[2].split("/")[0]
                        domainSpecified = ftstr[cookieList[2].startswith('.')]
                        path = cookieList[2].replace(domain, "")
                        secure = ftstr[0]
                        expires = cookieList[4]
                        name = cookieList[0]
                        value = cookieList[1]
                        s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domainSpecified, path, secure, expires, name, value))
        elif browser_type == 2:
            con = sqlite.connect(filePath + "\\cookies.sqlite")
            cur = con.cursor()
            cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
            for cookieInfo in cur.fetchall():
                domain = cookieInfo[0]
                domainSpecified = ftstr[cookieInfo[0].startswith('.')]
                path = cookieInfo[1]
                secure = ftstr[cookieInfo[2]]
                expires = cookieInfo[3]
                name = cookieInfo[4]
                value = cookieInfo[5]
#                 s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domainSpecified, path, secure, expires, name, value))
                try:
                    s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domainSpecified, path, secure, expires, name, value))
                except:
                    pass
        elif browser_type == 3:
            con = sqlite.connect(filePath + "\\Cookies")
            cur = con.cursor()
            cur.execute("select host_key, path, secure, expires_utc, name, value from cookies")
            for cookieInfo in cur.fetchall():
                domain = cookieInfo[0]
                domainSpecified = ftstr[cookieInfo[0].startswith('.')]
                path = cookieInfo[1]
                secure = ftstr[cookieInfo[2]]
                expires = cookieInfo[3]
                name = cookieInfo[4]
                value = cookieInfo[5]
                s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domainSpecified, path, secure, expires, name, value))
        s.seek(0)
        cookieJar = cookielib.MozillaCookieJar()
        cookieJar._really_load(s, '', True, True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
        urllib2.install_opener(opener)
        return True
    
    def proxy(self, ip, port, protocol):
    # 设置代理
        import urllib2
        proxyHandler = urllib2.ProxyHandler({protocol:"http://" + ip + ":" + port})
        opener = urllib2.build_opener(proxyHandler)
        urllib2.install_opener(opener)
        self.printMsg("设置代理成功")

    # 获取配置文件
    # config : 字典格式，如：{key1:value1, key2:value2}
    # mode=0 : 直接赋值
    # mode=1 : 字符串拼接
    # mode=2 : 取整
    # mode=3 : 文件路径，以'\'开头的为当前目录下创建
    # prefix: 前缀，只有在mode=1时有效
    # postfix: 后缀，只有在mode=1时有效
    def getConfig(self, config, key, default_value, mode, prefix=None, postfix=None):
        import traceback
        value = None
        if config.has_key(key):
            if mode == 0:
                value = config[key]
            elif mode == 1:
                value = config[key]
                if prefix is not None:
                    value = prefix + value
                if postfix is not None:
                    value = value + postfix
            elif mode == 2:
                try:
                    value = int(config[key])
                except:
                    self.printMsg("配置文件config.ini中key为'" + key + "'的值必须是一个整数，使用程序默认设置")
                    traceback.print_exc()
                    value = default_value
            elif mode == 3:
                value = config[key]
                if value[0] == "\\":
                    value = os.getcwd() + value
                return value
        else:
            self.printMsg("配置文件config.ini中没有找到key为'" + key + "'的参数，使用程序默认设置")
            value = default_value
        return value

    def analyzeConfig(self, config_path):
        configFile = open(config_path, 'r')
        lines = configFile.readlines()
        configFile.close()
        config = {}
        for line in lines:
            if len(line) == 0:
                continue
            line = line.lstrip().rstrip().replace(" ", "")
            if len(line) > 1 and line[0] != "#" and line.find('=') >= 0:
                try:
                    line = line.split("=")
                    config[line[0]] = line[1]
                except Exception, e:
                    self.printMsg(str(e))
                    pass
        return  config

    def printMsg(self, msg, is_time=True):
        if is_time:
            msg = self.getTime() + " " + msg
        print msg
    
    def trace(self, msg, is_print=1, log_path=''):
        if is_print == 1:
            msg = self.getTime() + " " + msg
#             self.printMsg(msg, False)
        if log_path != '':
            self.writeFile(msg, log_path)
    
    def printErrorMsg(self, msg, is_print=1, log_path=''):
        if is_print == 1:
            msg = self.getTime() + " [Error] " + msg
            self.printMsg(msg, False)
        if log_path != '':
            if msg.find("HTTP Error 500") != -1:
                return
            if msg.find("urlopen error The read operation timed out") != -1:
                return
            self.writeFile(msg, log_path)
    
    def printStepMsg(self, msg, is_print=1, log_path=''):
        if is_print == 1:
            msg = self.getTime() + " " + msg
            self.printMsg(msg, False)
        if log_path != '':
            self.writeFile(msg, log_path)
                
    def getTime(self):
        return time.strftime('%m-%d %H:%M:%S', time.localtime(time.time()))

    # 过滤一些文件夹名不支持的字符串
    def filterPath(self, title):
        # 盘符
        if title[1] == ':':
            title = title[:2] + title[2:].replace(':', '')
        title = title.replace('*', '')
        title = title.replace('?', '')
        title = title.replace('"', '')
        title = title.replace('<', '')
        title = title.replace('>', '')
        title = title.replace('|', '')
        return title

    # 文件路径编码转换
    def changePathEncoding(self, path):
        try:
            if isinstance(path, unicode):
                path = path.encode('GBK')
            else:
                path = path.decode('UTF-8').encode('GBK')
        except:
            if isinstance(path, unicode):
                path = path.encode('UTF-8')
            else:
                path = path.decode('UTF-8')
        return path

    def writeFile(self, msg, file_path):
        logFile = open(file_path, 'a')
        logFile.write(msg + "\n")
        logFile.close()

    # image_path 包括路径和文件名
    def saveImage(self, image_url, image_path):
        image_path = self.filterPath(image_path)
        image_path = self.changePathEncoding(image_path)
        image_byte = self.doGet(image_url)
        if image_byte:
            image_file = open(image_path, "wb")
            image_file.write(image_byte)
            image_file.close()
            return True
        return False

    # 删除目录下所有文件（保留目录）
    def removeDirFiles(self, dir_path):
        dir_path = self.changePathEncoding(dir_path)
        for fileName in os.listdir(dir_path):
            target_file = os.path.join(dir_path, fileName)
            if os.path.isfile(target_file):
                os.remove(target_file)

    # 创建目录
    # create_mode 0 : 不存在则创建
    # create_mode 1 : 存在则删除并创建
    # create_mode 2 : 存在提示删除，确定后删除创建，取消后退出程序
    def makeDir(self, dir_path, create_mode):
        import shutil
        dir_path = self.filterPath(dir_path)
        dir_path = self.changePathEncoding(dir_path)
        if create_mode != 0 and create_mode != 1 and create_mode != 2:
            create_mode = 0
        # 目录存在
        if os.path.exists(dir_path):
            if create_mode == 0:
                if os.path.isdir(dir_path):
                    return True
                else:
                    return False
            elif create_mode == 1:
                pass
            elif create_mode == 2:
                # 路径是空目录
                if os.path.isdir(dir_path) and not os.listdir(dir_path):
                    pass
                else:
                    isDelete = False
                    while not isDelete:
                        input = raw_input(self.getTime() + " 目录：" + dir_path + " 已存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                        try:
                            input = input.lower()
                            if input in ["y", "yes"]:
                                isDelete = True
                            elif input in ["n", "no"]:
                                self.processExit()
                        except Exception, e:
                            self.printErrorMsg(str(e))
                            pass

            # 删除原本路劲
            # 文件
            if os.path.isfile(dir_path):
                os.remove(dir_path)
            # 目录
            elif os.path.isdir(dir_path):
                # 非空目录
                if os.listdir(dir_path):
                    shutil.rmtree(dir_path, True)
                    # 保护，防止文件过多删除时间过长，5秒检查一次文件夹是否已经删除
                    while os.path.exists(dir_path):
                        shutil.rmtree(dir_path, True)
                        time.sleep(5)
                else:
                    return  True
        count = 0
        while count <= 5:
            try:
                os.makedirs(dir_path)
                if os.path.isdir(dir_path):
                    return True
            except Exception, e:
                self.printMsg(str(e))
                time.sleep(5)
            count += 1
        return False

    def copyFiles(self, source_path, dest_path):
        import shutil
        source_path = self.changePathEncoding(source_path)
        dest_path = self.changePathEncoding(dest_path)
        shutil.copyfile(source_path, dest_path)

    # 结束进程
    def processExit(self):
        sys.exit()

    # 关机
    def shutdown(self, widget, data=None):
        os.system("shutdown -h now")
