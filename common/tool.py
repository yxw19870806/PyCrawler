# -*- coding:UTF-8  -*-
'''
Created on 2013-7-16

@author: Administrator
'''

import cookielib
import cStringIO
import os
import platform
import shutil
import sys
import time
import threading
import traceback
import urllib2

IS_SET_TIMEOUT = False
PROCESS_STATUS = 0


class ProcessControl(threading.Thread):
    PROCESS_RUN = 0
    PROCESS_PAUSE = 1   # 进程暂停，知道状态变为0时才继续下载
    PROCESS_STOP = 2    # 进程立刻停止，删除还未完成的数据
    PROCESS_FINISH = 3  # 进程等待现有任务完成后停止

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global PROCESS_STATUS
        while 1:
            if os.path.exists(os.path.join(os.path.abspath(""), "..\\pause")):
                PROCESS_STATUS = self.PROCESS_PAUSE
            elif os.path.exists(os.path.join(os.path.abspath(""), "..\\stop")):
                PROCESS_STATUS = self.PROCESS_STOP
            elif os.path.exists(os.path.join(os.path.abspath(""), "..\\finish")):
                PROCESS_STATUS = self.PROCESS_STOP
            else:
                PROCESS_STATUS = self.PROCESS_RUN
            time.sleep(10)


# 进程是否需要结束
# 返回码 0: 正常运行; 1 立刻结束; 2 等待现有任务完成后结束
def is_process_end():
    global PROCESS_STATUS
    if PROCESS_STATUS == ProcessControl.PROCESS_STOP:
        return 1
    elif PROCESS_STATUS == ProcessControl.PROCESS_FINISH:
        return 2
    return 0


def restore_process_status():
    for file_name in ['pause', 'stop', 'finish']:
        file_path = os.path.join(os.path.abspath(".."), file_name)
        if os.path.exists(file_path):
            os.remove(file_path)


# http请求
# 返回 【返回码，数据, 请求信息】
# 返回码 -1：页面不存在（404）；-2：暂时无法访问页面
def http_request(url, post_data=None):
    global IS_SET_TIMEOUT
    global PROCESS_STATUS
    if url.find("http") == -1:
        return [-100, None, []]
    count = 0
    while 1:
        while PROCESS_STATUS == ProcessControl.PROCESS_PAUSE:
            time.sleep(10)
        try:
            if post_data:
                request = urllib2.Request(url, post_data)
            else:
                request = urllib2.Request(url)
            # 设置头信息
            request.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0")

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

            return [1, response.read(), response.info()]
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
            elif str(e).lower().find("http error 404") != -1:
                return [-1, None, []]
            else:
                print_msg(str(e))
                traceback.print_exc()

        count += 1
        if count > 9999:
            print_error_msg("无法访问页面：" + url)
            return [-2, None, []]


def get_response_info(response, key):
    try:
        if key in response:
            return response[key]
    except:
        pass
    return None


# 根据浏览器和操作系统，自动查找默认浏览器cookie路径(只支持windows)
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def get_default_browser_cookie_path(browser_type):
    if platform.system() != "Windows":
        return  None
    if browser_type == 1:
        return os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Cookies")
    elif browser_type == 2:
        default_browser_path = os.path.join(os.getenv("APPDATA"), "Mozilla\\Firefox\\Profiles")
        for dir_name in os.listdir(default_browser_path):
            if os.path.isdir(os.path.join(default_browser_path, dir_name)):
                if os.path.exists(os.path.join(default_browser_path, dir_name, "cookies.sqlite")):
                    return os.path.join(default_browser_path, dir_name)
    elif browser_type == 3:
        return os.path.join(os.getenv("APPDATA"), "Google\\Chrome\\User Data\\Default")
    print_msg("浏览器类型：" + browser_type + "不存在")
    return None


# 使用系统cookies
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def set_cookie(file_path, browser_type=1):
    if sys.version.find("32 bit") != -1:
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
            cookie_file = open(os.path.join(file_path, cookie_name), "r")
            cookie_info = cookie_file.read()
            cookie_file.close()
            for cookies in cookie_info.split("*"):
                cookie_list = cookies.strip("\n").split("\n")
                if len(cookie_list) >= 8:
                    domain = cookie_list[2].split("/")[0]
                    domain_specified = ftstr[cookie_list[2].startswith(".")]
                    path = cookie_list[2].replace(domain, "")
                    secure = ftstr[0]
                    expires = cookie_list[4]
                    name = cookie_list[0]
                    value = cookie_list[1]
                    s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
    elif browser_type == 2:
        con = sqlite.connect(os.path.join(file_path, "cookies.sqlite"))
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            domain_specified = ftstr[cookie_info[0].startswith(".")]
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
        con = sqlite.connect(os.path.join(file_path, "Cookies"))
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value from cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            domain_specified = ftstr[cookie_info[0].startswith(".")]
            path = cookie_info[1]
            secure = ftstr[cookie_info[2]]
            expires = cookie_info[3]
            name = cookie_info[4]
            value = cookie_info[5]
            s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
    s.seek(0)
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, "", True, True)
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


def trace(msg, is_print=1, log_path=""):
    if is_print == 1:
        msg = get_time() + " " + msg
        print_msg(msg, False)
    if log_path != "":
        write_file(msg, log_path)


def print_error_msg(msg, is_print=1, log_path=""):
    if is_print == 1:
        msg = get_time() + " [Error] " + msg
        print_msg(msg, False)
    if log_path != "":
        if msg.find("HTTP Error 500") != -1:
            return
        if msg.find("urlopen error The read operation timed out") != -1:
            return
        write_file(msg, log_path)


def print_step_msg(msg, is_print=1, log_path=""):
    if is_print == 1:
        msg = get_time() + " " + msg
        print_msg(msg, False)
    if log_path != "":
        write_file(msg, log_path)


def get_time():
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))


# 文件路径编码转换
def change_path_encoding(path):
    try:
        if isinstance(path, unicode):
            path = path.encode("GBK")
        else:
            path = path.decode("UTF-8").encode("GBK")
    except:
        if isinstance(path, unicode):
            path = path.encode("UTF-8")
        else:
            path = path.decode("UTF-8")
    return path


def write_file(msg, file_path):
    log_file = open(file_path, "a")
    log_file.write(msg + "\n")
    log_file.close()


# image_path 包括路径和文件名
def save_image(image_url, image_path):
    image_path = change_path_encoding(image_path)
    [image_return_code, image_byte] = http_request(image_url)[:2]
    if image_return_code == 1:
        image_file = open(image_path, "wb")
        image_file.write(image_byte)
        image_file.close()
        return True
    return False


# order desc 降序
# order asc  升序
# order 其他 不需要排序
def get_dir_files_name(path, order=None):
    path = change_path_encoding(path)
    files_list = os.listdir(path)
    # 升序
    if order == "asc":
        return sorted(files_list, reverse=False)
    # 降序
    elif order == "desc":
        return sorted(files_list, reverse=True)
    else:
        return files_list


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
