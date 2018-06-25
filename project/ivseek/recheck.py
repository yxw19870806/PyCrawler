# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os

DONE_SING= "~"


def read_save_data(save_data_path):
    result_list= []
    if not os.path.exists(path.change_path_encoding(save_data_path)):
        return result_list
    for single_save_data in tool.read_file(save_data_path, tool.READ_FILE_TYPE_LINE):
        single_save_data = single_save_data.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
        if len(single_save_data) == 0:
            continue
        single_save_list = single_save_data.split("\t")
        while len(single_save_list) <= 5:
            single_save_list.append("")
        result_list.append(single_save_list)
    return result_list


def main():
    save_data_path = crawler.quickly_get_save_data_path()
    save_data = read_save_data(save_data_path)
    done_list = {}
    for single_save_list in save_data:
        if single_save_list[4] == DONE_SING:
            done_list[single_save_list[3]] = 1
    for single_save_list in save_data:
        if single_save_list[3] in done_list:
            if single_save_list[4] != DONE_SING:
                output.print_msg("new done account " + str(single_save_list))
                single_save_list.append(DONE_SING)


if __name__ == "__main__":
    main()