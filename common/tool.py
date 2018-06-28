# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import base64
import hashlib
import json
import os
import platform
import random
import string
import sys
from Crypto.Cipher import AES
from common import path

# if sys.stdout.encoding != "UTF-8":
#     raise Exception("项目编码必须是UTF-8，请在IDE中修改相关设置")
if sys.version_info < (2, 7, 12):
    raise Exception("python版本过低，请访问官网 https://www.python.org/downloads/ 更新")
elif sys.version_info >= (3,):
    raise Exception("仅支持python2.X，请访问官网 https://www.python.org/downloads/ 安装最新的python2")
if getattr(sys, "frozen", False):
    IS_EXECUTABLE = True
else:
    IS_EXECUTABLE = False

READ_FILE_TYPE_FULL = 1  # 读取整个文件 ，返回字符串
READ_FILE_TYPE_LINE = 2  # 按行读取，返回list

WRITE_FILE_TYPE_APPEND = 1  # 追加写入文件
WRITE_FILE_TYPE_REPLACE = 2  # 覆盖写入文件

# 项目根目录
PROJECT_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# common目录
PROJECT_COMMON_PATH = os.path.abspath(os.path.join(PROJECT_ROOT_PATH, "common"))
# config.ini路径
PROJECT_CONFIG_PATH = os.path.abspath(os.path.join(PROJECT_ROOT_PATH, "common/config.ini"))
# 应用程序（APP）根目录，下面包含多个应用
PROJECT_APP_ROOT_PATH = os.path.abspath(os.path.join(PROJECT_ROOT_PATH, "project"))
# 应用程序（APP）目录
PROJECT_APP_PATH = os.getcwd()


# 根据开始与结束的字符串，截取字符串
# include_string是否包含查询条件的字符串
#   0 都不包含
#   1 只包含start_string
#   2 只包含end_string
#   3 包含start_string和end_string
def find_sub_string(haystack, start_string=None, end_string=None, include_string=0):
    # 参数验证
    haystack = str(haystack)
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
        start_index = haystack.find(start_string)
        if start_index == -1:
            return ""
        # 加上开始字符串的长度
        if start_string is not None:
            start_index += len(start_string)

    if end_string is None:
        stop_index = len(haystack)
    else:
        # 结束字符串第一次出现的位置
        stop_index = haystack.find(end_string, start_index)
        if stop_index == -1:
            return ""

    find_string = haystack[start_index:stop_index]
    # 是否需要追加开始或结束字符串
    if include_string & 1 == 1 and start_string is not None:
        find_string = start_string + find_string
    if include_string & 2 == 2 and end_string is not None:
        find_string += end_string
    return find_string


# decode a json string
def json_decode(json_string, default_value=None):
    try:
        return json.loads(json_string)
    except ValueError:
        pass
    except TypeError:
        pass
    return default_value


# 按照指定连接符合并二维数组生成字符串
def list_to_string(source_lists, first_sign="\n", second_sign="\t"):
    temp_list = []
    for value in source_lists:
        if second_sign != "":
            temp_list.append(second_sign.join(map(str, value)))
        else:
            temp_list.append(str(value))
    return first_sign.join(temp_list)


# 按照指定分割符，分割字符串生成二维数组
def string_to_list(source_string, first_split="\n", second_split="\t"):
    result = source_string.split(first_split)
    if second_split is None:
        return result
    temp_list = []
    for line in result:
        temp_list.append(line.split(second_split))
    return temp_list


# 生成指定长度的随机字符串
# char_lib_type 需要的字库取和， 1 - 大写字母；2 - 小写字母; 4 - 数字，默认7(1+2+4)包括全部
def generate_random_string(string_length, char_lib_type=7):
    char_lib = {
        1: string.lowercase,  # 小写字母
        2: string.uppercase,  # 大写字母
        4: "0123456789",  # 数字
    }
    char_pool = []
    for i, random_string in char_lib.iteritems():
        if char_lib_type & i == i:
            char_pool.append(random_string)
    char_pool = "".join(char_pool)
    if not char_pool:
        return ""
    result = []
    for random_count in range(0, string_length):
        result.append(random.choice(char_pool))
    return "".join(result)


# 获取指定文件的MD5值
def get_file_md5(file_path):
    file_path = path.change_path_encoding(file_path)
    if not os.path.exists(file_path):
        return None
    md5_obj = hashlib.md5()
    with open(file_path, "rb") as file_handle:
        buffer_size = 2**20  # 1M
        while True:
            file_buffer = file_handle.read(buffer_size)
            if not file_buffer:
                break
            md5_obj.update(file_buffer)
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


def read_file(file_path, read_type=READ_FILE_TYPE_FULL):
    """Read local file

    :param file_path:
        the path of file

    :param read_type:
        READ_FILE_TYPE_FULL     read full file
        READ_FILE_TYPE_LINE     read each line of file

    :return:
        READ_FILE_TYPE_FULL     type of string
        READ_FILE_TYPE_LINE     type of list
    """
    file_path = path.change_path_encoding(file_path)
    if not os.path.exists(file_path):
        if read_type == 1:
            return ""
        else:
            return []
    with open(file_path, "r") as file_handle:
        if read_type == 1:
            result = file_handle.read()
            if result[-1] == "\n":
                result = result[:-1]
        else:
            result = []
            for line in file_handle.readlines():
                if line[-1] == "\n":
                    line = line[:-1]
                if len(line) == 0:
                    continue
                result.append(line)
    return result


# 写文件
# type=1: 追加
# type=2: 覆盖
def write_file(msg, file_path, append_type=WRITE_FILE_TYPE_APPEND):
    file_path = path.change_path_encoding(file_path)
    if not path.create_dir(os.path.dirname(file_path)):
        return False
    if append_type == WRITE_FILE_TYPE_APPEND:
        open_type = "a"
    elif append_type == WRITE_FILE_TYPE_REPLACE:
        open_type = "w"
    else:
        return False
    with open(file_path, open_type) as file_handle:
        if isinstance(msg, unicode):
            msg = msg.encode("UTF-8")
        file_handle.write(msg + "\n")


AES_PRIVATE_KEY = "#@PyCrawl@#"


# AES-256加密字符串
def encrypt_string(s):
    # generate aes key
    key = hashlib.md5(AES_PRIVATE_KEY).hexdigest()
    aes_obj = AES.new(key, AES.MODE_CBC, key[:16])

    # base64
    message = base64.b64encode(str(s))
    # 补齐16*n位
    message += "=" * (16 - len(message) % 16)
    return base64.b64encode(aes_obj.encrypt(message))


# AES-256解密字符串
def decrypt_string(s):
    # generate aes key
    key = hashlib.md5(AES_PRIVATE_KEY).hexdigest()
    aes_obj = AES.new(key, AES.MODE_CBC, key[:16])

    try:
        return base64.b64decode(aes_obj.decrypt(base64.b64decode(s)))
    except TypeError:
        return None
    except ValueError:
        return None
