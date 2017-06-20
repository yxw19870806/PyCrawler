# -*- coding:UTF-8  -*-
# 获取指定存档文件中是否存在重复的主键


def check_repeat(file_path, name_col=0):
    file_handle = open(file_path, "r")
    lines = file_handle.readlines()
    file_handle.close()
    member = []
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        if temp_list[0] in member:
            print temp_list[0]
        else:
            member.append(temp_list[0])
    return member


if __name__ == "__main__":
    check_repeat("save.data")