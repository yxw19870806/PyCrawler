# -*- coding:UTF-8  -*-
"""
浏览器数据相关类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import output
import os
import platform
import sqlite3
if platform.system() == "Windows":
    import win32crypt

BROWSER_TYPE_IE = 1
BROWSER_TYPE_FIREFOX = 2
BROWSER_TYPE_CHROME = 3


# 根据浏览器和操作系统，自动查找默认浏览器cookie路径(只支持windows)
# browser_type=1: IE
# browser_type=2: firefox
# browser_type=3: chrome
def get_default_browser_cookie_path(browser_type):
    if platform.system() != "Windows":
        return None
    if browser_type == BROWSER_TYPE_IE:
        return os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Cookies")
    elif browser_type == BROWSER_TYPE_FIREFOX:
        default_browser_path = os.path.join(os.getenv("APPDATA"), "Mozilla\\Firefox\\Profiles")
        for dir_name in os.listdir(default_browser_path):
            if os.path.isdir(os.path.join(default_browser_path, dir_name)):
                if os.path.exists(os.path.join(default_browser_path, dir_name, "cookies.sqlite")):
                    return os.path.join(default_browser_path, dir_name)
    elif browser_type == BROWSER_TYPE_CHROME:
        return os.path.join(os.getenv("LOCALAPPDATA"), "Google\\Chrome\\User Data\\Default")
    else:
        output.print_msg("不支持的浏览器类型：" + browser_type)
    return None


# 从浏览器保存的cookies中获取指定key的cookie value
def get_cookie_value_from_browser(cookie_key, file_path, browser_type, target_domains=""):
    if not os.path.exists(file_path):
        output.print_msg("cookie目录：" + file_path + " 不存在")
        return None
    if browser_type == BROWSER_TYPE_IE:
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
                if cookie_list[0] == cookie_key:
                    return cookie_list[1]
    elif browser_type == BROWSER_TYPE_FIREFOX:
        con = sqlite3.connect(os.path.join(file_path, "cookies.sqlite"))
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if _filter_domain(domain, target_domains):
                continue
            if cookie_info[4] == cookie_key:
                return cookie_info[5]
    elif browser_type == BROWSER_TYPE_CHROME:
        # chrome仅支持windows系统的解密
        if platform.system() != "Windows":
            return None
        con = sqlite3.connect(os.path.join(file_path, "Cookies"))
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value, encrypted_value from cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if _filter_domain(domain, target_domains):
                continue
            if cookie_info[4] == cookie_key:
                try:
                    value = win32crypt.CryptUnprotectData(cookie_info[6], None, None, None, 0)[1]
                except:
                    return None
                return value
    else:
        output.print_msg("不支持的浏览器类型：" + browser_type)
        return None
    return None


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


# 从浏览器保存的cookie文件中读取所有cookie
# return    {
#           "domain1": {"key1": "value1", "key2": "value2", ......}
#           "domain2": {"key1": "value1", "key2": "value2", ......}
#           }
def get_all_cookie_from_browser(browser_type, file_path):
    if not os.path.exists(file_path):
        output.print_msg("cookie目录：" + file_path + " 不存在")
        return None
    all_cookies = {}
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
                cookie_domain = cookie_list[2].split("/")[0]
                cookie_key = cookie_info[0]
                cookie_value = cookie_info[1]
                if cookie_domain not in all_cookies:
                    all_cookies[cookie_domain] = {}
                all_cookies[cookie_domain][cookie_key] = cookie_value
    elif browser_type == 2:
        con = sqlite3.connect(os.path.join(file_path, "cookies.sqlite"))
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        for cookie_info in cur.fetchall():
            cookie_domain = cookie_info[0]
            cookie_key = cookie_info[4]
            cookie_value = cookie_info[5]
            if cookie_domain not in all_cookies:
                all_cookies[cookie_domain] = {}
            all_cookies[cookie_domain][cookie_key] = cookie_value
    elif browser_type == 3:
        # chrome仅支持windows系统的解密
        if platform.system() != "Windows":
            return None
        con = sqlite3.connect(os.path.join(file_path, "Cookies"))
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value, encrypted_value from cookies")
        for cookie_info in cur.fetchall():
            cookie_domain = cookie_info[0]
            cookie_key = cookie_info[4]
            try:
                cookie_value = win32crypt.CryptUnprotectData(cookie_info[6], None, None, None, 0)[1]
            except:
                continue
            if cookie_domain not in all_cookies:
                all_cookies[cookie_domain] = {}
            all_cookies[cookie_domain][cookie_key] = cookie_value
    else:
        output.print_msg("不支持的浏览器类型：" + browser_type)
        return None
    return all_cookies
