# -*- coding:UTF-8  -*-
"""
微博公共方法
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *

COOKIE_INFO = {"SUB": ""}


# 检测登录状态
def check_login():
    if "SUB" not in COOKIE_INFO or not COOKIE_INFO["SUB"]:
        return False
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    index_url = "https://weibo.com/"
    index_response = net.http_request(index_url, method="GET", cookies_list=cookies_list)
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        return index_response.data.find("$CONFIG['islogin']='1';") >= 0
    return False


# 使用浏览器保存的cookie模拟登录请求，获取一个session级别的访问cookie
def init_session():
    login_url = "https://login.sina.com.cn/sso/login.php"
    query_data = {"url": "https://weibo.com"}
    login_response = net.http_request(login_url, method="GET", fields=query_data, cookies_list=COOKIE_INFO)
    if login_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        COOKIE_INFO.update(net.get_cookies_from_response_header(login_response.headers))
        return True
    return False


# 获取账号首页
def get_account_index_page(account_id):
    account_index_url = "https://weibo.com/u/%s" % account_id
    cookies_list = {"SUB": tool.generate_random_string(30)}
    result = {
        "account_page_id": None,  # 页面解析出的账号page id
    }
    account_index_response = net.http_request(account_index_url, method="GET", cookies_list=cookies_list)
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取账号page id
        account_page_id = tool.find_sub_string(account_index_response.data, "$CONFIG['page_id']='", "'")
        if not crawler.is_integer(account_page_id):
            raise crawler.CrawlerException("账号不存在")
        result["account_page_id"] = account_page_id
    else:
        raise crawler.CrawlerException(crawler.request_failre(account_index_response.status))
    return result


# 检测图片是不是被微博自动删除的文件
def check_image_invalid(file_path):
    file_md5 = tool.get_file_md5(file_path)
    if file_md5 in ["14f2559305a6c96608c474f4ca47e6b0", "37b9e6dec174b68a545c852c63d4645a", "7bd88df2b5be33e1a79ac91e7d0376b5"]:
        return True
    return False
