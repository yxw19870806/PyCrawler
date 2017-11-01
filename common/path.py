# -*- coding:UTF-8  -*-
"""
浏览器数据相关类
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import shutil


CREATE_DIR_MODE_IGNORE_IF_EXIST = 1
CREATE_DIR_MODE_DELETE_IF_EXIST = 2
RETURN_FILE_LIST_ASC = 1
RETURN_FILE_LIST_DESC = 2


# 文件路径编码转换
def change_path_encoding(path):
    if isinstance(path, str):
        path = unicode(path, "UTF-8")
    return os.path.realpath(path)


# 创建目录
# create_mode 0 : 不存在则创建
# create_mode 1 : 存在则删除并创建
# create_mode 2 : 存在提示删除，确定后删除创建，取消后退出程序
def create_dir(dir_path, create_mode=CREATE_DIR_MODE_IGNORE_IF_EXIST):
    dir_path = change_path_encoding(dir_path)
    if create_mode not in [CREATE_DIR_MODE_IGNORE_IF_EXIST, CREATE_DIR_MODE_DELETE_IF_EXIST]:
        create_mode = CREATE_DIR_MODE_IGNORE_IF_EXIST
    # 目录存在
    if os.path.exists(dir_path):
        if create_mode == CREATE_DIR_MODE_IGNORE_IF_EXIST:
            if os.path.isdir(dir_path):
                return True
            else:
                return False
        elif create_mode == CREATE_DIR_MODE_DELETE_IF_EXIST:
            if os.path.isdir(dir_path):
                # empty dir
                if not os.listdir(dir_path):
                    return True
        delete_dir_or_file(dir_path)
    os.makedirs(dir_path)
    if os.path.isdir(dir_path):
        return True
    return False


# 删除整个目录以及目录下所有文件
def delete_dir_or_file(dir_path):
    dir_path = change_path_encoding(dir_path)
    if not os.path.exists(dir_path):
        return True
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path, True)
    else:
        os.remove(dir_path)


# 删除指定目录下的全部空文件夹
def delete_null_dir(dir_path):
    dir_path = change_path_encoding(dir_path)
    if os.path.isdir(dir_path):
        for file_name in os.listdir(dir_path):
            sub_path = os.path.join(dir_path, file_name)
            if os.path.isdir(sub_path):
                delete_null_dir(sub_path)
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)


# 获取指定目录的文件列表
# order desc 降序
# order asc  升序
# order 其他 不需要排序
def get_dir_files_name(path, order=None):
    path = change_path_encoding(path)
    if not os.path.exists(path):
        return []
    files_list = map(lambda file_name: file_name.encode("UTF-8"), os.listdir(path))
    # 升序
    if order == RETURN_FILE_LIST_ASC:
        return sorted(files_list, reverse=False)
    # 降序
    elif order == RETURN_FILE_LIST_DESC:
        return sorted(files_list, reverse=True)
    else:
        return files_list


# 复制文件
# source_file_path      源文件路径
# destination_file_path 目标文件路径
def copy_files(source_file_path, destination_file_path):
    source_file_path = change_path_encoding(source_file_path)
    if not create_dir(os.path.dirname(destination_file_path)):
        return False
    destination_file_path = change_path_encoding(destination_file_path)
    shutil.copyfile(source_file_path, destination_file_path)
    return True
