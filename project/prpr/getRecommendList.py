# -*- coding:UTF-8  -*-
"""
PR社APP全推荐账号获取
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *


# 获取存档文件
def get_account_from_save_data(file_path):
    account_list = {}
    for line in tool.read_file(file_path, 2):
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


def get_channel_from_api():
    api_url = "https://api.prpr.tinydust.cn/v3/channels/user/channels"
    api_response = net.http_request(api_url, method="GET", json_decode=True)
    channel_list = []
    if api_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(api_response.status))
    if not robot.check_sub_key(("code",), api_response.json_data):
        raise robot.RobotException("返回信息'code'字段不存在\n%s" % api_response.json_data)
    if not robot.is_integer(api_response.json_data["code"]):
        raise robot.RobotException("返回信息'code'字段类型不正确\n%s" % api_response.json_data)
    if int(api_response.json_data["code"]) != 200:
        raise robot.RobotException("返回信息'code'字段取值不正确\n%s" % api_response.json_data)
    if not robot.check_sub_key(("result",), api_response.json_data):
        raise robot.RobotException("返回信息'result'字段不存在\n%s" % api_response.json_data)
    for channel_info in api_response.json_data["result"]:
        if not robot.check_sub_key(("_id",), channel_info):
            raise robot.RobotException("频道信息'_id'字段不存在\n%s" % channel_info)
        channel_list.append(str(channel_info["_id"]))
    return channel_list


# 调用推荐API获取全部推荐账号
def get_channel_account_from_api(channel_id):
    page_count = 1
    account_per_page = 50
    account_list = {}
    while True:
        api_url = "https://api.prpr.tinydust.cn/v3/channels/%s/girls" % channel_id
        query_data = {
            "page": page_count,
            "limit": account_per_page,
        }
        api_response = net.http_request(api_url, method="GET", fields=query_data, json_decode=True)
        if api_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException(robot.get_http_request_failed_reason(api_response.status))
        if not robot.check_sub_key(("code",), api_response.json_data):
            raise robot.RobotException("返回信息'code'字段不存在\n%s" % api_response.json_data)
        if not robot.is_integer(api_response.json_data["code"]):
            raise robot.RobotException("返回信息'code'字段类型不正确\n%s" % api_response.json_data)
        if int(api_response.json_data["code"]) != 200:
            raise robot.RobotException("返回信息'code'字段取值不正确\n%s" % api_response.json_data)
        if not robot.check_sub_key(("result",), api_response.json_data):
            raise robot.RobotException("返回信息'result'字段不存在\n%s" % api_response.json_data)
        if len(api_response.json_data["result"]) == 0:
            break
        for account_info in api_response.json_data["result"]:
            if not robot.check_sub_key(("_id",), account_info):
                raise robot.RobotException("返回信息'_id'字段不存在\n%s" % account_info)
            if not robot.check_sub_key(("nickname",), account_info):
                raise robot.RobotException("返回信息'result'字段不存在\n%s" % account_info)
            account_list[str(account_info["_id"])] = robot.filter_text(str(account_info["nickname"].encode("UTF-8")))
        page_count += 1
    return account_list


def main():
    config = robot.read_config(tool.PROJECT_CONFIG_PATH)
    # 存档位置
    save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "\\\\info/save.data", 3)
    try:
        channel_list = get_channel_from_api()
    except robot.RobotException, e:
        output.print_msg("频道列表解析失败，原因：%s" % e.message)
        raise

    account_list_from_api = {}
    for channel_id in channel_list:
        try:
            channel_account_list = get_channel_account_from_api(channel_id)
        except robot.RobotException, e:
            output.print_msg("频道%s推荐账号解析失败，原因：%s" % (channel_id, e.message))
            raise
        output.print_msg("频道%s获取推荐账号%s个" % (channel_id, len(channel_account_list)))
        # 累加账号
        account_list_from_api.update(channel_account_list)

    if len(account_list_from_api) > 0:
        account_list_from_save_data = get_account_from_save_data(save_data_path)
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t%s" % (account_id, account_list_from_api[account_id])
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list, "\n", ""), save_data_path, 2)


if __name__ == "__main__":
    main()
