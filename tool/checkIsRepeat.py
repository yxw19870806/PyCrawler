# -*- coding:UTF-8  -*-
# 获取指定存档文件中是否存在重复的主键
import os


def check_repeat(file_path, name_col=0):
    file_handle = open(file_path, "r")
    lines = file_handle.readlines()
    file_handle.close()
    member = []
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        if temp_list[name_col] in member:
            print temp_list[name_col]
        else:
            member.append(temp_list[name_col])
    return member


if __name__ == "__main__":
    # 存档路径
    SAVE_FILE_PATH = os.path.join("save.data")
    # 存档中唯一标示（如，账号id）的字段下标
    NAME_COLUMN = 0

    check_repeat(SAVE_FILE_PATH, NAME_COLUMN)
