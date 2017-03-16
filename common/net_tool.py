# -*- coding:UTF-8  -*-
"""
暂存已废弃的urllib2相关的http请求方法
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import net, process, tool
import cookielib
import cStringIO
import mimetools
import os
import platform
import sqlite3
import sys
import time
import traceback
import urllib
import urllib2
if platform.system() == "Windows":
    import win32crypt


# 保存网络文件
# file_url 文件所在网址
# file_path 文件所在本地路径，包括路径和文件名
# need_content_type 是否需要读取response中的Content-Type作为后缀名，会自动替换file_path中的后缀名
def save_net_file(file_url, file_path, need_content_type=False):
    file_path = tool.change_path_encoding(file_path)
    create_file = False
    for i in range(0, 5):
        page_return_code, page_data, page_response = http_request(file_url)
        if page_return_code == 1:
            # response中的Content-Type作为文件后缀名
            if need_content_type:
                content_type = get_response_info(page_response.info(), "Content-Type")
                if content_type and content_type != "octet-stream":
                    file_path = os.path.splitext(file_path)[0] + "." + content_type.split("/")[-1]
            # 下载
            create_file = True
            file_handle = open(file_path, "wb")
            file_handle.write(page_data)
            file_handle.close()
            # 判断文件下载后的大小和response中的Content-Length是否一致
            content_length = get_response_info(page_response.info(), "Content-Length")
            file_size = os.path.getsize(file_path)
            if (content_length is None) or (int(content_length) == file_size):
                return True
            else:
                tool.print_msg("本地文件%s: %s和网络文件%s:%s不一致" % (file_path, content_length, file_url, file_size))
        elif page_return_code < 0:
            if create_file:
                os.remove(file_path)
            return False
    if create_file:
        os.remove(file_path)
    return False


# http请求
# header_list   http header信息，e.g. {"Host":“www.example.com"}
# is_random_ip  是否使用伪造IP
# 返回 【返回码，数据, response】
# 返回码 1：正常返回；-1：无法访问；-100：URL格式不正确；其他< 0：网页返回码
def http_request(url, post_data=None, header_list=None, is_random_ip=True):
    if not (url.find("http://") == 0 or url.find("https://") == 0):
        return -100, None, None
    count = 0
    while True:
        while process.PROCESS_STATUS == process.PROCESS_STATUS_PAUSE:
            time.sleep(10)
        if process.PROCESS_STATUS == process.PROCESS_STATUS_STOP:
            tool.process_exit(0)
        try:
            if post_data:
                if isinstance(post_data, dict):
                    post_data = urllib.urlencode(post_data)
                request = urllib2.Request(url, post_data)
            else:
                request = urllib2.Request(url)

            # 设置User-Agent
            request.add_header("User-Agent", net._random_user_agent())

            # 设置一个随机IP
            if is_random_ip:
                random_ip = net._random_ip_address()
                request.add_header("X-Forwarded-For", random_ip)
                request.add_header("x-Real-Ip", random_ip)

            # 自定义header
            if isinstance(header_list, dict):
                for header_name, header_value in header_list.iteritems():
                    request.add_header(header_name, header_value)

            # 设置访问超时
            response = urllib2.urlopen(request, timeout=net.HTTP_CONNECTION_TIMEOUT)

            if response:
                return 1, response.read(), response
        except Exception, e:
            # Connection refused（代理无法访问）
            if str(e).find("[Errno 10061]") != -1:
                # 判断是否设置了代理
                if urllib2._opener.handlers is not None:
                    for handler in urllib2._opener.handlers:
                        if isinstance(handler, urllib2.ProxyHandler):
                            notice = "无法访问代理服务器，请检查代理设置。检查完成后输入[(C)ontinue]继续程序或者[(S)top]退出程序："
                            input_str = tool.console_input(notice).lower()
                            if input_str in ["c", "continue"]:
                                pass
                            elif input_str in ["s", "stop"]:
                                sys.exit()
                            break
            # 10053 Software caused connection abort
            # 10054 Connection reset by peer
            elif str(e).find("[Errno 10053] ") != -1 or str(e).find("[Errno 10054] ") != -1 or \
                    str(e).find("HTTP Error 502: Server dropped connection") != -1:
                tool.print_msg(str(e))
                tool.print_msg(url + " 访问超时，稍后重试")
                time.sleep(30)
            # 超时
            elif str(e).find("timed out") != -1 or str(e).find("urlopen error EOF occurred in violation of protocol") != -1:
                tool.print_msg(str(e))
                tool.print_msg(url + " 访问超时，稍后重试")
                time.sleep(10)
            # 400
            elif str(e).lower().find("http error 400") != -1:
                return -400, None, None
            # 403
            elif str(e).lower().find("http error 403") != -1:
                return -403, None, None
            # 404
            elif str(e).lower().find("http error 404") != -1:
                return -404, None, None
            # 500
            elif str(e).lower().find("http error 500") != -1:
                return -500, None, None
            else:
                tool.print_msg(url)
                tool.print_msg(str(e))
                traceback.print_exc()

        count += 1
        if count > net.HTTP_REQUEST_RETRY_COUNT:
            tool.print_msg("无法访问页面：" + url)
            return -1, None, None


# 获取请求response中的指定信息
def get_response_info(response_info, key):
    if isinstance(response_info, mimetools.Message):
        if key in response_info:
            return response_info[key]
    return None


# 加载在浏览器中已经保存了的cookies
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def set_cookie_from_browser(file_path, browser_type, target_domains=""):
    if not os.path.exists(file_path):
        tool.print_msg("cookie目录：" + file_path + " 不存在")
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
                if __filter_domain(domain, target_domains):
                    continue
                domain_specified = ftstr[cookie_list[2].startswith(".")]
                path = cookie_list[2].replace(domain, "")
                secure = ftstr[0]
                expires = cookie_list[4]
                name = cookie_list[0]
                value = cookie_list[1]
                s.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (domain, domain_specified, path, secure, expires, name, value))
    elif browser_type == 2:
        # DB文件开启了WAL功能（SQL3.7引入，旧版本Python2.7.5的sqlite3的版本是3.6，可能无法访问，需要升级python版本）
        con = sqlite3.connect(os.path.join(file_path, "cookies.sqlite"))
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if __filter_domain(domain, target_domains):
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
        if platform.system() != "Windows":
            return None
        con = sqlite3.connect(os.path.join(file_path, "Cookies"))
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value, encrypted_value from cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if __filter_domain(domain, target_domains):
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
    else:
        tool.print_msg("不支持的浏览器类型：" + browser_type)
        return False
    s.seek(0)
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, "", True, True)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
    return True


# 设置代理
def set_proxy(ip, port):
    proxy_address = "http://%s:%s" % (ip, port)
    proxy_handler = urllib2.ProxyHandler({"http": proxy_address, "https": proxy_address})
    opener = urllib2.build_opener(proxy_handler)
    urllib2.install_opener(opener)
    tool.print_msg("设置代理成功")


# 是否需要过滤这个域的cookie
# return True - 过滤，不需要加载
# return False - 不过滤，需要加载
def __filter_domain(domain, target_domains):
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


# 快速设置cookie和代理
# is_set_cookie True / False
# is_set_proxy True / False
def quickly_set(is_set_cookie=True, is_set_proxy=True):
    import robot
    config = robot.read_config(os.path.join(os.getcwd(), "..\\common\\config.ini"))
    if is_set_cookie:
        # 操作系统&浏览器
        browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
        # cookie
        is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
        if is_auto_get_cookie:
            cookie_path = robot.tool.get_default_browser_cookie_path(browser_type)
        else:
            cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
        set_cookie_from_browser(cookie_path, browser_type)
    if is_set_proxy:
        proxy_ip = robot.get_config(config, "PROXY_IP", "127.0.0.1", 0)
        proxy_port = robot.get_config(config, "PROXY_PORT", "8087", 0)
        set_proxy(proxy_ip, proxy_port)


# 设置空的cookies，后续所有请求会携带cookies访问资源
def set_empty_cookie():
    cookie_jar = cookielib.MozillaCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
    urllib2.install_opener(opener)
