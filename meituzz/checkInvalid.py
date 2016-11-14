# -*- coding:UTF-8  -*-
"""
检查美图赚赚收费相册中已经被删除的那些
http://meituzz.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import os
import re


def check_invalid():
    # 获取存放路径
    config_path = os.path.join(os.getcwd(), "..\\common\\config.ini")
    config = robot.read_config(config_path)
    save_data_path = robot.get_config(config, "SAVE_DATA_PATH", "info/save.data", 3)
    save_data_dir = os.path.dirname(save_data_path)
    fee_save_data_path = os.path.join(save_data_dir, "fee.data")
    # 读取村存档中的收费相册列表
    if not os.path.exists(fee_save_data_path):
        log.step("收费相册存档不存在")
        return
    fee_save_data_file = open(fee_save_data_path, "r")
    fee_save_data = fee_save_data_file.read()
    fee_save_data_file.close()
    fee_album_id_list = fee_save_data.strip().split(" ")
    new_fee_album_id_list = []
    # 循环访问，判断相册是否已经被删除
    for fee_album_id in fee_album_id_list:
        album_url = "http://meituzz.com/album/browse?albumID=%s" % fee_album_id
        album_page_return_code, album_page = tool.http_request(album_url)[:2]
        if album_page_return_code == 1:
            if album_page.find("<title>相册已被删除</title>") == -1:
                new_fee_album_id_list.append(fee_album_id)
            else:
                log.step("第%s页相册已被删除" % fee_album_id)
    # 重新保存
    fee_save_data_file = open(fee_save_data_path, "w")
    fee_save_data_file.write(" ".join(new_fee_album_id_list) + " ")
    fee_save_data_file.close()

check_invalid()
