# -*- coding:UTF-8  -*-
"""
尤物看板图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re


# 获取一页图片信息列表
def get_one_page_photo(page_count):
    photo_pagination_url = "http://www.dahuadan.com/category/ywkb/page/%s" % page_count
    photo_pagination_response = net.http_request(photo_pagination_url)
    extra_info = {
        "is_over": False,  # 是不是已经没有新的相册
        "image_info_list": [],  # 是不是已经没有新的相册
    }
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        article_data = tool.find_sub_string(photo_pagination_response.data, '<section id="primary"', "</section>")
        image_info_list = re.findall('<article id="post-([\d]*)"[\s|\S]*?<img class="aligncenter" src="([^"]*)" />', article_data)
        image_id_2_url_list = {}
        for image_id, image_url in image_info_list:
            image_id_2_url_list[int(image_id)] = str(image_url)
        for image_id in sorted(image_id_2_url_list.keys(), reverse=True):
            extra_image_info = {
                "image_id": image_id,  # 图片id
                "image_url": image_id_2_url_list[image_id],  # 图片地址
            }
            extra_info["image_info_list"].append(extra_image_info)
    elif photo_pagination_response.status == 404:
        extra_info["is_over"] = True
    photo_pagination_response.extra_info = extra_info
    return photo_pagination_response


class YWKB(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的image id
        if os.path.exists(self.save_data_path):
            last_image_id = int(tool.read_file(self.save_data_path))
        else:
            last_image_id = 1

        page_count = 1
        image_count = 1
        is_over = False
        first_image_id = None
        while not is_over:
            log.step("开始解析第%s页日志" % page_count)

            photo_pagination_response = get_one_page_photo(page_count)
            if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(" 第%s页图片访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(photo_pagination_response.status)))
                tool.process_exit()

            if photo_pagination_response.extra_info["is_over"]:
                break

            for image_info in photo_pagination_response.extra_info["image_info_list"]:
                # 检查是否达到存档记录
                if image_info["image_id"] <= last_image_id:
                    is_over = True
                    break

                # 新的存档记录
                if first_image_id is None:
                    first_image_id = image_info["image_id"]

                log.step("开始下载%s的图片 %s" % (image_info["image_id"], image_info["image_url"]))

                file_type = image_info["image_url"].split(".")[-1]
                file_path = os.path.join(self.image_download_path, "%04d.%s" % (image_info["image_id"], file_type))
                save_file_return = net.save_net_file(image_info["image_url"], file_path)
                if save_file_return["status"] == 1:
                    log.step("%s的图片下载成功" % image_info["image_id"])
                    image_count += 1
                else:
                    log.error("%s的图片 %s 下载失败，原因：%s" % (image_info["image_id"], image_info["image_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))

            page_count += 1

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))

        # 重新保存存档文件
        if first_image_id is not None:
            tool.write_file(str(first_image_id), self.save_data_path, 2)


if __name__ == "__main__":
    YWKB().main()
