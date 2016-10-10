# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""

import cookielib
import cStringIO
import mimetools
import os
import platform
import random
import shutil
import sys
import time
import threading
import traceback
import urllib
import urllib2

IS_SET_TIMEOUT = False
PROCESS_STATUS = 0

IS_EXECUTABLE = False
if getattr(sys, 'frozen', False):
    IS_EXECUTABLE = True


# 进程监控
class ProcessControl(threading.Thread):
    PROCESS_RUN = 0
    PROCESS_PAUSE = 1   # 进程暂停，知道状态变为0时才继续下载
    PROCESS_STOP = 2    # 进程立刻停止，删除还未完成的数据
    PROCESS_FINISH = 3  # 进程等待现有任务完成后停止

    def __init__(self):
        threading.Thread.__init__(self)
        for file_name in ["pause", "stop", "finish"]:
            file_path = os.path.join(os.path.abspath(".."), file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

    def run(self):
        global PROCESS_STATUS
        while True:
            if os.path.exists(os.path.join(os.path.abspath(""), "..\\pause")):
                PROCESS_STATUS = self.PROCESS_PAUSE
            elif os.path.exists(os.path.join(os.path.abspath(""), "..\\stop")):
                PROCESS_STATUS = self.PROCESS_STOP
            elif os.path.exists(os.path.join(os.path.abspath(""), "..\\finish")):
                PROCESS_STATUS = self.PROCESS_FINISH
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


# http请求
# 返回 【返回码，数据, response】
# 返回码 1：正常返回；-1：无法访问；-100：URL格式不正确；其他< 0：网页返回码
def http_request(url, post_data=None, cookie=None):
    global IS_SET_TIMEOUT
    global PROCESS_STATUS
    if not (url.find("http://") == 0 or url.find("https://") == 0):
        return -100, None, None
    count = 0
    while True:
        while PROCESS_STATUS == ProcessControl.PROCESS_PAUSE:
            time.sleep(10)
        if PROCESS_STATUS == ProcessControl.PROCESS_STOP:
            process_exit(0)
        try:
            if post_data:
                if isinstance(post_data, dict):
                    post_data = urllib.urlencode(post_data)
                request = urllib2.Request(url, post_data)
            else:
                request = urllib2.Request(url)
            # 设置头信息
            request.add_header("User-Agent", random_user_agent())

            # cookies
            if isinstance(cookie, cookielib.CookieJar):
                opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
                urllib2.install_opener(opener)

            # 设置访问超时
            if sys.version_info < (2, 7):
                if not IS_SET_TIMEOUT:
                    urllib2.socket.setdefaulttimeout(5)
                    IS_SET_TIMEOUT = True
                response = urllib2.urlopen(request)
            else:
                response = urllib2.urlopen(request, timeout=5)

            if response:
                return 1, response.read(), response
        except Exception, e:
            # 代理无法访问
            if str(e).find("[Errno 10061]") != -1:
                # 判断是否设置了代理
                if urllib2._opener.handlers is not None:
                    for handler in urllib2._opener.handlers:
                        if isinstance(handler, urllib2.ProxyHandler):
                            input_str = raw_input("无法访问代理服务器，请检查代理设置。是否需要继续程序？(Y)es or (N)o：").lower()
                            if input_str in ["y", "yes"]:
                                pass
                            elif input_str in ["n", "no"]:
                                sys.exit()
                            break
            # 连接被关闭，等待1分钟后再尝试
            elif str(e).find("[Errno 10053] ") != -1:
                print_msg("访问页面超时，重新连接请稍后")
                time.sleep(30)
            # 超时
            elif str(e).find("timed out") != -1:
                print_msg("访问页面超时，重新连接请稍后")
            # 400
            elif str(e).lower().find("http error 400") != -1:
                return -400, None, None
            # 403
            elif str(e).lower().find("http error 403") != -1:
                return -403, None, None
            # 404
            elif str(e).lower().find("http error 404") != -1:
                return -404, None, None
            else:
                print_msg(url)
                print_msg(str(e))
                traceback.print_exc()

        count += 1
        if count > 500:
            print_msg("无法访问页面：" + url)
            return -1, None, None


# 随机生成一个合法的user agent
def random_user_agent():
    # "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0"
    # "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    firefox_version_max = 46
    chrome_version_list = ["40.0.2214", "41.0.2272", "42.0.2311", "43.0.2357", "44.0.2403",
                           "45.0.2454", "46.0.2490", "47.0.2526", "48.0.2564", "49.0.2623",
                           "50.0.2661", "51.0.2704", "52.0.2743", "53.0.2785", "54.0.2810"]
    windows_version_list = ["6.1", "6.3", "10.0"]
    browser_type = random.choice(["firefox", "chrome"])
    os_type = random.choice(windows_version_list)
    if browser_type == "firefox":
        firefox_version = random.randint(firefox_version_max - 10, firefox_version_max)
        return "Mozilla/5.0 (Windows NT %s; WOW64; rv:%s.0) Gecko/20100101 Firefox/%s.0" \
               % (os_type, firefox_version, firefox_version)
    elif browser_type == "chrome":
        sub_version = random.randint(1, 100)
        chrome_version = random.choice(chrome_version_list)
        return "Mozilla/5.0 (Windows NT %s; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s.%s Safari/537.36" \
               % (os_type, chrome_version, sub_version)
    return ""


# 获取请求response中的指定信息
def get_response_info(response_info, key):
    if isinstance(response_info, mimetools.Message):
        if key in response_info:
            return response_info[key]
    return None


# 根据浏览器和操作系统，自动查找默认浏览器cookie路径(只支持windows)
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def get_default_browser_cookie_path(browser_type):
    if platform.system() != "Windows":
        return None
    if browser_type == 1:
        return os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Cookies")
    elif browser_type == 2:
        default_browser_path = os.path.join(os.getenv("APPDATA"), "Mozilla\\Firefox\\Profiles")
        for dir_name in os.listdir(default_browser_path):
            if os.path.isdir(os.path.join(default_browser_path, dir_name)):
                if os.path.exists(os.path.join(default_browser_path, dir_name, "cookies.sqlite")):
                    return os.path.join(default_browser_path, dir_name)
    elif browser_type == 3:
        return os.path.join(os.getenv("LOCALAPPDATA"), "Google\\Chrome\\User Data\\Default")
    print_msg("浏览器类型：" + browser_type + "不存在")
    return None


# 根据key和value创建一个cookie
def create_cookie(name, value, domain="", path="/"):
    return cookielib.Cookie(version=0, name=name, value=value, port=None, port_specified=False, domain=domain,
                            domain_specified=False, domain_initial_dot=False, path=path, path_specified=True,
                            secure=False, expires=None, discard=True, comment=None, comment_url=None,
                            rest={"HttpOnly": None}, rfc2109=False)


# 使用系统cookies
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def set_cookie(file_path, browser_type=1, target_domains=""):
    # 有些DB文件开启了WAL功能（SQL3.7引入，Python2.7的sqlite3的版本是3.6，所以需要pysqlite2.8）
    # import sqlite3
    from pysqlite2 import dbapi2 as sqlite
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
                if len(cookie_list) < 8:
                    continue
                domain = cookie_list[2].split("/")[0]
                if _filter_domain(domain, target_domains):
                    continue
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
            if _filter_domain(domain, target_domains):
                continue
            domain_specified = ftstr[cookie_info[0].startswith(".")]
            path = cookie_info[1]
            secure = ftstr[cookie_info[2]]
            expires = cookie_info[3]
            name = cookie_info[4]
            value = cookie_info[5]
            try:
                s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
            except:
                pass
    elif browser_type == 3:
        try:
            import win32crypt
        except:
            return False
        con = sqlite.connect(os.path.join(file_path, "Cookies"))
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value, encrypted_value from cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if _filter_domain(domain, target_domains):
                continue
            domain_specified = ftstr[cookie_info[0].startswith(".")]
            path = cookie_info[1]
            secure = ftstr[cookie_info[2]]
            expires = cookie_info[3]
            name = cookie_info[4]
            value = cookie_info[5]
            try:
                value = win32crypt.CryptUnprotectData(cookie_info[6], None, None, None, 0)[1]
            except:
                pass
            try:
                s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
            except:
                pass
    s.seek(0)
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, "", True, True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    return True


# 是否需要过滤这个域的cookie
# return True - 过滤，不需要加载
# return False - 不过滤，需要加载
def _filter_domain(domain, target_domains):
    if target_domains:
        if isinstance(target_domains, str):
            if domain.find(target_domains) > 0:
                return False
        else:
            for target_domain in target_domains:
                if domain.find(target_domain) >= 0:
                    return False
        return True
    else:
        return False


# 设置代理
def set_proxy(ip, port):
    proxy_address = "http://%s:%s" % (ip, port)
    proxy_handler = urllib2.ProxyHandler({"http": proxy_address, "https": proxy_address})
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)
    print_msg("设置代理成功")


# 快速设置cookie和代理
# is_set_cookie     0:不设置, 1:设置
# proxy_type        0:不设置, 1:http, 2:https
def quickly_set(is_set_cookie, proxy_type):
    import robot
    config = robot.read_config(os.path.join(os.getcwd(), "..\\common\\config.ini"))
    if is_set_cookie == 1:
        # 操作系统&浏览器
        browser_type = robot.get_config(config, "BROWSER_VERSION", 2, 1)
        # cookie
        is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
        if is_auto_get_cookie:
            cookie_path = robot.tool.get_default_browser_cookie_path(browser_type)
        else:
            cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
        set_cookie(cookie_path, browser_type)
    if proxy_type == 1:
        proxy_ip = robot.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        proxy_port = robot.get_config(config, "PROXY_PORT", "8087", 0)
        set_proxy(proxy_ip, proxy_port)


# 控制台输出
def print_msg(msg, is_time=True):
    if is_time:
        msg = get_time() + " " + msg
    if IS_EXECUTABLE:
        print msg.decode("utf-8").encode("GBK")
    else:
        print msg


# 获取时间
def get_time():
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))


# http请求返回的时间字符串转换为时间戳
def response_time_to_timestamp(time_string):
    last_modified_time = time.strptime(time_string, "%a, %d %b %Y %H:%M:%S %Z")
    return int(time.mktime(last_modified_time)) - time.timezone


def find_sub_string(string, start_string, end_string, include_string=0):
    # 根据开始与结束的字符串，截取字符串
    # include_string是否包含查询条件的字符串，0 都不包含, 1 只包含start_string, 2 只包含end_string, 3 包含start_string和end_string
    # 参数验证
    string = str(string)
    if start_string is not None:
        start_string = str(start_string)
    if end_string is not None:
        end_string = str(end_string)
    include_string = int(include_string)
    if 0 < include_string > 3:
        include_string = 3

    if start_string is None:
        start_index = 0
    else:
        start_index = string.find(start_string)
    if start_index >= 0:
        if include_string & 1 == 0:
            start_index += len(start_string)
        if end_string is None:
            stop_index = len(string)
        else:
            stop_index = string.find(end_string, start_index)
        if stop_index >= 0:
            if include_string & 2 == 2:
                stop_index += len(end_string)
            return string[start_index:stop_index]
    return ""


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


# 写文件
# type=1: 追加
# type=2: 覆盖
def write_file(msg, file_path, append_type=1):
    if append_type == 1:
        file_handle = open(file_path, "a")
    else:
        file_handle = open(file_path, "w")
    file_handle.write(msg + "\n")
    file_handle.close()


# 保存网络文件
# file_path 包括路径和文件名
def save_net_file(file_url, file_path):
    file_path = change_path_encoding(file_path)
    page_return_code, page_data = http_request(file_url)[:2]
    if page_return_code == 1:
        file_handle = open(file_path, "wb")
        file_handle.write(page_data)
        file_handle.close()
        return True
    return False


# 按照指定连接符合并二维数组生成字符串
def list_to_string(source_lists, first_sign="\n", second_sign="\t"):
    temp_list = []
    for value in source_lists:
        if second_sign != "":
            temp_list.append(second_sign.join(map(str, value)))
        else:
            temp_list.append(str(value))
    return first_sign.join(temp_list)


# 获取指定目录的文件列表
# order desc 降序
# order asc  升序
# order 其他 不需要排序
def get_dir_files_name(path, order=None):
    path = change_path_encoding(path)
    if not os.path.exists(path):
        return []
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
    if not os.path.exists(dir_path):
        return True
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
                    input_str = input_str.lower()
                    if input_str in ["y", "yes"]:
                        is_delete = True
                    elif input_str in ["n", "no"]:
                        process_exit()

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


# 复制文件
def copy_files(source_path, destination_path):
    source_path = change_path_encoding(source_path)
    destination_path = change_path_encoding(destination_path)
    shutil.copyfile(source_path, destination_path)


# 生成指定长度的随机字符串
# char_lib_type 需要的字库取和， 1 - 大写字母；2 - 小写字母; 4 - 数字，默认7(1+2+4)包括全部
def generate_random_string(string_length, char_lib_type=7):
    result = ""
    char_lib = {
        1: "abcdefghijklmnopqrstuvwxyz",  # 小写字母
        2: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",  # 大写字母
        4: "0123456789",  # 数字
    }
    random_string = ""
    for i in char_lib:
        if char_lib_type & i == i:
            for char in char_lib[i]:
                random_string += char

    if not random_string:
        return result

    length = len(random_string) - 1
    for i in range(0, string_length):
        result += random_string[random.randint(0, length)]

    return result


# 结束进程
# exit_code 0: 正常结束, 1: 异常退出
def process_exit(exit_code=1):
    sys.exit(exit_code)


# 定时关机
def shutdown(delay_time=30):
    if platform.system() == "Windows":
        os.system("shutdown -s -f -t " + str(delay_time))
    else:
        os.system("halt")
