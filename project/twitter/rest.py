# -*- coding:UTF-8  -*-
"""
Twitter REST API
https://dev.twitter.com/rest/reference
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import base64
import json
import os
from common import *

API_HOST = "https://api.twitter.com"
API_VERSION = "1.1"
ACCESS_TOKEN = None
token_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "info\\session"))


def init():
    # 设置代理
    crawler.quickly_set_proxy()

    if ACCESS_TOKEN is not None:
        return True

    # 文件存在，检查格式是否正确
    if os.path.exists(token_file_path):
        api_info = tool.json_decode(tool.decrypt_string(tool.read_file(token_file_path)), [])
        if crawler.check_sub_key(("api_key", "api_secret"), api_info):
            # 验证token是否有效
            if get_access_token(api_info["api_key"], api_info["api_secret"]):
                output.print_msg("access token get succeed!")
                return True
            else:
                output.print_msg("api info has expired")
        else:
            output.print_msg("decrypt api info failure")
        # token已经无效了，删除掉
        path.delete_dir_or_file(token_file_path)
    output.print_msg("Please input api info")
    while True:
        api_key = output.console_input("API KEY: ")
        api_secret = output.console_input("API SECRET; ")
        # 验证token是否有效
        if get_access_token(api_key, api_secret):
            # 加密保存到文件中
            if not os.path.exists(token_file_path):
                api_info = tool.encrypt_string(json.dumps({"api_key": api_key, "api_secret": api_secret}))
                tool.write_file(api_info, token_file_path, tool.WRITE_FILE_TYPE_REPLACE)
            output.print_msg("access token get succeed!")
            return True
        output.print_msg("incorrect api info, please type again!")
    return False


def get_access_token(api_key, api_secret):
    auth_url = API_HOST + "/oauth2/token"
    header_list = {
        "Authorization": "Basic %s" % base64.b64encode("%s:%s" % (api_key, api_secret)),
        "Content-Type": 'application/x-www-form-urlencoded;charset=UTF-8.',
    }
    post_data = {
        "grant_type": "client_credentials"
    }
    response = net.http_request(auth_url, method="POST", header_list=header_list, fields=post_data, json_decode=True)
    if (
        response.status == net.HTTP_RETURN_CODE_SUCCEED and
        crawler.check_sub_key(("token_type", "access_token"), response.json_data) and
        response.json_data["token_type"] == "bearer"
    ):
        global ACCESS_TOKEN
        ACCESS_TOKEN = response.json_data["access_token"]
        return True
    return False


def _get_api_url(end_point):
    return "%s/%s/%s" % (API_HOST, API_VERSION, end_point)


# 根据user_id获取用户信息
def get_user_info_by_user_id(user_id):
    api_url = _get_api_url("users/show.json")
    query_data = {"user_id": user_id}
    header_list = {"Authorization": "Bearer %s" % ACCESS_TOKEN}
    response = net.http_request(api_url, method="GET", fields=query_data, header_list=header_list, json_decode=True)
    if response.status == net.HTTP_RETURN_CODE_SUCCEED:
        return response.json_data
    return {}


# 关注指定用户
def follow_account(user_id):
    api_url = _get_api_url("friendships/create.json")
    api_url += "?user_id=%s" % user_id
    header_list = {
        "Authorization": "Bearer %s" % ACCESS_TOKEN,
    }
    response = net.http_request(api_url, method="POST", header_list=header_list, json_decode=True)
    if response.status == net.HTTP_RETURN_CODE_SUCCEED:
        pass
    return False

init()
