# -*- coding:UTF-8  -*-
# 重新格式化存档，修改字段顺序
import os


# 旧存档路径
OLD_SAVE_FILE_PATH = os.path.join("save.data")
# 新存档路径
NEW_SAVE_FILE_PATH = os.path.join("new_save.data")


# 修改存档文件列的顺序并保存
def reformat_save():
    old_file_handle = open(OLD_SAVE_FILE_PATH, "r")
    lines = old_file_handle.readlines()
    old_file_handle.close()

    new_lines = []
    for line in lines:
        temp_list = line.replace("\n", "").split("\t")
        new_list = list([])
        # 新旧字段逻辑
        new_list.append(temp_list[0])
        new_list.append(temp_list[1])
        new_list.append(temp_list[2])
        new_lines.append("\t".join(new_list))

    new_file_handle = open(NEW_SAVE_FILE_PATH, "w")
    new_file_handle.write("\n".join(new_lines))
    new_file_handle.close()


if __name__ == "__main__":
    reformat_save()
