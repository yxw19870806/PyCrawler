# -*- coding:UTF-8  -*-
"""
グラドル自画撮り部 已下载文件中提取全部成员账号
http://jigadori.fkoji.com/users
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import os

# Twitter存档文件目录
SAVE_DATA_PATH = os.path.join(tool.PROJECT_APP_PATH, "twitter/info/save_5.data")
# 图片下载后的保存目录
FILE_STORAGE_PATH = os.path.join("photo")


# 获取存档文件
def get_account_from_save_data():
    account_list = {}
    if not os.path.exists(SAVE_DATA_PATH):
        return account_list
    for line in tool.read_file(SAVE_DATA_PATH, tool.READ_FILE_TYPE_LINE):
        line = line.replace("\n", "")
        account_info_temp = line.split("\t")
        account_list[account_info_temp[0]] = line
    return account_list


# 从存档目录获取去重后的账号名字
def get_account_from_storage():
    account_list = {}
    for root_path, dir_name_list, file_name_list in os.walk(FILE_STORAGE_PATH):
        for file_name in file_name_list:
            count, account_name = file_name.split(".")[0].split("_", 1)
            account_list[account_name] = 1
    return account_list


def main():
    account_list_from_storage = get_account_from_storage()
    if len(account_list_from_storage) > 0:
        account_list_from_save_data = get_account_from_save_data()
        for account_id in account_list_from_storage:
            if account_id not in account_list_from_save_data:
                account_list_from_save_data[account_id] = "%s\t\t\t\t\t" % account_id
        temp_list = [account_list_from_save_data[key] for key in sorted(account_list_from_save_data.keys())]
        tool.write_file(tool.list_to_string(temp_list, "\n", ""), SAVE_DATA_PATH, 2)


if __name__ == "__main__":
    main()
