# -*- coding:UTF-8  -*-
# 获取指定存档文件中是否存在重复的主键
import os


# 存档路径
SAVE_FILE_PATH = os.path.join("save.data")
# 存档中唯一标示（如，账号id）的字段下标
NAME_COLUMN = 0


# 检测存档文件中是否有相同的主键
def check_is_repeat():
    file_handle = open(SAVE_FILE_PATH, "r")
    lines = file_handle.readlines()
    file_handle.close()
    history = []
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        if temp_list[NAME_COLUMN] in history:
            print temp_list[NAME_COLUMN]
        else:
            history.append(temp_list[NAME_COLUMN])
    return history


if __name__ == "__main__":
    check_is_repeat()
