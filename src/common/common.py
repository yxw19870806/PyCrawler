# -*- coding:utf-8  -*-
'''
Created on 2013-7-16

@author: Administrator
'''

IS_SET_TIMEOUT = False

# http请求
def doGet(url):
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
                print "time out, try again"
            else:
                print e
                traceback.print_exc()
        count += 1
        if count > 10:
            print "can not connection " + url
            return False

# 使用系统cookies
def cookie(filePath):
    import cookielib
    import cStringIO
    import os
    import sys
    import urllib2
    from pysqlite2 import dbapi2 as sqlite
    if not os.path.exists(filePath):
        print filePath + " not exist"
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

def proxy(ip, port):
    import urllib2
    proxyHandler = urllib2.ProxyHandler({'https':"http://" + ip + ":" + port})
    opener = urllib2.build_opener(proxyHandler)
    urllib2.install_opener(opener)
    print "proxy set succeed"
            
# 获取配置文件
# config : 字典格式，如：{key1:value1, key2:value2}
# mode 0 : 直接赋值
# mode 1 : 字符串拼接
# mode 2 : 取整
# prefix: 前缀，只有在mode=1时有效
# postfix: 后缀，只有在mode=1时有效
def getConfig(config, key, defaultValue, mode, prefix=None, postfix=None):
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
                print "'" + key + "' must is a number in config.ini, default value"
                value = defaultValue
    else:
        print "Not found '" + key + "' in config.ini, default value"
        value = defaultValue
    return value

def getTime():
    import time
    return time.strftime('%H:%M:%S', time.localtime(time.time()))

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
