# -*- coding:UTF-8  -*-
# 重新格式化存档，修改字段顺序
import os
from common import tool

# 旧存档路径
OLD_SAVE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "save.data"))
# 新存档路径
NEW_SAVE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "new_save.data"))


# 修改存档文件列的顺序并保存
def reformat_save():
    new_lines = []
    for line in tool.read_file(OLD_SAVE_FILE_PATH, tool.READ_FILE_TYPE_LINE):
        temp_list = line.replace("\n", "").split("\t")
        new_list = list([])
        # 新旧字段逻辑
        new_list.append(temp_list[0])
        new_list.append(temp_list[1])
        new_list.append(temp_list[2])
        new_lines.append("\t".join(new_list))

    tool.write_file("\n".join(new_lines), NEW_SAVE_FILE_PATH, tool.WRITE_FILE_TYPE_REPLACE)


if __name__ == "__main__":
    reformat_save()
