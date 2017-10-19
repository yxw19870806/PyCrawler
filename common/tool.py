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
import ssl
import sys
import time
import threading
# if sys.stdout.encoding != "UTF-8":
#     raise Exception("项目编码必须是UTF-8，请在IDE中修改相关设置")
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
# 项目根目录
PROJECT_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), ".."))
# 项目程序目录
PROJECT_APP_PATH = os.path.join(PROJECT_ROOT_PATH, "project")
# common目录
PROJECT_COMMON_PATH = os.path.join(PROJECT_ROOT_PATH, "common")
# config.ini路径
PROJECT_CONFIG_PATH = os.path.join(PROJECT_ROOT_PATH, "common/config.ini")


# 控制台输出（线程安全）
def print_msg(msg, is_time=True):
    if is_time:
        msg = get_time() + " " + msg
    thread_lock.acquire()
    try:
        # 终端输出编码
        output_encoding = sys.stdout.encoding
        if output_encoding == "UTF-8":
            print msg
        else:
            print msg.decode("UTF-8").encode(output_encoding)
    except UnicodeEncodeError:
        print msg
    except:
        raise
    finally:
        thread_lock.release()


# 控制台输入
def console_input(msg):
    output_encoding = sys.stdout.encoding
    if output_encoding != "UTF-8":
        msg = msg.decode("UTF-8").encode(output_encoding)
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
    files_list = map(lambda file_name: file_name.encode("UTF-8"), os.listdir(path))
    # 升序
    if order == "asc":
        return sorted(files_list, reverse=False)
    # 降序
    elif order == "desc":
        return sorted(files_list, reverse=True)
    else:
        return files_list


# 复制文件
# source_file_path      源文件路径
# destination_file_path 目标文件路径
def copy_files(source_file_path, destination_file_path):
    source_file_path = change_path_encoding(source_file_path)
    if not create_dir(os.path.dirname(destination_file_path), 0):
        return
    destination_file_path = change_path_encoding(destination_file_path)
    shutil.copyfile(source_file_path, destination_file_path)


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


# 文件路径编码转换
def change_path_encoding(path):
    if isinstance(path, str):
        path = unicode(path, "UTF-8")
    return os.path.realpath(path)


# 读取文件
# type=1: 读取整个文件，同 .read()，返回string
# type=2: 按行读取整个文件，同 .readlines()，返回list
def read_file(file_path, read_type=1):
    file_path = change_path_encoding(file_path)
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
    file_path = change_path_encoding(file_path)
    if create_dir(os.path.dirname(file_path), 0):
        if append_type == 1:
            open_type = "a"
        else:
            open_type = "w"
        with open(file_path, open_type) as file_handle:
            if isinstance(msg, unicode):
                msg = msg.encode("UTF-8")
            file_handle.write(msg + "\n")


# 创建目录
# create_mode 0 : 不存在则创建
# create_mode 1 : 存在则删除并创建
# create_mode 2 : 存在提示删除，确定后删除创建，取消后退出程序
def create_dir(dir_path, create_mode):
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
                    input_str = console_input(get_time() + " 目录：" + str(dir_path) + " 已存在，是否需要删除该文件夹并继续程序? (Y)es or (N)o: ")
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
    for retry_count in range(0, 5):
        try:
            os.makedirs(dir_path)
            if os.path.isdir(dir_path):
                return True
        except Exception, e:
            print_msg(str(e))
            time.sleep(5)
    return False


# 删除整个目录以及目录下所有文件
def delete_dir_or_file(dir_path):
    dir_path = change_path_encoding(dir_path)
    if not os.path.exists(dir_path):
        return True
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path, True)
    else:
        os.remove(dir_path)


# 删除指定目录下的全部空文件夹
def delete_null_dir(dir_path):
    dir_path = change_path_encoding(dir_path)
    if os.path.isdir(dir_path):
        for file_name in os.listdir(dir_path):
            sub_path = os.path.join(dir_path, file_name)
            if os.path.isdir(sub_path):
                delete_null_dir(sub_path)
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)
