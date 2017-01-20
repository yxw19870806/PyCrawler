# -*- coding:UTF-8  -*-
"""

@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""

from common import process, tool
import json
import os
import random
import time
import traceback
import urllib3

HTTP_CONNECTION_POOL = None
HTTP_CONNECTION_TIMEOUT = 10
HTTP_REQUEST_RETRY_COUNT = 10
# https://www.python.org/dev/peps/pep-0476/
# disable urllib3 HTTPS warning
urllib3.disable_warnings()

HTTP_RETURN_CODE_RETRY = 0
HTTP_RETURN_CODE_URL_INVALID = -1
HTTP_RETURN_CODE_JSON_DECODE_ERROR = -2
HTTP_RETURN_CODE_EXCEPTION_CATCH = -10


# 错误response的对象
class ErrorResponse(object):
    def __init__(self, status=-1):
        self.status = status
        self.data = None
        self.headers = {}


# 初始化urllib3的连接池
def init_http_connection_pool():
    global HTTP_CONNECTION_POOL
    HTTP_CONNECTION_POOL = urllib3.PoolManager(retries=False, timeout=urllib3.Timeout(connect=HTTP_CONNECTION_TIMEOUT))


# 设置代理，初始化带有代理的urllib3的连接池
def set_proxy(ip, port):
    global HTTP_CONNECTION_POOL
    HTTP_CONNECTION_POOL = urllib3.ProxyManager("http://%s:%s" % (ip, port), retries=False, timeout=urllib3.Timeout(connect=HTTP_CONNECTION_TIMEOUT))
    tool.print_msg("设置代理成功")


# http请求(urlib3)
# header_list       http header信息，e.g. {"Host":“www.example.com"}
# is_random_ip      是否使用伪造IP
# exception_return  如果异常信息中包含以下字符串，直接返回-1
# return            0：无法访问
#                   -1：URL格式不正确
#                   -2：json decode error
#                   -10：特殊异常捕获后的返回
#                   其他>0：网页返回码（正常返回码为200）
def http_request(url, post_data=None, header_list=None, is_random_ip=True, json_decode=False, exception_return=""):
    if not (url.find("http://") == 0 or url.find("https://") == 0):
        return ErrorResponse(HTTP_RETURN_CODE_URL_INVALID)
    if HTTP_CONNECTION_POOL is None:
        init_http_connection_pool()

    retry_count = 0
    while True:
        while process.PROCESS_STATUS == process.PROCESS_STATUS_PAUSE:
            time.sleep(10)
        if process.PROCESS_STATUS == process.PROCESS_STATUS_STOP:
            tool.process_exit(0)

        if header_list is None:
            header_list = {}

        # 设置User-Agent
        header_list["User-Agent"] = _random_user_agent()

        # 设置一个随机IP
        if is_random_ip:
            random_ip = _random_ip_address()
            header_list["X-Forwarded-For"] = random_ip
            header_list["x-Real-Ip"] = random_ip

        try:
            if post_data:
                response = HTTP_CONNECTION_POOL.request('POST', url, fields=post_data, headers=header_list)
            else:
                response = HTTP_CONNECTION_POOL.request('GET', url, headers=header_list)
            if json_decode:
                try:
                    response.json_data = json.loads(response.data)
                except ValueError:
                    return ErrorResponse(HTTP_RETURN_CODE_JSON_DECODE_ERROR)
            return response
        except urllib3.exceptions.ProxyError:
            notice = "无法访问代理服务器，请检查代理设置。检查完成后输入(C)ontinue继续程序或者(S)top退出程序："
            input_str = raw_input(notice).lower()
            if input_str in ["c", "continue"]:
                pass
            elif input_str in ["s", "stop"]:
                tool.process_exit(0)
        # except urllib3.exceptions.MaxRetryError, e:
        #     print_msg(url)
        #     print_msg(str(e))
        #     # 无限重定向
        #     # if str(e).find("Caused by ResponseError('too many redirects',)") >= 0:
        #     #     return ErrorResponse(-1)
        # except urllib3.exceptions.ConnectTimeoutError, e:
        #     print_msg(str(e))
        #     print_msg(url + " 访问超时，稍后重试")
        #     # 域名无法解析
        #     # if str(e).find("[Errno 11004] getaddrinfo failed") >= 0:
        #     #     return ErrorResponse(-2)
        # except urllib3.exceptions.ProtocolError, e:
        #     print_msg(str(e))
        #     print_msg(url + " 访问超时，稍后重试")
        #     # 链接被终止
        #     # if str(e).find("'Connection aborted.', error(10054,") >= 0:
        #     #     return ErrorResponse(-3)
        except Exception, e:
            if exception_return and str(e).find(exception_return) >= 0:
                return ErrorResponse(HTTP_RETURN_CODE_EXCEPTION_CATCH)
            tool.print_msg(str(e))
            tool.print_msg(url + " 访问超时，稍后重试")
            traceback.print_exc()

        retry_count += 1
        if retry_count >= HTTP_REQUEST_RETRY_COUNT:
            tool.print_msg("无法访问页面：" + url)
            return ErrorResponse(HTTP_RETURN_CODE_RETRY)


# 随机生成一个合法的user agent
def _random_user_agent():
    # "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0"
    # "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    firefox_version_max = 49
    # https://zh.wikipedia.org/zh-cn/Google_Chrome
    chrome_version_list = ["45.0.2454", "46.0.2490", "47.0.2526", "48.0.2564", "49.0.2623",
                           "50.0.2661", "51.0.2704", "52.0.2743", "53.0.2785", "54.0.2840"]
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


# 生成一个随机的IP地址
def _random_ip_address():
    return "%s.%s.%s.%s" % (random.randint(1, 254), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


# 获取请求response中的指定信息(urlib3)
def get_response_info(response, key):
    if isinstance(response, urllib3.HTTPResponse):
        if key in response.headers:
            return response.headers[key]
    return None


# 保存网络文件
# file_url 文件所在网址
# file_path 文件所在本地路径，包括路径和文件名
# need_content_type 是否需要读取response中的Content-Type作为后缀名，会自动替换file_path中的后缀名
# return
#       status: 0：失败，1：成功,
#       code:   -1：无法访问（没有获得返回，可能是域名无法解析，请求被直接丢弃，地址被墙等）
#               -2：下载失败（访问没有问题，但下载后与源文件大小不一致，网络问题）
#               > 0：访问出错，对应url的http code
def save_net_file(file_url, file_path, need_content_type=False):
    file_path = tool.change_path_encoding(file_path)
    create_file = False
    for i in range(0, 5):
        response = http_request(file_url)
        if response.status == 200:
            # response中的Content-Type作为文件后缀名
            if need_content_type:
                content_type = get_response_info(response, "Content-Type")
                if content_type and content_type != "octet-stream":
                    file_path = os.path.splitext(file_path)[0] + "." + content_type.split("/")[-1]
            # 下载
            file_handle = open(file_path, "wb")
            file_handle.write(response.data)
            file_handle.close()
            create_file = True
            # 判断文件下载后的大小和response中的Content-Length是否一致
            content_length = get_response_info(response, "Content-Length")
            file_size = os.path.getsize(file_path)
            if (content_length is None) or (int(content_length) == file_size):
                return {"status": 1, "code": 0}
            else:
                tool.print_msg("本地文件%s：%s和网络文件%s：%s不一致" % (file_path, content_length, file_url, file_size))
        # 超过重试次数，直接退出
        elif response.status == 0:
            if create_file:
                os.remove(file_path)
            return {"status": 0, "code": -1}
        # 其他http code，退出
        else:
            if create_file:
                os.remove(file_path)
            return {"status": 0, "code": response.status}
    if create_file:
        os.remove(file_path)
    return {"status": 0, "code": -2}
