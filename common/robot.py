# -*- coding:UTF-8  -*-

from common import log
import tool
import os
import time
import traceback

IS_INIT = False


class Robot(object):

    def __init__(self):
        global IS_INIT
        config = analyze_config(os.path.join(os.path.abspath(""), "..\\common\\config.ini"))

        # 日志
        self.is_show_error = get_config(config, "IS_SHOW_ERROR", 1, 2)
        self.is_show_step = get_config(config, "IS_SHOW_STEP", 1, 2)
        self.is_show_trace = get_config(config, "IS_SHOW_TRACE", 0, 2)
        self.error_log_path = get_config(config, "ERROR_LOG_PATH", "log/errorLog.txt", 3)
        error_log_dir = os.path.dirname(self.error_log_path)
        if not tool.make_dir(error_log_dir, 0):
            tool.print_msg("创建错误日志目录：" + error_log_dir + " 失败，程序结束！", True)
            tool.process_exit()
        is_log = get_config(config, "IS_LOG", 1, 2)
        if is_log == 0:
            self.step_log_path = ""
        else:
            self.step_log_path = get_config(config, "TRACE_LOG_PATH", "log/stepLog.txt", 3)
            # 日志文件保存目录
            step_log_dir = os.path.dirname(self.step_log_path)
            if not tool.make_dir(step_log_dir, 0):
                tool.print_msg("创建步骤日志目录：" + step_log_dir + " 失败，程序结束！", True)
                tool.process_exit()
        if False:
            self.trace_log_path = ""
        else:
            self.trace_log_path = get_config(config, "STEP_LOG_PATH", "log/traceLog.txt", 3)
            trace_log_dir = os.path.dirname(self.trace_log_path)
            if not tool.make_dir(trace_log_dir, 0):
                tool.print_msg("创建调试日志目录：" + trace_log_dir + " 失败，程序结束！", True)
                tool.process_exit()

        if not IS_INIT:
            log.IS_SHOW_ERROR = self.is_show_error
            log.IS_SHOW_STEP = self.is_show_step
            log.IS_SHOW_TRACE = self.is_show_trace
            log.ERROR_LOG_PATH = self.error_log_path
            log.STEP_LOG_PATH = self.step_log_path
            log.TRACE_LOG_PATH = self.trace_log_path
            IS_INIT = True

        # 存档
        self.image_download_path = get_config(config, "IMAGE_DOWNLOAD_PATH", "photo", 3)
        self.image_temp_path = get_config(config, "IMAGE_TEMP_PATH", "tempImage", 3)

        self.is_sort = get_config(config, "IS_SORT", 1, 2)
        self.get_image_count = get_config(config, "GET_IMAGE_COUNT", 0, 2)

        self.save_data_path = get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)

        # 代理
        self.is_proxy = get_config(config, "IS_PROXY", 2, 2)
        self.proxy_ip = get_config(config, "PROXY_IP", "127.0.0.1", 0)
        self.proxy_port = get_config(config, "PROXY_PORT", "8087", 0)

        # 操作系统&浏览器
        self.browser_version = get_config(config, "BROWSER_VERSION", 2, 2)

        # cookie
        is_auto_get_cookie = get_config(config, "IS_AUTO_GET_COOKIE", 1, 2)
        if is_auto_get_cookie == 0:
            self.cookie_path = get_config(config, "COOKIE_PATH", "", 0)
        else:
            self.cookie_path = tool.get_default_browser_cookie_path(self.browser_version)

        # 线程数
        self.thread_count = get_config(config, "THREAD_COUNT", 10, 2)


# 获取配置文件
# config : 字典格式，如：{key1:value1, key2:value2}
# mode=0 : 直接赋值
# mode=1 : 字符串拼接
# mode=2 : 取整
# mode=3 : 文件路径，以"\"开头的为当前目录下创建
# prefix: 前缀，只有在mode=1时有效
# postfix: 后缀，只有在mode=1时有效
def get_config(config, key, default_value, mode, prefix=None, postfix=None):
    value = None
    if key in config:
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
                tool.print_msg("配置文件config.ini中key为'" + key + "'的值必须是一个整数，使用程序默认设置")
                traceback.print_exc()
                value = default_value
        elif mode == 3:
            value = config[key]
            if value[0] == "\\":
                value = os.path.join(os.path.abspath(""), value[1:])  # 第一个 \ 仅做标记使用，实际需要去除
    else:
        tool.print_msg("配置文件config.ini中没有找到key为'" + key + "'的参数，使用程序默认设置")
        value = default_value
    return value


# 读取配置文件，并生成配置字典
def analyze_config(config_path):
    config_file = open(config_path, "r")
    lines = config_file.readlines()
    config_file.close()
    config = {}
    for line in lines:
        if len(line) == 0:
            continue
        line = line.lstrip().rstrip().replace(" ", "")
        if len(line) > 1 and line[0] != "#" and line.find("=") >= 0:
            try:
                line = line.split("=")
                config[line[0]] = line[1]
            except Exception, e:
                tool.print_msg(str(e))
                pass
    return config


# 将制定文件夹内的所有文件排序重命名并复制到其他文件夹中
def sort_file(source_path, destination_path, start_count, file_name_length):
    image_list = tool.get_dir_files_name(source_path, "desc")
    # 判断排序目标文件夹是否存在
    if len(image_list) >= 1:
        if not tool.make_dir(destination_path, 0):
            return False
        # 倒叙排列
        for file_name in image_list:
            start_count += 1
            file_type = os.path.splitext(file_name)[1]
            new_file_name = str(("%0" + str(file_name_length) + "d") % start_count) + file_type
            tool.copy_files(os.path.join(source_path, file_name), os.path.join(destination_path, new_file_name))
        # 删除临时文件夹
        tool.remove_dir(source_path)
    return True


# 读取存档文件，并根据指定列生成存档字典
# default_value_list 每一位的默认值
def read_save_data(save_data_path, key_index, default_value_list):
    result_list = {}
    if os.path.exists(save_data_path):
        save_data_file = open(save_data_path, "r")
        save_list = save_data_file.readlines()
        save_data_file.close()
        for single_save_data in save_list:
            single_save_data = single_save_data.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
            if len(single_save_data) < 1:
                continue
            single_save_list = single_save_data.split("\t")

            # 根据default_value_list给没给字段默认值
            index = 0
            for default_value in default_value_list:
                # _开头表示和该数组下标的值一直，如["", "_0"] 表示第1位为空时数值和第0位一致
                if default_value != "" and default_value[0] == "_":
                    default_value = single_save_list[int(default_value.replace("_", ""))]
                if len(single_save_list) <= index:
                    single_save_list.append(default_value)
                if single_save_list[index] == "":
                    single_save_list[index] = default_value
                index += 1
            result_list[single_save_list[key_index]] = single_save_list
    return result_list


# 对存档文件夹按照指定列重新排序
def sort_save_data(save_data_path, sort_key_index=0):
    save_data_file = open(save_data_path, "")
    lines = save_data_file.readlines()
    save_data_file.close()
    line_list = {}
    for line in lines:
        line = line.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
        temp_list = line.split("\t")
        if len(temp_list) > 0:
            line_list[temp_list[sort_key_index]] = temp_list

    save_data_file = open(save_data_path, "w")
    for sort_key in sorted(line_list.keys()):
        save_data_file.write("\t".join(line_list[sort_key]) + "\n")
    save_data_file.close()


# 生成新存档的文件路径
def get_new_save_file_path(old_save_file_path):
    return os.path.join(os.path.dirname(old_save_file_path), time.strftime("%m-%d_%H_%M_", time.localtime(time.time())) + os.path.basename(old_save_file_path))