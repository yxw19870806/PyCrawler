# -*- coding:UTF-8  -*-
"""
分组移动封面图到子目录中
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import shutil


def group():
    # 没有分类的
    other_dir = os.path.join(destination_path, "-")
    if not os.path.exists(other_dir):
        os.makedirs(other_dir)

    for root, dirs, files in os.walk(source_path):
        for file_name in files:
            if file_name.find("-") >= 0:
                title, num = file_name.split("-")
                if title.isalpha():
                    if title == "CON":
                        title = "CON_"
                    new_dir = os.path.join(destination_path, title)
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                    shutil.move(os.path.join(root, file_name), os.path.join(new_dir, file_name))
                    continue
            shutil.move(os.path.join(root, file_name), os.path.join(other_dir, file_name))

if __name__ == "__main__":
    source_path = "D:\\workspace\\1\\photo"
    destination_path = "D:\\workspace\\2"
    group()
