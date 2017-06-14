# -*- coding:UTF-8  -*-
# 获取指定存档文件中所有毕业成员的名字

def get_member_list():
    file_handle = open("member.txt", "r")
    lines = file_handle.readlines()
    file_handle.close()
    member = []
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        member.append(temp_list[0])
    return member


def get_save_file_name_list(file_path, name_col):
    file_handle = open(file_path, "r")
    lines = file_handle.readlines()
    file_handle.close()
    member = []
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        member.append(temp_list[name_col])
    return member


if __name__ == "__main__":
    member_list = get_member_list()
    save_file_account_name_list = get_save_file_name_list("save.data", 4)
    for account_name in save_file_account_name_list:
        if account_name not in member_list:
            print account_name