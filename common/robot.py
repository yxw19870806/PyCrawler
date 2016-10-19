# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, tool
import codecs
import ConfigParser
import os
import sys
import time

IS_INIT = False


class Robot(object):
    # 程序全局变量的设置
    # is_download_image 程序是否支持下载图片功能（会判断配置中是否需要下载图片，如全部是则创建图片下载目录）
    # is_download_video 程序是否支持下载视频功能（会判断配置中是否需要下载视频，如全部是则创建视频下载目录）
    def __init__(self, is_download_image=False, is_download_video=False, is_auto_proxy=False, extra_config=None):
        global IS_INIT
        self.start_time = time.time()
        self.error_msg = ""

        # exe程序
        if tool.IS_EXECUTABLE:
            application_path = os.path.dirname(sys.executable)
            os.chdir(application_path)
            config_path = os.path.join(os.getcwd(), "data\\config.ini")
        else:
            config_path = os.path.join(os.getcwd(), "..\\common\\config.ini")

        config = read_config(config_path)

        if not isinstance(extra_config, dict):
            extra_config = {}

        # 日志
        self.is_show_error = get_config(config, "IS_SHOW_ERROR", True, 2)
        self.is_show_step = get_config(config, "IS_SHOW_STEP", True, 2)
        self.is_show_trace = get_config(config, "IS_SHOW_TRACE", False, 2)
        error_log_path = get_config(config, "ERROR_LOG_PATH", "log/errorLog.txt", 3)
        self.error_log_path = error_log_path.replace("{date}", time.strftime("%y-%m-%d", time.localtime(time.time())))
        error_log_dir = os.path.dirname(self.error_log_path)

        if not tool.make_dir(error_log_dir, 0):
            tool.print_msg("创建错误日志目录：" + error_log_dir + " 失败", True)
            tool.process_exit()
        is_log_step = get_config(config, "IS_LOG_STEP", True, 2)
        if not is_log_step:
            self.step_log_path = ""
        else:
            step_log_path = get_config(config, "STEP_LOG_PATH", "log/stepLog.txt", 3)
            self.step_log_path = step_log_path.replace("{date}", time.strftime("%y-%m-%d", time.localtime(time.time())))
            # 日志文件保存目录
            step_log_dir = os.path.dirname(self.step_log_path)
            if not tool.make_dir(step_log_dir, 0):
                tool.print_msg("创建步骤日志目录：" + step_log_dir + " 失败", True)
                tool.process_exit()
        is_log_trace = get_config(config, "IS_LOG_TRACE", True, 2)
        if not is_log_trace:
            self.trace_log_path = ""
        else:
            trace_log_path = get_config(config, "TRACE_LOG_PATH", "log/traceLog.txt", 3)
            self.trace_log_path = trace_log_path.replace("{date}", time.strftime("%y-%m-%d", time.localtime(time.time())))
            # 日志文件保存目录
            trace_log_dir = os.path.dirname(self.trace_log_path)
            if not tool.make_dir(trace_log_dir, 0):
                tool.print_msg("创建调试日志目录：" + trace_log_dir + " 失败", True)
                tool.process_exit()

        if not IS_INIT:
            log.IS_SHOW_ERROR = self.is_show_error
            log.IS_SHOW_STEP = self.is_show_step
            log.IS_SHOW_TRACE = self.is_show_trace
            log.ERROR_LOG_PATH = self.error_log_path
            log.STEP_LOG_PATH = self.step_log_path
            log.TRACE_LOG_PATH = self.trace_log_path
            IS_INIT = True

        # 是否下载
        self.is_download_image = get_config(config, "IS_DOWNLOAD_IMAGE", True, 2) and is_download_image
        self.is_download_video = get_config(config, "IS_DOWNLOAD_VIDEO", True, 2) and is_download_video

        if not self.is_download_image and not self.is_download_video:
            # 下载图片和视频都没有开启，请检查配置
            if not is_download_image and not is_download_video:
                self.error_msg = "下载图片和视频都没有开启，请检查配置！"
            elif not is_download_image:
                self.error_msg = "下载图片没有开启，请检查配置！"
            elif not is_download_video:
                self.error_msg = "下载视频没有开启，请检查配置！"
            return

        # 是否需要下载图片
        if self.is_download_image:
            # 图片保存目录
            if "image_download_path" in extra_config:
                self.image_download_path = extra_config["image_download_path"]
            else:
                self.image_download_path = get_config(config, "IMAGE_DOWNLOAD_PATH", "photo", 3)
            if not tool.make_dir(self.image_download_path, 0):
                # 图片保存目录创建失败
                self.error_msg = "图片保存目录%s创建失败！" % self.image_download_path
                return
            # 图片临时下载目录
            if "image_temp_path" in extra_config:
                self.image_temp_path = extra_config["image_temp_path"]
            else:
                self.image_temp_path = get_config(config, "IMAGE_TEMP_PATH", "tempImage", 3)
            if not tool.make_dir(self.image_temp_path, 0):
                # 图片临时下载目录创建失败
                self.error_msg = "图片临时下载目录%s创建失败！" % self.image_temp_path
                return
            # 图片下载数量，0为下载全部可用资源
            self.get_image_count = get_config(config, "GET_IMAGE_COUNT", 0, 1)
        else:
            self.image_download_path = None
            self.image_temp_path = None
            self.get_image_count = 0
        # 是否需要下载视频
        if self.is_download_video:
            # 视频保存目录
            if "video_download_path" in extra_config:
                self.video_download_path = extra_config["video_download_path"]
            else:
                self.video_download_path = get_config(config, "VIDEO_DOWNLOAD_PATH", "video", 3)
            if not tool.make_dir(self.video_download_path, 0):
                # 视频保存目录创建失败
                self.error_msg = "视频保存目录%s创建失败！" % self.video_download_path
                return
            # 视频下载临时目录
            if "video_temp_path" in extra_config:
                self.video_temp_path = extra_config["video_temp_path"]
            else:
                self.video_temp_path = get_config(config, "VIDEO_TEMP_PATH", "tempVideo", 3)
            if not tool.make_dir(self.video_temp_path, 0):
                # 视频下载临时目录创建失败
                self.error_msg = "视频临时下载目录%s创建失败！" % self.video_temp_path
                return
            # 视频下载数量，0为下载全部可用资源
            self.get_video_count = get_config(config, "GET_VIDEO_COUNT", 0, 1)
        else:
            self.video_download_path = None
            self.video_temp_path = None
            self.get_video_count = 0
        # 是否需要重新排序图片
        self.is_sort = get_config(config, "IS_SORT", True, 2)
        self.get_page_count = get_config(config, "GET_PAGE_COUNT", 0, 1)

        # 存档
        if "save_data_path" in extra_config:
            self.save_data_path = extra_config["save_data_path"]
        else:
            self.save_data_path = get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)
        if not os.path.exists(self.save_data_path):
            # 存档文件不存在
            self.error_msg = "视频临时下载目录%s创建失败！" % self.video_temp_path
            return

        # 代理
        is_proxy = get_config(config, "IS_PROXY", 2, 1)
        if is_proxy == 1 or (is_proxy == 2 and is_auto_proxy):
            proxy_ip = get_config(config, "PROXY_IP", "127.0.0.1", 0)
            proxy_port = get_config(config, "PROXY_PORT", "8087", 0)
            tool.set_proxy(proxy_ip, proxy_port)

        # 操作系统&浏览器
        self.browser_version = get_config(config, "BROWSER_VERSION", 2, 1)

        # cookie
        is_auto_get_cookie = get_config(config, "IS_AUTO_GET_COOKIE", True, 2)
        if is_auto_get_cookie:
            self.cookie_path = tool.get_default_browser_cookie_path(self.browser_version)
        else:
            self.cookie_path = get_config(config, "COOKIE_PATH", "", 0)

        # 线程数
        self.thread_count = get_config(config, "THREAD_COUNT", 10, 1)

    # 获取程序已运行时间（seconds）
    def get_run_time(self):
        return time.time() - self.start_time

    # 输出是否有初始化异常
    def init_result(self, print_error_function, print_step_function):
        if self.error_msg:
            print_error_function(self.error_msg)
            tool.process_exit()
            return True
        print_step_function("配置文件读取完成")
        return False


# 读取配置文件
def read_config(config_path):
    config = ConfigParser.SafeConfigParser()
    with codecs.open(config_path, encoding="utf-8-sig") as file_handle:
        config.readfp(file_handle)
    return config


# 获取配置文件
# config : 字典格式，如：{key1:value1, key2:value2}
# mode=0 : 直接赋值
# mode=1 : 取整
# mode=2 : 布尔值，非True的传值或者字符串"0"和"false"为False，其他值为True
# mode=3 : 文件路径，以"\"开头的为当前目录下创建
def get_config(config, key, default_value, mode):
    if config.has_option("setting", key):
        value = config.get("setting", key).encode("utf-8")
    else:
        tool.print_msg("配置文件config.ini中没有找到key为'" + key + "'的参数，使用程序默认设置")
        value = default_value
    if mode == 0:
        pass
    elif mode == 1:
        if isinstance(value, int):
            pass
        elif isinstance(value, str) and value.isdigit():
            value = int(value)
        else:
            tool.print_msg("配置文件config.ini中key为'" + key + "'的值必须是一个整数，使用程序默认设置")
            value = default_value
    elif mode == 2:
        if not value or value == "0" or (isinstance(value, str) and value.lower() == "false"):
            value = False
        else:
            value = True
    elif mode == 3:
        if value[0] == "\\":
            value = os.path.join(os.path.abspath(""), value[1:])  # 第一个 \ 仅做标记使用，实际需要去除
        value = os.path.realpath(value)
    return value


# 将制定文件夹内的所有文件排序重命名并复制到其他文件夹中
def sort_file(source_path, destination_path, start_count, file_name_length):
    file_list = tool.get_dir_files_name(source_path, "desc")
    # 判断排序目标文件夹是否存在
    if len(file_list) >= 1:
        if not tool.make_dir(destination_path, 0):
            return False
        # 倒叙排列
        for file_name in file_list:
            start_count += 1
            file_type = os.path.splitext(file_name)[1]  # 包括 .扩展名
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
            if len(single_save_data) == 0:
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


# 将临时存档文件按照主键排序后写入原始存档文件
# 只支持一行一条记录，每条记录格式相同的存档文件
def rewrite_save_file(temp_save_data_path, save_data_path):
    account_list = read_save_data(temp_save_data_path, 0, [])
    temp_list = [account_list[key] for key in sorted(account_list.keys())]
    tool.write_file(tool.list_to_string(temp_list), save_data_path, 2)
    os.remove(temp_save_data_path)


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


# 判断类型是否为字典，并且检测是否存在指定的key
def check_sub_key(needles, haystack):
    if not isinstance(needles, tuple):
        needles = tuple(needles)
    if isinstance(haystack, dict):
        for needle in needles:
            if needle not in haystack:
                return False
        return True
    return False
