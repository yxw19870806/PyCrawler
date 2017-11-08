# -*- coding:UTF-8  -*-
"""
网络访问类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""

from common import output, path, process, tool
import json
import os
import random
import ssl
import time
import traceback
import urllib3

HTTP_CONNECTION_POOL = None
HTTP_CONNECTION_TIMEOUT = 10
HTTP_REQUEST_RETRY_COUNT = 10
# https://www.python.org/dev/peps/pep-0476/
# disable urllib3 HTTPS warning
urllib3.disable_warnings()
# disable URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:590)>
ssl._create_default_https_context = ssl._create_unverified_context

HTTP_RETURN_CODE_RETRY = 0
HTTP_RETURN_CODE_URL_INVALID = -1  # 地址不符合规范（非http:// 或者 https:// 开头）
HTTP_RETURN_CODE_JSON_DECODE_ERROR = -2  # 返回数据不是JSON格式，但返回状态是200
HTTP_RETURN_CODE_DOMAIN_NOT_RESOLVED = -3  # 域名无法解析
HTTP_RETURN_CODE_EXCEPTION_CATCH = -10
HTTP_RETURN_CODE_SUCCEED = 200


class ErrorResponse(object):
    """Default http_request() response object(exception return)"""
    def __init__(self, status=-1):
        self.status = status
        self.data = None
        self.headers = {}
        self.json_data = []


def init_http_connection_pool():
    """init urllib3 connection pool"""
    global HTTP_CONNECTION_POOL
    HTTP_CONNECTION_POOL = urllib3.PoolManager(retries=False)


def set_proxy(ip, port):
    """init urllib3 proxy connection pool"""
    global HTTP_CONNECTION_POOL
    HTTP_CONNECTION_POOL = urllib3.ProxyManager("http://%s:%s" % (ip, port), retries=False)
    output.print_msg("设置代理成功")


def build_header_cookie_string(cookies_list):
    """generate cookies string for http request header

    :param cookies_list:
        {
            "cookie1":“value1",
            "cookie2":“value2"
        }

    :return:
        cookie1=value1; cookie2=value2
    """
    if not cookies_list:
        return ""
    temp_string = []
    for cookie_name in cookies_list:
        temp_string.append(cookie_name + "=" + cookies_list[cookie_name])
    return "; ".join(temp_string)


def get_cookies_from_response_header(response_headers):
    """Get dictionary of cookies values from http response header list"""
    if not isinstance(response_headers, urllib3._collections.HTTPHeaderDict):
        return {}
    if "Set-Cookie" not in response_headers:
        return {}
    cookies_list = {}
    for cookie in response_headers.getlist("Set-Cookie"):
        cookie_name, cookie_value = cookie.split(";")[0].split("=", 1)
        cookies_list[cookie_name] = cookie_value
    return cookies_list


def http_request(url, method="GET", fields=None, binary_data=None, header_list=None, cookies_list=None, encode_multipart=False, redirect=True,
                 connection_timeout=HTTP_CONNECTION_TIMEOUT, read_timeout=HTTP_CONNECTION_TIMEOUT, is_random_ip=True, json_decode=False):
    """Http request via urllib3

    :param url:
        the url which you want visit, start with "http://" or "https://"

    :param method:
        request method, value in ["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE"]

    :param fields:
        dictionary type of request data, will urlencode() them to string. like post data, query string, etc
        not work with binary_data

    :param binary_data:
        binary type of request data, not work with post_data

    :param header_list:
        customize header dictionary

    :param cookies_list:
        customize cookies dictionary, will replaced header_list["Cookie"]

    :param encode_multipart:
        see "encode_multipart" in urllib3.request_encode_body

    :param redirect:
        is auto redirect, when response.status in [301, 302, 303, 307, 308]

    :param connection_timeout:
        customize connection timeout seconds

    :param read_timeout:
        customize read timeout seconds

    :param is_random_ip:
        is counterfeit a request header with random ip, will replaced header_list["X-Forwarded-For"] and header_list["X-Real-Ip"]

    :param json_decode:
        is return a decoded json data when response status = 200
        if decode failure will replace response status with HTTP_RETURN_CODE_JSON_DECODE_ERROR
    """
    if not (url.find("http://") == 0 or url.find("https://") == 0):
        return ErrorResponse(HTTP_RETURN_CODE_URL_INVALID)
    method = method.upper()
    if method not in ["GET", "POST", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE"]:
        return ErrorResponse(HTTP_RETURN_CODE_URL_INVALID)
    if HTTP_CONNECTION_POOL is None:
        init_http_connection_pool()

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

    # 超时设置
    if connection_timeout == 0 and read_timeout == 0:
        timeout = None
    elif connection_timeout == 0:
        timeout = urllib3.Timeout(read=read_timeout)
    elif read_timeout == 0:
        timeout = urllib3.Timeout(connect=connection_timeout)
    else:
        timeout = urllib3.Timeout(connect=connection_timeout, read=read_timeout)

    retry_count = 0
    while True:
        while process.PROCESS_STATUS == process.PROCESS_STATUS_PAUSE:
            time.sleep(10)
        if process.PROCESS_STATUS == process.PROCESS_STATUS_STOP:
            tool.process_exit(0)

        try:
            if method in ['DELETE', 'GET', 'HEAD', 'OPTIONS']:
                response = HTTP_CONNECTION_POOL.request(method, url, headers=header_list, redirect=redirect, timeout=timeout, fields=fields)
            else:
                if binary_data is None:
                    response = HTTP_CONNECTION_POOL.request(method, url, headers=header_list, redirect=redirect, timeout=timeout, fields=fields, encode_multipart=encode_multipart)
                else:
                    response = HTTP_CONNECTION_POOL.request(method, url, headers=header_list, redirect=redirect, timeout=timeout, body=binary_data, encode_multipart=encode_multipart)
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
            elif response.status in [500, 502, 503, 504]:  # 服务器临时性错误，重试
                retry_count += 1
                continue
            return response
        except urllib3.exceptions.ProxyError:
            notice = "无法访问代理服务器，请检查代理设置。检查完成后输入(C)ontinue继续程序或者(S)top退出程序："
            input_str = output.console_input(notice).lower()
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
        except Exception, e:
            if str(e).find("EOF occurred in violation of protocol") >=0:
                time.sleep(30)
            output.print_msg(str(e))
            output.print_msg(url + " 访问超时，稍后重试")
            traceback.print_exc()

        retry_count += 1
        if retry_count >= HTTP_REQUEST_RETRY_COUNT:
            output.print_msg("无法访问页面：" + url)
            return ErrorResponse(HTTP_RETURN_CODE_RETRY)


def _random_user_agent():
    """Get a random valid Firefox or Chrome user agent

        Common firefox user agent   "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0"
        Common chrome user agent    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    """
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


def _random_ip_address():
    """Get a random IP address(not necessarily correct)"""
    return "%s.%s.%s.%s" % (random.randint(1, 254), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


def save_net_file(file_url, file_path, need_content_type=False, header_list=None, cookies_list=None):
    """Visit web and save to local

    :param file_url:
        the remote resource URL which you want to save

    :param file_path:
        the local file path which you want to save remote resource

    :param need_content_type:
        is auto rename file according to "Content-Type" in response headers

    :param header_list:
        customize header dictionary

    :param cookies_list:
        customize cookies dictionary, will replaced header_list["Cookie"]

    :return:
        status      0 download failure, 1 download successful
        code        failure reason
        file_path   finally local file path(when need_content_type is True, will rename it)
    """
    file_path = path.change_path_encoding(file_path)
    # 判断保存目录是否存在
    if not path.create_dir(os.path.dirname(file_path)):
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
                output.print_msg("本地文件%s：%s和网络文件%s：%s不一致" % (file_path, content_length, file_url, file_size))
        elif response.status == HTTP_RETURN_CODE_URL_INVALID:
            if create_file:
                path.delete_dir_or_file(file_path)
            return {"status": 0, "code": -1}
        # 超过重试次数，直接退出
        elif response.status == HTTP_RETURN_CODE_RETRY:
            if create_file:
                path.delete_dir_or_file(file_path)
            return {"status": 0, "code": -2}
        # 其他http code，退出
        else:
            if create_file:
                path.delete_dir_or_file(file_path)
            return {"status": 0, "code": response.status}
    if create_file:
        path.delete_dir_or_file(file_path)
    return {"status": 0, "code": -3}


def save_net_file_list(file_url_list, file_path, header_list=None, cookies_list=None):
    """Visit web and save to local(multiple remote resource, single local file)

    :param file_url_list:
        the list of remote resource URL which you want to save

    :param file_path:
        the local file path which you want to save remote resource

    :param header_list:
        customize header dictionary

    :param cookies_list:
        customize cookies dictionary, will replaced header_list["Cookie"]

    :return:
        status      0 download failure, 1 download successful
        code        failure reason
    """
    file_path = path.change_path_encoding(file_path)
    # 判断保存目录是否存在
    if not path.create_dir(os.path.dirname(file_path)):
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
                    path.delete_dir_or_file(file_path)
                    return {"status": 0, "code": -1}
                # 其他http code，退出
                else:
                    path.delete_dir_or_file(file_path)
                    return {"status": 0, "code": response.status}
        return {"status": 1, "code": 0}
    # path.delete_dir_or_file(file_path)
    return {"status": 0, "code": -2}
