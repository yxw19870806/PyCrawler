# -*- coding:UTF-8  -*-
"""
爬虫父类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import browser, keyboardEvent, log, net, output, path, tool
import codecs
import ConfigParser
import os
import re
import sys
import thread
import threading
import time

# 程序是否支持下载图片功能（会判断配置中是否需要下载图片，如全部是则创建图片下载目录）
SYS_DOWNLOAD_IMAGE = "download_image"
# 程序是否支持下载视频功能（会判断配置中是否需要下载视频，如全部是则创建视频下载目录）
SYS_DOWNLOAD_VIDEO = "download_video"
# 程序是否默认需要设置代理
SYS_SET_PROXY = "set_proxy"
# 程序是否支持不需要存档文件就可以开始运行
SYS_NOT_CHECK_SAVE_DATA = "no_save_data"
# 程序是否需要从浏览器存储的cookie中获取指定cookie的值
SYS_GET_COOKIE = "get_cookie"
# 程序是否需要额外读取配置（应用级别）
# 传入参数类型为tuple，且长度至少为二
# 第一位是配置文件所在路径
# 第二位开始是配置规则，类型为tuple，每个配置规则长度为3，顺序为(配置名字，默认值，配置读取方式)，同analysis_config方法后三个参数
SYS_APP_CONFIG = "app_config"

CONFIG_ANALYSIS_MODE_RAW = 0
CONFIG_ANALYSIS_MODE_INTEGER = 1
CONFIG_ANALYSIS_MODE_BOOLEAN = 2
CONFIG_ANALYSIS_MODE_PATH = 3


class Crawler(object):
    total_image_count = 0
    total_video_count = 0
    print_function = None
    thread_event = None
    prcess_status = True  # 主进程是否在运行

    # 输出错误日志
    def print_msg(self, msg):
        if self.print_function is None:
            output.print_msg(msg, True)
        else:
            self.print_function(msg)

    # 程序全局变量的设置
    def __init__(self, sys_config, extra_config=None):
        self.start_time = time.time()

        # 程序启动配置
        if not isinstance(sys_config, dict):
            self.print_msg("程序启动配置不存在，请检查代码！")
            tool.process_exit()
            return
        sys_download_image = SYS_DOWNLOAD_IMAGE in sys_config
        sys_download_video = SYS_DOWNLOAD_VIDEO in sys_config
        sys_set_proxy = SYS_SET_PROXY in sys_config
        sys_get_cookie = SYS_GET_COOKIE in sys_config
        sys_not_check_save_data = SYS_NOT_CHECK_SAVE_DATA in sys_config

        # exe程序
        if tool.IS_EXECUTABLE:
            application_path = os.path.dirname(sys.executable)
            os.chdir(application_path)
            config_path = os.path.join(os.getcwd(), "data/config.ini")
        else:
            config_path = tool.PROJECT_CONFIG_PATH

        # 程序配置
        config = read_config(config_path)
        if not isinstance(extra_config, dict):
            extra_config = {}

        # 应用配置
        self.app_config = {}
        if SYS_APP_CONFIG in sys_config and len(sys_config[SYS_APP_CONFIG]) >= 2:
            if os.path.exists(sys_config[SYS_APP_CONFIG][0]):
                app_config = read_config(sys_config[SYS_APP_CONFIG][0])
            else:
                app_config = {}
            for app_config_template in sys_config[SYS_APP_CONFIG][1:]:
                if len(app_config_template) == 3:
                    self.app_config[app_config_template[0]] = analysis_config(app_config, app_config_template[0], app_config_template[1], app_config_template[2])

        # 日志
        log.IS_SHOW_ERROR = self.is_show_error = analysis_config(config, "IS_SHOW_ERROR", True, CONFIG_ANALYSIS_MODE_BOOLEAN)
        log.IS_SHOW_STEP = self.is_show_step = analysis_config(config, "IS_SHOW_STEP", True, CONFIG_ANALYSIS_MODE_BOOLEAN)
        log.IS_SHOW_TRACE = self.is_show_trace = analysis_config(config, "IS_SHOW_TRACE", False, CONFIG_ANALYSIS_MODE_BOOLEAN)
        error_log_path = analysis_config(config, "ERROR_LOG_PATH", "\\log/errorLog.txt", CONFIG_ANALYSIS_MODE_PATH)
        log.ERROR_LOG_PATH = self.error_log_path = replace_path(error_log_path)
        error_log_dir = os.path.dirname(self.error_log_path)
        if not path.create_dir(error_log_dir):
            self.print_msg("创建错误日志目录 %s 失败" % error_log_dir)
            tool.process_exit()
            return
        is_log_step = analysis_config(config, "IS_LOG_STEP", True, CONFIG_ANALYSIS_MODE_BOOLEAN)
        if not is_log_step:
            log.STEP_LOG_PATH = self.step_log_path = ""
        else:
            step_log_path = analysis_config(config, "STEP_LOG_PATH", "\\log/stepLog.txt", CONFIG_ANALYSIS_MODE_PATH)
            log.STEP_LOG_PATH = self.step_log_path = replace_path(step_log_path)
            # 日志文件保存目录
            step_log_dir = os.path.dirname(self.step_log_path)
            if not path.create_dir(step_log_dir):
                self.print_msg("创建步骤日志目录 %s 失败" % step_log_dir)
                tool.process_exit()
                return
        is_log_trace = analysis_config(config, "IS_LOG_TRACE", True, CONFIG_ANALYSIS_MODE_BOOLEAN)
        if not is_log_trace:
            log.TRACE_LOG_PATH = self.trace_log_path = ""
        else:
            trace_log_path = analysis_config(config, "TRACE_LOG_PATH", "\\log/traceLog.txt", CONFIG_ANALYSIS_MODE_PATH)
            log.TRACE_LOG_PATH = self.trace_log_path = replace_path(trace_log_path)
            # 日志文件保存目录
            trace_log_dir = os.path.dirname(self.trace_log_path)
            if not path.create_dir(trace_log_dir):
                self.print_msg("创建调试日志目录 %s 失败" % trace_log_dir)
                tool.process_exit()
                return

        # 是否下载
        self.is_download_image = analysis_config(config, "IS_DOWNLOAD_IMAGE", True, CONFIG_ANALYSIS_MODE_BOOLEAN) and sys_download_image
        self.is_download_video = analysis_config(config, "IS_DOWNLOAD_VIDEO", True, CONFIG_ANALYSIS_MODE_BOOLEAN) and sys_download_video

        if not self.is_download_image and not self.is_download_video:
            if sys_download_image or sys_download_video:
                self.print_msg("所有支持的下载都没有开启，请检查配置！")
                tool.process_exit()
                return

        # 存档
        if "save_data_path" in extra_config:
            self.save_data_path = os.path.realpath(extra_config["save_data_path"])
        else:
            self.save_data_path = analysis_config(config, "SAVE_DATA_PATH", "\\\\info/save.data", CONFIG_ANALYSIS_MODE_PATH)
        if not sys_not_check_save_data and not os.path.exists(self.save_data_path):
            # 存档文件不存在
            self.print_msg("存档文件%s不存在！" % self.save_data_path)
            tool.process_exit()
            return
        temp_file_name = time.strftime("%m-%d_%H_%M_", time.localtime(time.time())) + os.path.basename(self.save_data_path)
        self.temp_save_data_path = os.path.join(os.path.dirname(self.save_data_path), temp_file_name)

        # 是否需要下载图片
        if self.is_download_image:
            # 图片保存目录
            if "image_download_path" in extra_config:
                self.image_download_path = os.path.realpath(extra_config["image_download_path"])
            else:
                self.image_download_path = analysis_config(config, "IMAGE_DOWNLOAD_PATH", "\\\\photo", CONFIG_ANALYSIS_MODE_PATH)
            if not path.create_dir(self.image_download_path):
                # 图片保存目录创建失败
                self.print_msg("图片保存目录%s创建失败！" % self.image_download_path)
                tool.process_exit()
                return
        else:
            self.image_download_path = ""
        # 是否需要下载视频
        if self.is_download_video:
            # 视频保存目录
            if "video_download_path" in extra_config:
                self.video_download_path = os.path.realpath(extra_config["video_download_path"])
            else:
                self.video_download_path = analysis_config(config, "VIDEO_DOWNLOAD_PATH", "\\\\video", CONFIG_ANALYSIS_MODE_PATH)
            if not path.create_dir(self.video_download_path):
                # 视频保存目录创建失败
                self.print_msg("视频保存目录%s创建失败！" % self.video_download_path)
                tool.process_exit()
                return
        else:
            self.video_download_path = ""

        # 代理
        is_proxy = analysis_config(config, "IS_PROXY", 2, CONFIG_ANALYSIS_MODE_INTEGER)
        if is_proxy == 1 or (is_proxy == 2 and sys_set_proxy):
            proxy_ip = analysis_config(config, "PROXY_IP", "127.0.0.1")
            proxy_port = analysis_config(config, "PROXY_PORT", "8087")
            # 使用代理的线程池
            net.set_proxy(proxy_ip, proxy_port)
        else:
            # 初始化urllib3的线程池
            net.init_http_connection_pool()

        # cookies
        self.cookie_value = {}
        if sys_get_cookie:
            # 操作系统&浏览器
            browser_type = analysis_config(config, "BROWSER_TYPE", 2, CONFIG_ANALYSIS_MODE_INTEGER)
            # cookie
            is_auto_get_cookie = analysis_config(config, "IS_AUTO_GET_COOKIE", True, CONFIG_ANALYSIS_MODE_BOOLEAN)
            if is_auto_get_cookie:
                cookie_path = browser.get_default_browser_cookie_path(browser_type)
            else:
                cookie_path = analysis_config(config, "COOKIE_PATH", "")
            all_cookie_from_browser = browser.get_all_cookie_from_browser(browser_type, cookie_path)
            for cookie_domain in sys_config[SYS_GET_COOKIE]:
                # 如果指定了cookie key
                if sys_config[SYS_GET_COOKIE][cookie_domain]:
                    for cookie_key in sys_config[SYS_GET_COOKIE][cookie_domain]:
                        self.cookie_value[cookie_key] = ""
                    if cookie_domain in all_cookie_from_browser:
                        for cookie_name in self.cookie_value:
                            if cookie_name in all_cookie_from_browser[cookie_domain]:
                                self.cookie_value[cookie_name] = all_cookie_from_browser[cookie_domain][cookie_name]
                # 没有指定cookie key那么就是取全部
                else:
                    if cookie_domain in all_cookie_from_browser:
                        for cookie_name in all_cookie_from_browser[cookie_domain]:
                            self.cookie_value[cookie_name] = all_cookie_from_browser[cookie_domain][cookie_name]

        # Http Setting
        net.HTTP_CONNECTION_TIMEOUT = analysis_config(config, "HTTP_CONNECTION_TIMEOUT", 10, CONFIG_ANALYSIS_MODE_INTEGER)
        net.HTTP_REQUEST_RETRY_COUNT = analysis_config(config, "HTTP_REQUEST_RETRY_COUNT", 10, CONFIG_ANALYSIS_MODE_INTEGER)

        # 线程数
        self.thread_count = analysis_config(config, "THREAD_COUNT", 10, CONFIG_ANALYSIS_MODE_INTEGER)
        self.thread_lock = threading.Lock()  # 线程锁，避免操作一些全局参数
        self.thread_condition = threading.Condition()  # 线程数达到上限时等待wait()，直到任意线程唤醒notify()

        # 启用线程监控是否需要暂停其他下载线程
        # process_control_thread = process.ProcessControl()
        # process_control_thread.setDaemon(True)
        # process_control_thread.start()

        # 键盘监控线程
        if analysis_config(config, "IS_KEYBOARD_EVENT", True, CONFIG_ANALYSIS_MODE_BOOLEAN):
            keyboard_event_bind = {}
            pause_process_key = analysis_config(config, "PAUSE_PROCESS_KEYBOARD_KEY", "F9")
            # 暂停进程
            if pause_process_key:
                keyboard_event_bind[pause_process_key] = net.pause_request
            # 继续进程
            continue_process_key = analysis_config(config, "CONTINUE_PROCESS_KEYBOARD_KEY", "F10")
            if continue_process_key:
                keyboard_event_bind[continue_process_key] = net.resume_request
            # 结束进程（取消当前的线程，完成任务）
            stop_process_key = analysis_config(config, "STOP_PROCESS_KEYBOARD_KEY", "CTRL + F12")
            if stop_process_key:
                keyboard_event_bind[stop_process_key] = self.stop_process

            if keyboard_event_bind:
                keyboard_control_thread = keyboardEvent.KeyboardEvent(keyboard_event_bind)
                keyboard_control_thread.setDaemon(True)
                keyboard_control_thread.start()

        self.print_msg("初始化完成")

    def stop_process(self):
        output.print_msg("stop process")
        net.resume_request
        self.prcess_status = False

    # 获取程序已运行时间（seconds）
    def get_run_time(self):
        """Get process runned time(seconds)"""
        return int(time.time() - self.start_time)

    def is_running(self):
        return self.prcess_status

    def wait_sub_thread(self):
        self.thread_condition.acquire()
        self.thread_condition.wait()
        self.thread_condition.release()


class DownloadThread(threading.Thread):
    """Download sub-thread"""
    main_thread = None
    thread_lock = None
    total_image_count = 0
    total_video_count = 0
    temp_path_list = []

    def __init__(self, account_info, main_thread):
        """
        :param account_info:

        :param thread_lock:
            threading.Lock() object in main thread

        :param thread_event:
            threading.Event() object in main thread, flag of process is running
        """
        threading.Thread.__init__(self)
        self.account_info = account_info
        if isinstance(main_thread, Crawler):
            self.main_thread = main_thread
            self.thread_lock = main_thread.thread_lock
        else:
            output.print_msg("下载线程参数异常")
            tool.process_exit()

    # 检测主线程是否已经结束（外部中断）
    def main_thread_check(self):
        if not self.main_thread.is_running():
            self.notify_main_thread()
            tool.process_exit(0)

    # 线程下完完成后唤醒主线程，开启新的线程
    def notify_main_thread(self):
        self.main_thread.thread_condition.acquire()
        self.main_thread.thread_condition.notify()
        self.main_thread.thread_condition.release()

    # 中途退出，删除临时文件/目录
    def clean_temp_path(self):
        for temp_path in self.temp_path_list:
            path.delete_dir_or_file(temp_path)


class CrawlerException(SystemExit):
    def __init__(self, msg=""):
        SystemExit.__init__(self, 1)
        self.exception_message = msg

    @property
    def message(self):
        return self.exception_message


def read_config(config_path):
    """Read config file"""
    config = ConfigParser.SafeConfigParser()
    with codecs.open(path.change_path_encoding(config_path), encoding="UTF-8-SIG") as file_handle:
        config.readfp(file_handle)
    return config


def analysis_config(config, key, default_value, mode=CONFIG_ANALYSIS_MODE_RAW):
    """Analysis config

    :param config:
        Dictionary of config

    :param key:
        key of config

    :param default_value:
        default value

    :param mode:
        type of analysis mode
        None    direct assignment
        1       conversion to integer
        2       conversion to boolean
                    the value Equivalent to False, or string of "0" and "false" will conversion to False
                    other string will conversion to True
        3       conversion to file path
                    startup with '\', project root path
                    startup with '\\', application root path
    """
    if isinstance(config, ConfigParser.SafeConfigParser) and config.has_option("setting", key):
        value = config.get("setting", key).encode("UTF-8")
    else:
        output.print_msg("配置文件config.ini中没有找到key为'" + key + "'的参数，使用程序默认设置")
        value = default_value
    if mode == CONFIG_ANALYSIS_MODE_INTEGER:
        if isinstance(value, int) or isinstance(value, long) or (isinstance(value, str) and value.isdigit()):
            value = int(value)
        else:
            output.print_msg("配置文件config.ini中key为'" + key + "'的值必须是一个整数，使用程序默认设置")
            value = default_value
    elif mode == CONFIG_ANALYSIS_MODE_BOOLEAN:
        if not value or value == "0" or (isinstance(value, str) and value.lower() == "false"):
            value = False
        else:
            value = True
    elif mode == CONFIG_ANALYSIS_MODE_PATH:
        if value[:2] == "\\\\":  # \\ 开头，程序所在目录
            value = os.path.join(os.path.abspath(""), value[2:])  # \\ 仅做标记使用，实际需要去除
        elif value[0] == "\\":   # \ 开头，项目根目录（common目录上级）
            value = os.path.join(tool.PROJECT_ROOT_PATH, value[1:])  # \ 仅做标记使用，实际需要去除
        value = os.path.realpath(value)
    return value


# 将指定文件夹内的所有文件排序重命名并复制到其他文件夹中
def sort_file(source_path, destination_path, start_count, file_name_length):
    file_list = path.get_dir_files_name(source_path, path.RETURN_FILE_LIST_DESC)
    # 判断排序目标文件夹是否存在
    if len(file_list) >= 1:
        if not path.create_dir(destination_path):
            return False
        # 倒叙排列
        for file_name in file_list:
            start_count += 1
            file_type = os.path.splitext(file_name)[1]  # 包括 .扩展名
            new_file_name = str(("%0" + str(file_name_length) + "d") % start_count) + file_type
            path.copy_files(os.path.join(source_path, file_name), os.path.join(destination_path, new_file_name))
        # 删除临时文件夹
        path.delete_dir_or_file(source_path)
    return True


# 读取存档文件，并根据指定列生成存档字典
# default_value_list 每一位的默认值
def read_save_data(save_data_path, key_index, default_value_list):
    result_list = {}
    if not os.path.exists(path.change_path_encoding(save_data_path)):
        return result_list
    for single_save_data in tool.read_file(save_data_path, tool.READ_FILE_TYPE_LINE):
        single_save_data = single_save_data.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
        if len(single_save_data) == 0:
            continue
        single_save_list = single_save_data.split("\t")

        if single_save_list[key_index] in result_list:
            output.print_msg("存档中存在重复行 %s" % single_save_list[key_index])
            tool.process_exit()

        # 去除前后空格
        single_save_list = map(lambda value: value.strip(), single_save_list)

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
    tool.write_file(tool.list_to_string(temp_list), save_data_path, tool.WRITE_FILE_TYPE_REPLACE)
    path.delete_dir_or_file(temp_save_data_path)


# 替换目录中的指定字符串
def replace_path(path):
    return path.replace("{date}", time.strftime("%y-%m-%d", time.localtime(time.time())))


# 获取当前时间
def get_time():
    return time.strftime("%m-%d %H:%M:%S", time.localtime(time.time()))


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


# 判断是不是整数
def is_integer(number):
    if isinstance(number, int):
        return True
    elif isinstance(number, long):
        return True
    elif str(number).isdigit():
        return True
    return False


# 替换文本中的表情符号
def filter_emoji(text):
    try:
        emoji = re.compile(u'[\U00010000-\U0010ffff]')
    except re.error:
        emoji = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    return emoji.sub('', text)


# 获取网络文件下载失败的原因
def get_save_net_file_failed_reason(return_code):
    if return_code == 404:
        return "源文件已被删除"
    elif return_code == 403:
        return "源文件没有权限下载"
    elif return_code == -1:
        return "源文件地址格式不正确"
    elif return_code == -2:
        return "源文件多次获取失败，可能无法访问"
    elif return_code == -3:
        return "源文件多次下载后和原始文件大小不一致，可能网络环境较差"
    elif return_code > 0:
        return "未知错误，http code %s" % return_code
    else:
        return "未知错误，下载返回码 %s" % return_code


# 获取网络文件下载失败的原因
def get_http_request_failed_reason(return_code):
    # return_code = response.status
    if return_code == 404:
        return "页面已被删除"
    elif return_code == 403:
        return "页面没有权限访问"
    elif return_code == net.HTTP_RETURN_CODE_RETRY:
        return "页面多次访问失败，可能无法访问"
    elif return_code == net.HTTP_RETURN_CODE_URL_INVALID:
        return "URL格式错误"
    elif return_code == net.HTTP_RETURN_CODE_JSON_DECODE_ERROR:
        return "返回信息不是一个有效的JSON格式"
    elif return_code == net.HTTP_RETURN_CODE_DOMAIN_NOT_RESOLVED:
        return "域名无法解析"
    elif return_code > 0:
        return "未知错误，http code %s" % return_code
    else:
        return "未知错误，return code %s" % return_code


# 读取配置文件，快速设置代理
# is_auto = False   始终使用代理
#           True    配置文件未禁止时使用代理（IS_PROXY = 1 or 2)
def quickly_set_proxy(config=None, is_auto=True):
    if not isinstance(config, ConfigParser.SafeConfigParser):
        config = read_config(tool.PROJECT_CONFIG_PATH)
    # 设置代理
    if is_auto:
        is_proxy = analysis_config(config, "IS_PROXY", 2, CONFIG_ANALYSIS_MODE_INTEGER)
        if is_proxy == 0:
            return
    proxy_ip = analysis_config(config, "PROXY_IP", "127.0.0.1")
    proxy_port = analysis_config(config, "PROXY_PORT", "8087")
    # 使用代理的线程池
    net.set_proxy(proxy_ip, proxy_port)


# 读取配置文件，返回存档文件所在路径
def quickly_get_save_data_path(config=None):
    if not isinstance(config, ConfigParser.SafeConfigParser):
        config = read_config(tool.PROJECT_CONFIG_PATH)
    return analysis_config(config, "SAVE_DATA_PATH", "\\\\info/save.data", CONFIG_ANALYSIS_MODE_PATH)


# 读取浏览器cookies
def quickly_get_all_cookies_from_browser(config=None):
    if not isinstance(config, ConfigParser.SafeConfigParser):
        config = read_config(tool.PROJECT_CONFIG_PATH)
    # 是否自动查找cookies路径
    is_auto_get_cookie = analysis_config(config, "IS_AUTO_GET_COOKIE", True, CONFIG_ANALYSIS_MODE_BOOLEAN)
    if not is_auto_get_cookie:
        return {}
    # 操作系统&浏览器
    browser_type = analysis_config(config, "BROWSER_TYPE", browser.BROWSER_TYPE_CHROME, CONFIG_ANALYSIS_MODE_INTEGER)
    cookie_path = browser.get_default_browser_cookie_path(browser_type)
    return browser.get_all_cookie_from_browser(browser_type, cookie_path)
