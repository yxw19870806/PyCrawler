# -*- coding:UTF-8  -*-
"""
看了又看APP全推荐账号获取
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *


AUTH_TOKEN = ""
ZHEZHE_INFO = ""


def get_recommend():
    api_url = "https://api.yasaxi.com/users/recommend?tag="
    header_list = {
        "x-auth-token": AUTH_TOKEN,
        "x-zhezhe-info": ZHEZHE_INFO,
    }
    api_response = net.http_request(api_url, header_list=header_list, json_decode=True)
    if api_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("data",), api_response.json_data):
            for account_info in api_response.json_data["data"]:
                print "%s\t%s" % (str(account_info["userId"].encode("utf-8")), robot.filter_emoji(str(account_info["nick"].encode("utf-8")).strip()))

if __name__ == "__main__":
    get_recommend()