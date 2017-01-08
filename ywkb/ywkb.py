# -*- coding:UTF-8  -*-
"""
尤物看板图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import os
import re

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True


# 获取一页图片列表
def get_one_page_image_url_list(page_count):
    index_url = "http://www.dahuadan.com/category/ywkb/page/%s" % page_count
    index_response = tool.http_request2(index_url)
    if index_response.status == 200:
        image_url_list = re.findall('<img class="aligncenter" src="([^"]*)" />', index_response.data)
        return {"is_over": False, "image_url_list": image_url_list}
    elif index_response.status == 404:
        return {"is_over": True, "image_url_list": []}
    return None


class Template(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
        if IS_SORT:
            image_path = IMAGE_TEMP_PATH
        else:
            image_path = IMAGE_DOWNLOAD_PATH
        tool.make_dir(image_path, 0)

        page_count = 1
        image_count = 1
        while True:
            log.step("开始解析第%s页日志" % page_count)

            image_info = get_one_page_image_url_list(page_count)
            if image_info is None:
                log.error(" 第%s页图片无法获取" % page_count)
                tool.process_exit()

            if image_info["is_over"]:
                break

            for image_url in image_info["image_url_list"]:
                log.step("开始下载第%s张图片 %s" % (page_count, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                if tool.save_net_file2(image_url, file_path):
                    log.step("第%s张图片下载成功" % image_count)
                    image_count += 1
                else:
                    log.error("第%s张图片 %s 获取失败" % (image_count, image_url))

            page_count += 1

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))


if __name__ == "__main__":
    Template().main()
