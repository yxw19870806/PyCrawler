# -*- coding:UTF-8  -*-
# 获取指定存档文件中全部毕业成员的名字
import os
from common import output, tool

# 存档路径
SAVE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "save.data"))
# 存档中记录成员名字的字段下标
NAME_COLUMN = 4


# 从现役成员名单中获取全部成员名字（由get48GroupMember.py生成）
def get_member_list():
    member = []
    for line in tool.read_file("member.txt", tool.READ_FILE_TYPE_LINE):
        temp_list = line.replace("\n", "").split("\t")
        member.append(temp_list[0])
    return member


# 从存档文件中获取全部名字（NAME_COLUMN对应的名字必须和从官网获取的成员本名一致）
def get_save_file_name_list():
    member = []
    for line in tool.read_file(SAVE_FILE_PATH, tool.READ_FILE_TYPE_LINE):
        temp_list = line.replace("\n", "").split("\t")
        member.append(temp_list[NAME_COLUMN])
    return member


def check_is_graduation():
    member_list = get_member_list()
    save_file_account_name_list = get_save_file_name_list()
    for account_name in save_file_account_name_list:
        if account_name not in member_list:
            output.print_msg(account_name)


if __name__ == "__main__":
    check_is_graduation()
