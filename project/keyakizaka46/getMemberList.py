# -*- coding:UTF-8  -*-
"""
欅坂46公式ブログ成员id获取
http://www.keyakizaka46.com/mob/news/diarShw.php?cd=member
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import net, robot, tool
import re


# 获取存档文件
def get_account_from_save_data(file_path):
    account_list = {}
    for line in tool.read_file(file_path, 2):
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


# 从页面获取全部成员账号
def get_account_from_index():
    index_url = "http://www.keyakizaka46.com/mob/news/diarShw.php"
    query_data = {"cd": "member"}
    index_response = net.http_request(index_url, method="GET", fields=query_data)
    account_list = {}
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(index_response.status))
    member_list_data = tool.find_sub_string(index_response.data, '<ul class="thumb">', "</ul>")
    if not member_list_data:
        raise robot.RobotException("页面截取账号列表失败\n%s" % index_response.data)
    member_list_find = re.findall("<li ([\S|\s]*?)</li>", member_list_data)
    for member_info in member_list_find:
        # 获取账号id
        account_id = tool.find_sub_string(member_info, "&ct=", '">')
        if not account_id:
            raise robot.RobotException("账号信息截取账号id失败\n%s" % member_info)
        # 获取成员名字
        account_name = tool.find_sub_string(member_info, '<p class="name">', "</p>").strip().replace(" ", "")
        if not account_name:
            raise robot.RobotException("账号信息截取成员名字失败\n%s" % member_info)
        account_list[account_id] = account_name
    return account_list


def main():
    config = robot.read_config(tool.PROJECT_CONFIG_PATH)
    # 存档位置
    save_data_path = robot.analysis_config(config, "SAVE_DATA_PATH", "\\\\info/save.data", robot.CONFIG_ANALYSIS_MODE_PATH)
    account_list_from_api = get_account_from_index()
    if len(account_list_from_api) > 0:
        account_list_from_save_data = get_account_from_save_data(save_data_path)
        for account_id in account_list_from_api:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t\t%s" % (account_id, account_list_from_api[account_id])
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list, "\n", ""), save_data_path, 2)


if __name__ == "__main__":
    main()
