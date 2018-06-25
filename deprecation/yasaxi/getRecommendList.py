# -*- coding:UTF-8  -*-
"""
看了又看APP全推荐账号获取
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import yasaxiCommon


# 调用推荐API获取全部推荐账号
def get_account_from_api():
    api_url = "https://api.yasaxi.com/users/recommend"
    query_data = {"tag": ""}
    header_list = {
        "x-auth-token": yasaxiCommon.AUTH_TOKEN,
        "x-zhezhe-info": yasaxiCommon.ZHEZHE_INFO
    }
    account_list = {}
    api_response = net.http_request(api_url, method="GET", fields=query_data, header_list=header_list, json_decode=True)
    if api_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(api_response.status))
    if not crawler.check_sub_key(("data",), api_response.json_data):
        raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % api_response.json_data)
    for account_info in api_response.json_data["data"]:
        if not crawler.check_sub_key(("userId",), account_info):
            raise crawler.CrawlerException("账号信息'userId'字段不存在\n%s" % account_info)
        if not crawler.check_sub_key(("nick",), account_info):
            raise crawler.CrawlerException("账号信息'nick'字段不存在\n%s" % account_info)
        account_list[str(account_info["userId"].encode("UTF-8"))] = str(crawler.filter_emoji(account_info["nick"]).encode("UTF-8")).strip()
    return account_list


def main():
    if not yasaxiCommon.get_token_from_file():
        while True:
            input_str = output.console_input("未检测到api token，是否手动输入(y)es / (N)o：").lower()
            if input_str in ["y", "yes"]:
                yasaxiCommon.set_token_to_file()
                break
            elif input_str in ["n", "no"]:
                return

    # 存档位置
    save_data_path = crawler.quickly_get_save_data_path()
    try:
        account_list_from_api = get_account_from_api()
    except crawler.CrawlerException, e:
        output.print_msg("推荐账号解析失败，原因：%s" % e.message)
        raise
    if len(account_list_from_api) > 0:
        account_list_from_save_data = crawler.read_save_data(save_data_path, 0, [])
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t%s" % (account_id, account_list_from_api[account_id])
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file("\n".join(temp_list), save_data_path, tool.WRITE_FILE_TYPE_REPLACE)

if __name__ == "__main__":
    main()
