# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import py2exe
import shutil
from distutils.core import setup
from common import extraTool, path, tool


def create_exe(py_file_path, need_config=False, need_zip=False):
    build_path = os.path.abspath(".\\build")
    build_dist_path = os.path.abspath(".\\dist")
    py_file_name = ".".join(os.path.basename(py_file_path).split(".")[:-1])

    # 旧目录删除
    path.delete_dir_or_file(build_path)
    path.delete_dir_or_file(build_dist_path)

    # 打包
    setup(console=[py_file_path])

    # 复制其他必要文件
    if need_config:
        path.create_dir(os.path.join(build_dist_path, "data\\"))
        path.copy_file(os.path.join(tool.PROJECT_COMMON_PATH, "config_exe.ini"), os.path.join(build_dist_path, "data\\config.ini"))

    # 删除临时目录
    path.delete_dir_or_file(build_path)

    # 是否需要压缩
    if need_zip:
        extraTool.zip_dir(build_dist_path, os.path.abspath("%s.zip" % py_file_name))
        path.delete_dir_or_file(build_dist_path)
    else:
        shutil.move(build_dist_path, os.path.abspath(".\\%s" % py_file_name))


if __name__ == "__main__":
    file_path = os.path.abspath("..\\weibo\\weibo.py")
    create_exe(file_path)