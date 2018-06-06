# -*- coding:UTF-8  -*-
"""
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import tool
import os
import re


# 从文件中读取全部的url列表
def get_file_url_from_log(log_path):
    log_data = tool.read_file(log_path)
    return re.findall("(http://[\S]*)", log_data)


# 根据url列表，生成包含全部下载地址的页面
def generate_html_page(video_url_list):
    html = "<!DOCTYPE html>\n<html>\n<body>\n"
    index = 1
    for video_url in video_url_list:
        html += "\t<a href='%s'>%s</a>\n" % (video_url, "%s.mp4" % index)
        index += 1
    html += "</body>\n</html>"
    return html

if __name__ == "__main__":
    file_path = os.path.abspath("..//log//log.txt")
    html_file = open("video.html", "w")
    html_file.write(generate_html_page(get_file_url_from_log(file_path)))
    html_file.close()
