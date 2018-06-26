# -*- coding:UTF-8  -*-
"""
乃木坂46 OFFICIAL BLOG成员id获取
http://http://blog.nogizaka46.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import re
from common import *


# 从页面获取全部成员账号
def get_account_from_index():
    index_url = "http://blog.nogizaka46.com/"
    index_response = net.http_request(index_url, method="GET")
    account_list = {}
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        member_list_find = re.findall('<div class="unit"><a href="./([^"]*)"><img src="[^>]*alt="([^"]*)" />', index_response.data)
        if len(member_list_find) == 0:
            raise crawler.CrawlerException("页面截取成员类别失败\n%s" % index_response.data)
        for member_info in member_list_find:
            account_list[member_info[0]] = member_info[1].replace(" ", "")
    else:
        raise crawler.CrawlerException(crawler.request_failre(index_response.status))
    return account_list


def main():
    # 存档位置
    save_data_path = crawler.quickly_get_save_data_path()
    account_list_from_api = get_account_from_index()
    if len(account_list_from_api) > 0:
        account_list_from_save_data = crawler.read_save_data(save_data_path, 0, [])
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = [account_id, "", "", account_list_from_api[account_id]]
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list), save_data_path, tool.WRITE_FILE_TYPE_REPLACE)

if __name__ == "__main__":
    main()
