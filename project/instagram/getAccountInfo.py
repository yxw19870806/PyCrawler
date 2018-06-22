# -*- coding:UTF-8  -*-
"""
Instagram批量获取账号介绍
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
from common import *


# 获取账号首页
def get_account_index_page(account_name):
    account_index_url = "https://www.instagram.com/%s/" % account_name
    account_index_response = net.http_request(account_index_url, method="GET")
    result = {
        "account_info": "",  # 自我介绍
        "external_url": "",  # 外部链接地址
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取账号信息
        if account_index_response.data.find('"biography": null,') >= 0:
            result["account_info"] = ""
        else:
            account_info = tool.find_sub_string(account_index_response.data, '"biography": "', '"')
            if not account_info:
                raise crawler.CrawlerException("页面截取账号信息失败\n%s" % account_index_response.data)
            account_info = account_info.replace(r"\n", "").replace("'", chr(1))
            result["account_info"] = eval("u'%s'" % account_info).replace(chr(1), "'").encode("UTF-8")
        # 获取外部链接地址
        if account_index_response.data.find('"external_url": null,') >= 0:
            result["external_url"] = ""
        else:
            result["external_url"] = tool.find_sub_string(account_index_response.data, '"external_url": "', '"')
    elif account_index_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    else:
        raise crawler.CrawlerException(crawler.request_failre(account_index_response.status))
    return result


def main():
    config = crawler.read_config(tool.PROJECT_CONFIG_PATH)
    # 存档位置
    save_data_path = crawler.quickly_get_save_data_path(config)
    # 读取存档文件
    account_list = crawler.read_save_data(save_data_path, 0, [""])
    # 设置代理
    crawler.quickly_set_proxy(config)

    result_file_path = os.path.join(os.path.dirname(__file__), "info/account_info.data")
    for account in sorted(account_list.keys()):
        try:
            account_index_response = get_account_index_page(account)
        except crawler.CrawlerException, e:
            output.print_msg(account + "解析信息失败，原因：%s" % "")
            continue
        tool.write_file("%s\t%s\t%s" % (account, account_index_response["account_info"], account_index_response["external_url"]), result_file_path)

if __name__ == "__main__":
    main()
