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


def change_path_encoding(file_path):
    """Decode file path to unicode, and return the real path"""
    if not isinstance(file_path, unicode):
        file_path = str(file_path)
        file_path = unicode(file_path, "UTF-8")
    return os.path.realpath(file_path)


def create_dir(dir_path, create_mode=CREATE_DIR_MODE_IGNORE_IF_EXIST):
    """Create directory

    :param create_mode:
        CREATE_DIR_MODE_IGNORE_IF_EXIST   create if not exist; do nothing if exist
        CREATE_DIR_MODE_DELETE_IF_EXIST   delete first if exist and not empty

    :return:
        True    create succeed
        False   create failed（include file_path is a file, not a directory）
    """
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


def delete_dir_or_file(dir_path):
    """Delete file or directory（include subdirectory or files）"""
    dir_path = change_path_encoding(dir_path)
    if not os.path.exists(dir_path):
        return True
    if os.path.isdir(dir_path):
        shutil.rmtree(dir_path, True)
    else:
        os.remove(dir_path)


def delete_null_dir(dir_path):
    """Delete all empty subdirectory"""
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
def get_dir_files_name(dir_path, order=None):
    """Get list of filename from specified directory

    :param order:
        RETURN_FILE_LIST_ASC    ascending order of files list
        RETURN_FILE_LIST_DESC   descending order of files list
        Other                   default files list

    :return:
        list of files list(unicode)
    """
    dir_path = change_path_encoding(dir_path)
    if not os.path.exists(dir_path):
        return []
    if not os.path.isdir(dir_path):
        return []
    files_list = map(lambda file_name: unicode(file_name, "UTF-8"), os.listdir(dir_path))
    # 升序
    if order == RETURN_FILE_LIST_ASC:
        return sorted(files_list, reverse=False)
    # 降序
    elif order == RETURN_FILE_LIST_DESC:
        return sorted(files_list, reverse=True)
    else:
        return files_list


def copy_files(source_dir_path, destination_dir_path):
    """Copy Files from source directory to destination directory"""
    source_dir_path = change_path_encoding(source_dir_path)
    if not create_dir(os.path.dirname(destination_dir_path)):
        return False
    destination_dir_path = change_path_encoding(destination_dir_path)
    shutil.copyfile(source_dir_path, destination_dir_path)
    return True
