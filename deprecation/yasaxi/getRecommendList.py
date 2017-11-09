# -*- coding:UTF-8  -*-
"""
看了又看APP全推荐账号获取
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import yasaxiCommon


# 获取存档文件
def get_account_from_save_data(file_path):
    account_list = {}
    for line in tool.read_file(file_path, 2):
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


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
        raise robot.RobotException(robot.get_http_request_failed_reason(api_response.status))
    if not robot.check_sub_key(("data",), api_response.json_data):
        raise robot.RobotException("返回信息'data'字段不存在\n%s" % api_response.json_data)
    for account_info in api_response.json_data["data"]:
        if not robot.check_sub_key(("userId",), account_info):
            raise robot.RobotException("账号信息'userId'字段不存在\n%s" % account_info)
        if not robot.check_sub_key(("nick",), account_info):
            raise robot.RobotException("账号信息'nick'字段不存在\n%s" % account_info)
        account_list[str(account_info["userId"].encode("UTF-8"))] = str(robot.filter_emoji(account_info["nick"]).encode("UTF-8")).strip()
    return account_list


def main():
    if yasaxiCommon.get_token_from_file():
        config = robot.read_config(tool.PROJECT_CONFIG_PATH)
        # 存档位置
        save_data_path = robot.analysis_config(config, "SAVE_DATA_PATH", "\\\\info/save.data", robot.CONFIG_ANALYSIS_MODE_PATH)
        try:
            account_list_from_api = get_account_from_api()
        except robot.RobotException, e:
            output.print_msg("推荐账号解析失败，原因：%s" % e.message)
            raise
        if len(account_list_from_api) > 0:
            account_list_from_save_data = get_account_from_save_data(save_data_path)
            for account_id in account_list_from_api:
                if account_id not in account_list_from_save_data:
                    account_list_from_save_data[account_id] = "%s\t\t%s" % (account_id, account_list_from_api[account_id])
            temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
            tool.write_file(tool.list_to_string(temp_list, "\n", ""), save_data_path, 2)

if __name__ == "__main__":
    main()
