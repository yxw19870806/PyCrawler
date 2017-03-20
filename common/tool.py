# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import hashlib
import os
import platform
import random
import shutil
import sqlite3
import ssl
import sys
import time
import threading
if platform.system() == "Windows":
    import win32crypt

# 初始化操作
if sys.version_info < (2, 7, 12):
    raise Exception("python版本过低，请访问官网 https://www.python.org/downloads/ 更新")
elif sys.version_info >= (3,):
    raise Exception("仅支持python2.X，请访问官网 https://www.python.org/downloads/ 安装最新的python2")
# disable URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:590)>
ssl._create_default_https_context = ssl._create_unverified_context
thread_lock = threading.Lock()
if getattr(sys, "frozen", False):
    IS_EXECUTABLE = True
else:
    IS_EXECUTABLE = False


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


# 从浏览器保存的cookies中获取指定key的cookie value
def get_cookie_value_from_browser(cookie_key, file_path, browser_type, target_domains=""):
    if not os.path.exists(file_path):
        print_msg("cookie目录：" + file_path + " 不存在")
        return None
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
                if cookie_list[0] == cookie_key:
                    return cookie_list[1]
    elif browser_type == 2:
        con = sqlite3.connect(os.path.join(file_path, "cookies.sqlite"))
        cur = con.cursor()
        cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if __filter_domain(domain, target_domains):
                continue
            if cookie_info[4] == cookie_key:
                return cookie_info[5]
    elif browser_type == 3:
        con = sqlite3.connect(os.path.join(file_path, "Cookies"))
        cur = con.cursor()
        cur.execute("select host_key, path, secure, expires_utc, name, value, encrypted_value from cookies")
        for cookie_info in cur.fetchall():
            domain = cookie_info[0]
            if __filter_domain(domain, target_domains):
                continue
            if cookie_info[4] == cookie_key:
                try:
                    value = win32crypt.CryptUnprotectData(cookie_info[6], None, None, None, 0)[1]
                except:
                    return None
                return value
    else:
        print_msg("不支持的浏览器类型：" + browser_type)
        return None
    return None


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


# 从浏览器保存的cookie文件中读取所有cookie
# return    {
#           "domain1": {"key1": "value1", "key2": "value2", ......}
#           "domain2": {"key1": "value1", "key2": "value2", ......}
#           }
def get_all_cookie_from_browser(browser_type, file_path):
    if not os.path.exists(file_path):
        print_msg("cookie目录：" + file_path + " 不存在")
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
        print_msg("不支持的浏览器类型：" + browser_type)
        return None
    return all_cookies


# 控制台输出
def print_msg(msg, is_time=True):
    if is_time:
        msg = get_time() + " " + msg
    thread_lock.acquire()
    # 终端输出编码
    output_encoding = sys.stdout.encoding
    if output_encoding == "utf-8":
        print msg
    else:
        print msg.decode("utf-8").encode(output_encoding)
    thread_lock.release()


# 控制台输入
def console_input(msg):
    output_encoding = sys.stdout.encoding
    if output_encoding != "utf-8":
        msg = msg.decode("utf-8").encode(output_encoding)
    return raw_input(msg)


# 获取时间
def get_time():
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))


# 根据开始与结束的字符串，截取字符串
# include_string是否包含查询条件的字符串
#   0 都不包含
#   1 只包含start_string
#   2 只包含end_string
#   3 包含start_string和end_string
def find_sub_string(string, start_string=None, end_string=None, include_string=0):
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
        # 开始字符串第一次出现的位置
        start_index = string.find(start_string)
        if start_index == -1:
            return ""
        # 加上开始字符串的长度
        if start_string is not None:
            start_index += len(start_string)

    if end_string is None:
        stop_index = len(string)
    else:
        # 结束字符串第一次出现的位置
        stop_index = string.find(end_string, start_index)
        if stop_index == -1:
            return ""

    find_string = string[start_index:stop_index]
    # 是否需要追加开始或结束字符串
    if include_string & 1 == 1 and start_string is not None:
        find_string = start_string + find_string
    if include_string & 2 == 2 and end_string is not None:
        find_string += end_string
    return find_string


# 文件路径编码转换
# todo 优化
def change_path_encoding(path):
    try:
        if isinstance(path, unicode):
            path = path.encode("GBK")
        else:
            path = path.decode("UTF-8").encode("GBK")
    except UnicodeEncodeError:
        if isinstance(path, unicode):
            path = path.encode("UTF-8")
        else:
            path = path.decode("UTF-8")
    except UnicodeDecodeError:
        if isinstance(path, unicode):
            path = path.encode("UTF-8")
        else:
            path = path.decode("UTF-8")
    return path


# 写文件
# type=1: 追加
# type=2: 覆盖
def write_file(msg, file_path, append_type=1):
    thread_lock.acquire()
    if append_type == 1:
        file_handle = open(file_path, "a")
    else:
        file_handle = open(file_path, "w")
    file_handle.write(msg + "\n")
    file_handle.close()
    thread_lock.release()


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


# 删除整个目录以及目录下所有文件
def remove_dir(dir_path):
    dir_path = change_path_encoding(dir_path)
    if not os.path.exists(dir_path):
        return True
    shutil.rmtree(dir_path, True)


# 删除指定目录下的全部空文件夹
def delete_null_dir(dir_path):
    if os.path.isdir(dir_path):
        for file_name in os.listdir(dir_path):
            sub_path = os.path.join(dir_path, file_name)
            if os.path.isdir(sub_path):
                delete_null_dir(sub_path)
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)


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
                    input_str = console_input(get_time() + " 目录：" + dir_path + " 已存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
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


# 获取指定文件的MD5值
def get_file_md5(file_path):
    file_path = change_path_encoding(file_path)
    if not os.path.exists(file_path):
        return None
    file_handle = open(file_path, "rb")
    md5_obj = hashlib.md5()
    md5_obj.update(file_handle.read())
    file_handle.close()
    return md5_obj.hexdigest()


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
