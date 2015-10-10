# -*- coding:UTF-8  -*-
'''
Created on 2013-7-16

@author: Administrator
'''

import cookielib
import cStringIO
import getpass
import os
import shutil
import sys
import time
import traceback
import urllib2

IS_SET_TIMEOUT = False


class Robot(object):

    def __init__(self):

        config = self.analyze_config(os.getcwd() + "\\..\\common\\config.ini")

        # 日志
        self.is_log = self.get_config(config, "IS_LOG", 1, 2)
        self.is_show_error = self.get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.is_trace = self.get_config(config, "IS_TRACE", 1, 2)
        self.is_show_step = self.get_config(config, "IS_SHOW_STEP", 1, 2)
        if self.is_log == 0:
            self.trace_log_path = ""
            self.step_log_path = ""
        else:
            self.trace_log_path = self.get_config(config, "TRACE_LOG_FILE_NAME", "\\log\\traceLog.txt", 3)
            self.step_log_path = self.get_config(config, "STEP_LOG_FILE_NAME", "\\log\\stepLog.txt", 3)
            # 日志文件保存目录
            step_log_dir = os.path.dirname(self.step_log_path)
            if not make_dir(step_log_dir, 0):
                print_error_msg("创建步骤日志目录：" + step_log_dir + " 失败，程序结束！", self.is_show_step, self.step_log_path)
                process_exit()
            trace_log_dir = os.path.dirname(self.trace_log_path)
            if not make_dir(trace_log_dir, 0):
                print_error_msg("创建调试日志目录：" + trace_log_dir + " 失败，程序结束！", self.is_show_step, self.trace_log_path)
                process_exit()
        self.error_log_path = self.get_config(config, "ERROR_LOG_FILE_NAME", "\\log\\errorLog.txt", 3)
        error_log_dir = os.path.dirname(self.error_log_path)
        if not make_dir(error_log_dir, 0):
            print_error_msg("创建错误日志目录：" + error_log_dir + " 失败，程序结束！", self.is_show_error, self.error_log_path)
            process_exit()

        # 存档
        self.image_download_path = self.get_config(config, "IMAGE_DOWNLOAD_DIR_NAME", "\\photo", 3)
        self.image_temp_path = self.get_config(config, "IMAGE_TEMP_DIR_NAME", "\\tempImage", 3)

        self.is_sort = self.get_config(config, "IS_SORT", 1, 2)
        self.get_image_count = self.get_config(config, "GET_IMAGE_COUNT", 0, 2)

        self.user_id_list_file_path = self.get_config(config, "USER_ID_LIST_FILE_NAME", "\\info\\idlist.txt", 3)

        # 代理
        self.is_proxy = self.get_config(config, "IS_PROXY", 2, 2)
        self.proxy_ip = self.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxy_port = self.get_config(config, "PROXY_PORT", "8087", 0)

        # 操作系统&浏览器
        self.browser_version = self.get_config(config, "BROWSER_VERSION", 2, 2)

        # cookie
        is_auto_get_cookie = self.get_config(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if is_auto_get_cookie == 0:
            self.cookie_path = self.get_config(config, "COOKIE_PATH", "", 0)
        else:
            os_version = self.get_config(config, "OS_VERSION", 1, 2)
            self.cookie_path = get_default_browser_cookie_path(os_version, self.browser_version)

        # 线程数
        self.thread_count = self.get_config(config, "THREAD_COUNT", 10, 2)

    # 获取配置文件
    # config : 字典格式，如：{key1:value1, key2:value2}
    # mode=0 : 直接赋值
    # mode=1 : 字符串拼接
    # mode=2 : 取整
    # mode=3 : 文件路径，以'\'开头的为当前目录下创建
    # prefix: 前缀，只有在mode=1时有效
    # postfix: 后缀，只有在mode=1时有效
    def get_config(self, config, key, default_value, mode, prefix=None, postfix=None):
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
                    print_msg("配置文件config.ini中key为'" + key + "'的值必须是一个整数，使用程序默认设置")
                    traceback.print_exc()
                    value = default_value
            elif mode == 3:
                value = config[key]
                if value[0] == "\\":
                    value = os.getcwd() + value
        else:
            print_msg("配置文件config.ini中没有找到key为'" + key + "'的参数，使用程序默认设置")
            value = default_value
        return value

    def analyze_config(self, config_path):
        config_file = open(config_path, 'r')
        lines = config_file.readlines()
        config_file.close()
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
                    print_msg(str(e))
                    pass
        return config


# http请求
def do_get(url, post_data=None):
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

            # cookie
            # cookie = cookielib.CookieJar()
            # opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
            # urllib2.install_opener(opener)

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
                input_str = raw_input("无法访问代理服务器，请检查代理设置。是否需要继续程序？(Y)es or (N)o：").lower()
                if input_str in ["y", "yes"]:
                    pass
                elif input_str in ["n", "no"]:
                    sys.exit()
            # 连接被关闭，等待1分钟后再尝试
            elif str(e).find("[Errno 10053] ") != -1:
                print_msg("访问页面超时，重新连接请稍后")
                time.sleep(30)
            # 超时
            elif str(e).find("timed out") != -1:
                print_msg("访问页面超时，重新连接请稍后")
            # 404
            elif str(e).find("HTTP Error 404: Not Found") != -1:
                count += 100
            else:
                print_msg(str(e))
                traceback.print_exc()
        count += 1
        if count > 20:
            print_error_msg("无法访问页面：" + url)
            return False


# 根据浏览器和操作系统，自动查找默认浏览器cookie路径
# os_version=1: win7
# os_version=2: xp
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def get_default_browser_cookie_path(os_version, browser_type):
    if browser_type == 1:
        if os_version == 1:
            return "C:\\Users\\%s\\AppData\\Roaming\\Microsoft\\Windows\\Cookies\\" % (getpass.getuser())
        elif os_version == 2:
            return "C:\\Documents and Settings\\%s\\Cookies\\" % (getpass.getuser())
    elif browser_type == 2:
        if os_version == 1:
            default_browser_path = "C:\\Users\\%s\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\" % (getpass.getuser())
            for dir_name in os.listdir(default_browser_path):
                if os.path.isdir(default_browser_path + "\\" + dir_name):
                    if os.path.exists(default_browser_path + "\\" + dir_name + "\\cookies.sqlite"):
                        return default_browser_path + "\\" + dir_name + "\\"
        elif os_version == 2:
            default_browser_path = "C:\\Documents and Settings\\%s\\Local Settings\\Application Data\\Mozilla\\Firefox\\Profiles\\" % (getpass.getuser())
            for dir_name in os.listdir(default_browser_path):
                if os.path.isdir(default_browser_path + "\\" + dir_name):
                    if os.path.exists(default_browser_path + "\\" + dir_name + "\\cookies.sqlite"):
                        return default_browser_path + "\\" + dir_name + "\\"
    elif browser_type == 3:
        if os_version == 1:
            return "C:\\Users\%s\\AppData\\Local\\Google\\Chrome\\User Data\\Default" % (getpass.getuser())
        elif os_version == 2:
            return "C:\\Documents and Settings\\%s\\Local Settings\\Application Data\\Google\\Chrome\\User Data\Default\\" % (getpass.getuser())
    print_msg("浏览器类型：" + browser_type + "不存在")
    return None


# 使用系统cookies
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def set_cookie(file_path, browser_type=1):
    if sys.version.find('32 bit') != -1:
        from pysqlite2_win32 import dbapi2 as sqlite
    else:
        from pysqlite2_win64 import dbapi2 as sqlite
    if not os.path.exists(file_path):
        print_msg("cookie目录：" + file_path + " 不存在")
        return False
    ftstr = ["FALSE", "TRUE"]
    s = cStringIO.StringIO()
    s.write("# Netscape HTTP Cookie File\n")
    if browser_type == 1:
        for cookie_name in os.listdir(file_path):
            if cookie_name.find(".txt") == -1:
                continue
            cookie_file = open(file_path + "\\" + cookie_name, 'r')
            cookie_info = cookie_file.read()
            cookie_file.close()
            for cookies in cookie_info.split("*"):
                cookie_list = cookies.strip("\n").split("\n")
                if len(cookie_list) >= 8:
                    domain = cookie_list[2].split("/")[0]
                    domain_specified = ftstr[cookie_list[2].startswith('.')]
                    path = cookie_list[2].replace(domain, "")
                    secure = ftstr[0]
                    expires = cookie_list[4]
                    name = cookie_list[0]
                    value = cookie_list[1]
                    s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
    elif browser_type == 2:
        con = sqlite.connect(file_path + "\\cookies.sqlite")
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            domain_specified = ftstr[cookie_info[0].startswith('.')]
            path = cookie_info[1]
            secure = ftstr[cookie_info[2]]
            expires = cookie_info[3]
            name = cookie_info[4]
            value = cookie_info[5]
            #s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
            try:
                s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
            except:
                pass
    elif browser_type == 3:
        con = sqlite.connect(file_path + "\\Cookies")
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value from cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            domain_specified = ftstr[cookie_info[0].startswith('.')]
            path = cookie_info[1]
            secure = ftstr[cookie_info[2]]
            expires = cookie_info[3]
            name = cookie_info[4]
            value = cookie_info[5]
            s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
    s.seek(0)
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, '', True, True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    return True


# 设置代理
def set_proxy(ip, port, protocol):
    proxy_handler = urllib2.ProxyHandler({protocol:"http://" + ip + ":" + port})
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)
    print_msg("设置代理成功")


def print_msg(msg, is_time=True):
    if is_time:
        msg = get_time() + " " + msg
    print msg


def trace(msg, is_print=1, log_path=''):
    if is_print == 1:
        msg = get_time() + " " + msg
        print_msg(msg, False)
    if log_path != '':
        write_file(msg, log_path)


def print_error_msg(msg, is_print=1, log_path=''):
    if is_print == 1:
        msg = get_time() + " [Error] " + msg
        print_msg(msg, False)
    if log_path != '':
        if msg.find("HTTP Error 500") != -1:
            return
        if msg.find("urlopen error The read operation timed out") != -1:
            return
        write_file(msg, log_path)


def print_step_msg(msg, is_print=1, log_path=''):
    if is_print == 1:
        msg = get_time() + " " + msg
        print_msg(msg, False)
    if log_path != '':
        write_file(msg, log_path)


def get_time():
    return time.strftime('%m-%d %H:%M:%S', time.localtime(time.time()))


# 文件路径编码转换
def change_path_encoding(path):
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


def write_file(msg, file_path):
    log_file = open(file_path, 'a')
    log_file.write(msg + "\n")
    log_file.close()


# image_path 包括路径和文件名
def save_image(image_url, image_path):
    image_path = change_path_encoding(image_path)
    image_byte = do_get(image_url)
    if image_byte:
        image_file = open(image_path, "wb")
        image_file.write(image_byte)
        image_file.close()
        return True
    return False


# 删除目录下所有文件
# only_files 是否仅仅删除目录下文件而保留目录
def remove_dir(dir_path, only_files=False):
    dir_path = change_path_encoding(dir_path)
    if only_files:
        for file_name in os.listdir(dir_path):
            target_file = os.path.join(dir_path, file_name)
            if os.path.isfile(target_file):
                os.remove(target_file)
    else:
        shutil.rmtree(dir_path, True)


# 创建目录
# create_mode 0 : 不存在则创建
# create_mode 1 : 存在则删除并创建
# create_mode 2 : 存在提示删除，确定后删除创建，取消后退出程序
def make_dir(dir_path, create_mode):
    dir_path = change_path_encoding(dir_path)
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
                is_delete = False
                while not is_delete:
                    input_str = raw_input(get_time() + " 目录：" + dir_path + " 已存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
                    try:
                        input_str = input_str.lower()
                        if input_str in ["y", "yes"]:
                            is_delete = True
                        elif input_str in ["n", "no"]:
                            process_exit()
                    except Exception, e:
                        print_error_msg(str(e))
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
                return True
    count = 0
    while count <= 5:
        try:
            os.makedirs(dir_path)
            if os.path.isdir(dir_path):
                return True
        except Exception, e:
            print_msg(str(e))
            time.sleep(5)
        count += 1
    return False


def copy_files(source_path, destination_path):
    source_path = change_path_encoding(source_path)
    destination_path = change_path_encoding(destination_path)
    shutil.copyfile(source_path, destination_path)


# 结束进程
def process_exit():
    sys.exit()

