# -*- coding:UTF-8  -*-
"""
http://www.miaopai.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import re
from common import *


# 获取指定账号的全部关注列表
# suid -> 0r9ewgQ0v7UoDptu
def get_follow_list(suid):
    page_count = 1
    follow_list = {}
    while True:
        follow_pagination_url = "http://www.miaopai.com/gu/follow"
        query_data = {
            "page": page_count,
            "suid": suid,
        }
        follow_pagination_response = net.http_request(follow_pagination_url, method="GET", fields=query_data, json_decode=True)
        if follow_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if crawler.check_sub_key(("msg", "stat"), follow_pagination_response.json_data) and follow_pagination_response.json_data["stat"].isdigit():
                stat = int(follow_pagination_response.json_data["stat"]["stat"])
                if stat == 1 or stat == 2:
                    one_page_follow_list = re.findall('<a title="([^"]*)" href="http://www.miaopai.com/u/paike_([^"]*)">', follow_pagination_response.json_data["msg"])
                    for account_name, account_id in one_page_follow_list:
                        follow_list[account_id] = account_name
                    if stat == 1:
                        page_count += 1
                        continue
        return follow_list
