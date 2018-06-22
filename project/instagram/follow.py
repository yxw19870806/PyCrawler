# -*- coding:UTF-8  -*-
"""
Instagram批量关注
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import time
from common import *

COOKIE_INFO = {}
IS_FOLLOW_PRIVATE_ACCOUNT = False  # 是否对私密账号发出关注请求


# 获取账号首页
def get_account_index_page(account_name):
    account_index_url = "https://www.instagram.com/%s" % account_name
    account_index_response = net.http_request(account_index_url, method="GET", cookies_list=COOKIE_INFO)
    result = {
        "is_follow": False,  # 是否已经关注
        "is_private": False,  # 是否是私密账号
        "account_id": None,  # account id
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取账号id
        account_id = tool.find_sub_string(account_index_response.data, '"profilePage_', '"')
        if not crawler.is_integer(account_id):
            raise crawler.CrawlerException("页面截取账号id失败\n%s" % account_index_response.data)
        result["account_id"] = account_id
        # 判断是不是已经关注
        result["is_follow"] = tool.find_sub_string(account_index_response.data, '"followed_by_viewer": ', ",") == "true"
        # 判断是不是私密账号
        result["is_private"] = tool.find_sub_string(account_index_response.data, '"is_private": ', ",") == "true"
    elif account_index_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    else:
        raise crawler.CrawlerException(crawler.request_failre(account_index_response.status))
    return result


# 关注指定账号
def follow_account(account_name, account_id):
    follow_api_url = "https://www.instagram.com/web/friendships/%s/follow/" % account_id
    header_list = {"Referer": "https://www.instagram.com/", "x-csrftoken": COOKIE_INFO["csrftoken"], "X-Instagram-AJAX": 1}
    follow_response = net.http_request(follow_api_url, method="POST", header_list=header_list, cookies_list=COOKIE_INFO, json_decode=True)
    if follow_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if not crawler.check_sub_key(("status", "result"), follow_response.json_data):
            output.print_msg(crawler.CrawlerException("关注%s失败，返回内容不匹配\n%s" % (account_name, follow_response.json_data)))
            tool.process_exit()
        if follow_response.json_data["result"] == "following":
            output.print_msg("关注%s成功" % account_name)
            return True
        elif follow_response.json_data["result"] == "requested":
            output.print_msg("私密账号%s，已发送关注请求" % account_name)
            return True
        else:
            return False
    elif follow_response.status == 403 and follow_response.data == "Please wait a few minutes before you try again.":
        output.print_msg(crawler.CrawlerException("关注%s失败，连续关注太多等待一会儿继续尝试" % account_name))
        tool.process_exit()
    else:
        output.print_msg(crawler.CrawlerException("关注%s失败，请求返回结果：%s" % (account_name, crawler.request_failre(follow_response.status))))
        tool.process_exit()


def main():
    config = crawler.read_config(tool.PROJECT_CONFIG_PATH)
    # 获取cookies
    all_cookie_from_browser = crawler.quickly_get_all_cookies_from_browser(config)
    if "www.instagram.com" in all_cookie_from_browser:
        for cookie_key in all_cookie_from_browser["www.instagram.com"]:
            COOKIE_INFO[cookie_key] = all_cookie_from_browser["www.instagram.com"][cookie_key]
    else:
        output.print_msg("没有检测到登录信息")
        tool.process_exit()
    # 设置代理
    crawler.quickly_set_proxy(config)
    # 存档位置
    save_data_path = crawler.quickly_get_save_data_path(config)
    # 读取存档文件
    account_list = crawler.read_save_data(save_data_path, 0, [""])

    count = 0
    for account_name in sorted(account_list.keys()):
        try:
            account_index_response = get_account_index_page(account_name)
        except crawler.CrawlerException, e:
            log.error(account_name + " 首页解析失败，原因：%s" % e.message)
            continue

        if account_index_response["is_follow"]:
            output.print_msg("%s已经关注，跳过" % account_name)
        elif account_index_response["is_private"] and not IS_FOLLOW_PRIVATE_ACCOUNT:
            output.print_msg("%s是私密账号，跳过" % account_name)
        else:
            if follow_account(account_name, account_index_response["account_id"]):
                count += 1
            time.sleep(0.1)

    output.print_msg("关注完成，成功关注了%s个账号" % count)

if __name__ == "__main__":
    main()
