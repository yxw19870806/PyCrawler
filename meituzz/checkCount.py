# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os


def compare(new_path, old_path):
    new_dir_list = os.listdir(new_path)
    for dir_name in new_dir_list:
        temp_path = os.path.join(old_path, dir_name)
        if os.path.exists(temp_path):
            new_count = len(os.listdir(os.path.join(new_path, dir_name)))
            old_count = len(os.listdir(temp_path))
            if new_count < old_count:
                print dir_name + " not compare!"


compare("D:\\workspace\\Code\\meituzz\\photo2", "D:\\workspace\\G+\\meituzz\\photo")