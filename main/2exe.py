# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""

from common import extraTool, tool
from distutils.core import setup
import os
import py2exe
import shutil


def create_exe(py_file_path, need_config=False, need_zip=False):
    build_path = os.path.realpath(".\\build")
    build_dist_path = os.path.realpath(".\\dist")
    py_file_name = ".".join(os.path.basename(py_file_path).split(".")[:-1])

    # 旧目录删除
    tool.remove_dir(build_path)
    tool.remove_dir(build_dist_path)

    # 打包
    setup(console=[py_file_path])

    # 复制其他必要文件
    if need_config:
        tool.make_dir(os.path.join(build_dist_path, "data\\"), 0)
        tool.copy_files(os.path.realpath("..\\common\\config_exe.ini"), os.path.join(build_dist_path, "data\\config.ini"))

    # 删除临时目录
    tool.remove_dir(build_path)

    # 是否需要压缩
    if need_zip:
        extraTool.zip_dir(build_dist_path, os.path.realpath("%s.zip" % py_file_name))
        tool.remove_dir(build_dist_path)
    else:
        shutil.move(build_dist_path, os.path.realpath(".\\%s" % py_file_name))


if __name__ == "__main__":
    file_path = os.path.realpath("..\\weibo\\weibo.py")
    create_exe(file_path)