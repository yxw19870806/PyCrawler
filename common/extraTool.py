# -*- coding:UTF-8  -*-
"""
一些暂时用不到的方法
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import zipfile


# 压缩文件夹
# need_source_dir   是否需要把文件夹名作为根目录
def zip_dir(source_dir, zip_file_path, need_source_dir=True):
    file_list = []
    path_prefix_len = len(source_dir)  # 文件列表路径前缀的长度
    # 是目录，直接添加
    if os.path.isfile(source_dir):
        file_list.append(source_dir)
    else:
        # 如果需要包含目录
        if need_source_dir:
            path_prefix_len -= len(os.path.basename(source_dir)) + 1
        for root, dirs, files in os.walk(source_dir):
            for name in files:
                file_list.append(os.path.join(root, name))
    zip_file = zipfile.ZipFile(zip_file_path, "w", zipfile.zlib.DEFLATED)
    for file_path in file_list:
        zip_file_path = file_path[path_prefix_len:]
        zip_file.write(file_path, zip_file_path)
    zip_file.close()


# 解压缩文件
def unzip_file(zip_file_path, destination_path):
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
    zip_file = zipfile.ZipFile(zip_file_path)
    for zip_file_path in zip_file.namelist():
        zip_file_path = zip_file_path.replace("\\", "/")
        if zip_file_path.endswith("/"):  # 解压目录
            os.makedirs(os.path.join(destination_path, zip_file_path))
        else:  # 解压文件
            file_path = os.path.join(destination_path, zip_file_path)  # 文件的完整路径
            file_dir = os.path.dirname(file_path)
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            outfile = open(file_path, "wb")
            outfile.write(zip_file.read(zip_file_path))
            outfile.close()