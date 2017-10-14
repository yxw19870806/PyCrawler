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
HTTP_RETURN_CODE_URL_INVALID = -1  # 地址不符合规范（非http:// 或者 https:// 开头）
HTTP_RETURN_CODE_JSON_DECODE_ERROR = -2  # 返回数据不是JSON格式，但返回状态是200
HTTP_RETURN_CODE_DOMAIN_NOT_RESOLVED = -3  # 域名无法解析
HTTP_RETURN_CODE_EXCEPTION_CATCH = -10
HTTP_RETURN_CODE_SUCCEED = 200


# 错误response的对象
class ErrorResponse(object):
    def __init__(self, status=-1):
        self.status = status
        self.data = None
        self.headers = {}
        self.json_data = []


# 初始化urllib3的连接池
def init_http_connection_pool():
    global HTTP_CONNECTION_POOL
    HTTP_CONNECTION_POOL = urllib3.PoolManager(retries=False)


# 设置代理，初始化带有代理的urllib3的连接池
def set_proxy(ip, port):
    global HTTP_CONNECTION_POOL
    HTTP_CONNECTION_POOL = urllib3.ProxyManager("http://%s:%s" % (ip, port), retries=False)
    tool.print_msg("设置代理成功")


# 根据传入cookie key和value，生成一个放入header中的cookie字符串
# {"cookie1":“value1", "cookie2":“value2"} -> cookie1=value1; cookie2=value2
def build_header_cookie_string(cookies_list):
    if not cookies_list:
        return ""
    temp_string = []
    for cookie_name in cookies_list:
        temp_string.append(cookie_name + "=" + cookies_list[cookie_name])
    return "; ".join(temp_string)


# 从请求返回的set-cookie字段解析出全部的cookies内容字典
def get_cookies_from_response_header(response_headers):
    if not isinstance(response_headers, urllib3._collections.HTTPHeaderDict):
        return {}
    if "Set-Cookie" not in response_headers:
        return {}
    cookies_list = {}
    for cookie in response_headers.getlist("Set-Cookie"):
        cookie_name, cookie_value = cookie.split(";")[0].split("=", 1)
        cookies_list[cookie_name] = cookie_value
    return cookies_list


# http请求(urlib3)
# header_list       http header信息，e.g. {"Host":“www.example.com"}
# cookies_list      cookie信息，e.g. {"cookie1":“value1", "cookie2":“value2"}
# is_random_ip      是否使用伪造IP
# exception_return  如果异常信息中包含以下字符串，直接返回-1
# return            0：无法访问
#                   -1：URL格式不正确
#                   -2：json decode error
#                   -10：特殊异常捕获后的返回
#                   其他>0：网页返回码（正常返回码为200）
def http_request(url, method="GET", post_data=None, binary_data=None, header_list=None, cookies_list=None, connection_timeout=HTTP_CONNECTION_TIMEOUT,
                 read_timeout=HTTP_CONNECTION_TIMEOUT, is_random_ip=True, json_decode=False, encode_multipart=False, redirect=True, exception_return=""):
    if not (url.find("http://") == 0 or url.find("https://") == 0):
        return ErrorResponse(HTTP_RETURN_CODE_URL_INVALID)
    method = method.upper()
    if method not in ["GET", "POST", "HEAD"]:
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
        if "User-Agent" not in header_list:
            header_list["User-Agent"] = _random_user_agent()

        # 设置一个随机IP
        if is_random_ip:
            random_ip = _random_ip_address()
            header_list["X-Forwarded-For"] = random_ip
            header_list["X-Real-Ip"] = random_ip

        # 设置cookie
        if cookies_list:
            header_list["Cookie"] = build_header_cookie_string(cookies_list)

        try:
            if connection_timeout == 0 and read_timeout == 0:
                timeout = None
            elif connection_timeout == 0:
                timeout = urllib3.Timeout(read=read_timeout)
            elif read_timeout == 0:
                timeout = urllib3.Timeout(connect=connection_timeout)
            else:
                timeout = urllib3.Timeout(connect=connection_timeout, read=read_timeout)
            if method == "POST":
                if binary_data is None:
                    response = HTTP_CONNECTION_POOL.request(method, url, headers=header_list, redirect=redirect, timeout=timeout, fields=post_data, encode_multipart=encode_multipart)
                else:
                    response = HTTP_CONNECTION_POOL.request(method, url, headers=header_list, redirect=redirect, timeout=timeout, body=binary_data, encode_multipart=encode_multipart)
            else:
                response = HTTP_CONNECTION_POOL.request(method, url, headers=header_list, redirect=redirect, timeout=timeout)
            if response.status == HTTP_RETURN_CODE_SUCCEED and json_decode:
                try:
                    response.json_data = json.loads(response.data)
                except ValueError:
                    is_error = True
                    content_type = response.getheader("Content-Type")
                    if content_type is not None:
                        charset = tool.find_sub_string(content_type, "charset=", None)
                        if charset:
                            if charset == "gb2312":
                                charset = "GBK"
                            try:
                                response.json_data = json.loads(response.data.decode(charset))
                            except:
                                pass
                            else:
                                is_error = False
                    if is_error:
                        response.status = HTTP_RETURN_CODE_JSON_DECODE_ERROR
            return response
        except urllib3.exceptions.ProxyError:
            notice = "无法访问代理服务器，请检查代理设置。检查完成后输入(C)ontinue继续程序或者(S)top退出程序："
            input_str = tool.console_input(notice).lower()
            if input_str in ["c", "continue"]:
                pass
            elif input_str in ["s", "stop"]:
                tool.process_exit(0)
        except urllib3.exceptions.ReadTimeoutError:
            pass
        except urllib3.exceptions.ConnectTimeoutError, e:
            # 域名无法解析
            if str(e).find("[Errno 11004] getaddrinfo failed") >= 0:
                return ErrorResponse(HTTP_RETURN_CODE_DOMAIN_NOT_RESOLVED)
            pass
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
            elif str(e).find("EOF occurred in violation of protocol") >=0:
                time.sleep(30)
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
    firefox_version_max = 55
    # https://zh.wikipedia.org/zh-cn/Google_Chrome
    chrome_version_list = ["51.0.2704", "52.0.2743", "53.0.2785", "54.0.2840", "55.0.2883",
                           "56.0.2924", "57.0.2987", "58.0.3029", "59.0.3071", "60.0.3080"]
    windows_version_list = ["6.1", "6.3", "10.0"]
    browser_type = random.choice(["firefox", "chrome"])
    os_type = random.choice(windows_version_list)
    if browser_type == "firefox":
        firefox_version = random.randint(firefox_version_max - 10, firefox_version_max)
        return "Mozilla/5.0 (Windows NT %s; WOW64; rv:%s.0) Gecko/20100101 Firefox/%s.0" % (os_type, firefox_version, firefox_version)
    elif browser_type == "chrome":
        sub_version = random.randint(1, 100)
        chrome_version = random.choice(chrome_version_list)
        return "Mozilla/5.0 (Windows NT %s; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s.%s Safari/537.36" % (os_type, chrome_version, sub_version)
    return ""


# 生成一个随机的IP地址
def _random_ip_address():
    return "%s.%s.%s.%s" % (random.randint(1, 254), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


# 保存网络文件
# file_url 文件所在网址
# file_path 文件所在本地路径，包括路径和文件名
# need_content_type 是否需要读取response中的Content-Type作为后缀名，会自动替换file_path中的后缀名
# return
#       status: 0：失败，1：成功,
#       code:   -1：无法访问（没有获得返回，可能是域名无法解析，请求被直接丢弃，地址被墙等）
#               -2：下载失败（访问没有问题，但下载后与源文件大小不一致，网络问题）
#               > 0：访问出错，对应url的http code
def save_net_file(file_url, file_path, need_content_type=False, header_list=None, cookies_list=None):
    file_path = tool.change_path_encoding(file_path)
    # 判断保存目录是否存在
    if not tool.make_dir(os.path.dirname(file_path), 0):
        return False
    create_file = False
    for retry_count in range(0, 5):
        response = http_request(file_url, header_list=header_list, cookies_list=cookies_list, read_timeout=60)
        if response.status == HTTP_RETURN_CODE_SUCCEED:
            # response中的Content-Type作为文件后缀名
            if need_content_type:
                content_type = response.getheader("Content-Type")
                if content_type is not None and content_type != "octet-stream":
                    file_path = os.path.splitext(file_path)[0] + "." + content_type.split("/")[-1]
            # 下载
            with open(file_path, "wb") as file_handle:
                file_handle.write(response.data)
            create_file = True
            # 判断文件下载后的大小和response中的Content-Length是否一致
            content_length = response.getheader("Content-Length")
            if content_length is None:
                return {"status": 1, "code": 0, "file_path": file_path}
            file_size = os.path.getsize(file_path)
            if int(content_length) == file_size:
                return {"status": 1, "code": 0, "file_path": file_path}
            else:
                tool.print_msg("本地文件%s：%s和网络文件%s：%s不一致" % (file_path, content_length, file_url, file_size))
        elif response.status == HTTP_RETURN_CODE_URL_INVALID:
            if create_file:
                os.remove(file_path)
            return {"status": 0, "code": -1}
        # 超过重试次数，直接退出
        elif response.status == HTTP_RETURN_CODE_RETRY:
            if create_file:
                os.remove(file_path)
            return {"status": 0, "code": -2}
        # 500锡类错误，重试
        elif response.status in [500, 502, 503, 504]:
            pass
        # 其他http code，退出
        else:
            if create_file:
                os.remove(file_path)
            return {"status": 0, "code": response.status}
    if create_file:
        os.remove(file_path)
    return {"status": 0, "code": -3}


# 保存网络文件列表（多个URL的内容按顺序写入一个文件）
# file_url 文件所在网址
# file_path 文件所在本地路径，包括路径和文件名
# return
#       status: 0：失败，1：成功,
#       code:   -1：无法访问（没有获得返回，可能是域名无法解析，请求被直接丢弃，地址被墙等）
#               -2：下载失败（访问没有问题，但下载后与源文件大小不一致，网络问题）
#               > 0：访问出错，对应url的http code
def save_net_file_list(file_url_list, file_path, header_list=None):
    file_path = tool.change_path_encoding(file_path)
    # 判断保存目录是否存在
    if not tool.make_dir(os.path.dirname(file_path), 0):
        return False
    for retry_count in range(0, 5):
        # 下载
        with open(file_path, "wb") as file_handle:
            for file_url in file_url_list:
                response = http_request(file_url, header_list=header_list, read_timeout=60)
                if response.status == HTTP_RETURN_CODE_SUCCEED:
                    file_handle.write(response.data)
                # 超过重试次数，直接退出
                elif response.status == HTTP_RETURN_CODE_RETRY:
                    os.remove(file_path)
                    return {"status": 0, "code": -1}
                # 其他http code，退出
                else:
                    os.remove(file_path)
                    return {"status": 0, "code": response.status}
        return {"status": 1, "code": 0}
    # os.remove(file_path)
    return {"status": 0, "code": -2}
