# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import path
import hashlib
import os
import platform
import random
import string
import sys

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

# 项目根目录
PROJECT_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), ".."))
# 项目程序目录
PROJECT_APP_PATH = os.path.join(PROJECT_ROOT_PATH, "project")
# common目录
PROJECT_COMMON_PATH = os.path.join(PROJECT_ROOT_PATH, "common")
# config.ini路径
PROJECT_CONFIG_PATH = os.path.join(PROJECT_ROOT_PATH, "common/config.ini")


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


# 按照指定连接符合并二维数组生成字符串
def list_to_string(source_lists, first_sign="\n", second_sign="\t"):
    temp_list = []
    for value in source_lists:
        if second_sign != "":
            temp_list.append(second_sign.join(map(str, value)))
        else:
            temp_list.append(str(value))
    return first_sign.join(temp_list)


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
        md5_obj.update(file_handle.read())
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


# 读取文件
# type=1: 读取整个文件，同 .read()，返回string
# type=2: 按行读取整个文件，同 .readlines()，返回list
def read_file(file_path, read_type=1):
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
                result.append(line)
    return result


# 写文件
# type=1: 追加
# type=2: 覆盖
def write_file(msg, file_path, append_type=1):
    file_path = path.change_path_encoding(file_path)
    if path.create_dir(os.path.dirname(file_path)):
        if append_type == 1:
            open_type = "a"
        else:
            open_type = "w"
        with open(file_path, open_type) as file_handle:
            if isinstance(msg, unicode):
                msg = msg.encode("UTF-8")
            file_handle.write(msg + "\n")
