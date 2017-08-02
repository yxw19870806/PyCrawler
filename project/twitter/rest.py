# -*- coding:UTF-8  -*-
"""
Twitter REST API
https://dev.twitter.com/rest/reference
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import os
import sys

API_HOST = "https://api.twitter.com"
API_VERSION = "1.1"
ACCESS_TOKEN = None


def get_access_token(api_key, api_secret):
    auth_url = API_HOST + "/oauth2/token"
    header_list = {
        "Authorization": "Basic %s" % base64.b64encode("%s:%s" % (api_key, api_secret)),
        "Content-Type": 'application/x-www-form-urlencoded;charset=UTF-8.',
    }
    post_data = {
        "grant_type": "client_credentials"
    }
    response = net.http_request(auth_url, method="POST", header_list=header_list, post_data=post_data, json_decode=True)
    if response.status == net.HTTP_RETURN_CODE_SUCCEED and robot.check_sub_key(("token_type", "access_token"), response.json_data) and response.json_data["token_type"] == "bearer":
        global ACCESS_TOKEN
        ACCESS_TOKEN = response.json_data["access_token"]
        return True
    return False


def _get_api_url(end_point):
    return "%s/%s/%s" % (API_HOST, API_VERSION, end_point)


# 根据user_id获取用户信息
def get_user_info_by_user_id(user_id):
    api_url = _get_api_url("users/show.json")
    api_url += "?user_id=%s" % user_id
    header_list = {
        "Authorization": "Bearer %s" % ACCESS_TOKEN,
    }
    response = net.http_request(api_url, method="GET", header_list=header_list, json_decode=True)
    if response.status == net.HTTP_RETURN_CODE_SUCCEED:
        return response.json_data
    return {}


if ACCESS_TOKEN is None:
    while True:
        api_info = tool.read_file(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "token.data"))
        if api_info:
            api_info = base64.b64decode(api_info)
            if robot.check_sub_key(("api_key", "api_secret"), api_info):
                if get_access_token(api_info["api_key"], api_info["api_secret"]):
                    break
        print "access token获取失败"
