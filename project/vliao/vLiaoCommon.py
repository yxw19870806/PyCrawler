# -*- coding:UTF-8  -*-
"""
V聊视频爬虫
http://www.vliaoapp.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os

USER_ID = ""
USER_KEY = ""
API_VERSION = "31"
token_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "session"))


# 检查登录信息
def check_login():
    global USER_ID, USER_KEY
    # 文件存在，检查格式是否正确
    if os.path.exists(token_file_path):
        api_info = tool.json_decode(tool.decrypt_string(tool.read_file(token_file_path)))
        if crawler.check_sub_key(("user_id", "user_key"), api_info):
            # 验证token是否有效
            if check_token(api_info["user_id"], api_info["user_key"]):
                USER_ID = api_info["user_id"]
                USER_KEY = api_info["user_key"]
                return True
        # token已经无效了，删除掉
        path.delete_dir_or_file(token_file_path)
    log.step("Please input api info")
    while True:
        user_id = output.console_input("USER ID: ")
        user_key = output.console_input("USER KEY; ")
        # 验证token是否有效
        if check_token(user_id, user_key):
            USER_ID = user_id
            USER_KEY = user_key
            # 加密保存到文件中
            if not os.path.exists(token_file_path):
                api_info = tool.encrypt_string(json.dumps({"user_id": user_id, "user_key": user_key}))
                tool.write_file(api_info, token_file_path, tool.WRITE_FILE_TYPE_REPLACE)
            return True
        log.step("incorrect api info, please type again!")
    return False


# 验证user_id和user_key是否匹配
def check_token(user_id, user_key):
    index_url = "http://v3.vliao3.xyz/v%s/user/mydata" % API_VERSION
    post_data = {
        "userId": user_id,
        "userKey": user_key,
    }
    index_response = net.http_request(index_url, method="POST", fields=post_data, json_decode=True)
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if crawler.check_sub_key(("result",), index_response.json_data) and index_response.json_data["result"] is True:
            return True
    return False
