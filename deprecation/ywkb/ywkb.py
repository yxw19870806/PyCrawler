# -*- coding:UTF-8  -*-
"""
尤物看板图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import os
import re
import traceback
from common import *


# 获取一页图片信息列表
def get_one_page_photo(page_count):
    photo_pagination_url = "http://www.dahuadan.com/category/ywkb/page/%s" % page_count
    photo_pagination_response = net.http_request(photo_pagination_url, method="GET")
    result = {
        "image_info_list": [],  # 是不是已经没有新的相册
        "is_over": False,  # 是不是已经没有新的相册
    }
    if photo_pagination_response.status == 404:
        result["is_over"] = True
    elif photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(photo_pagination_response.status))
    article_data = tool.find_sub_string(photo_pagination_response.data, '<section id="primary"', "</section>")
    if not article_data:
        raise crawler.CrawlerException("页面截取正文失败\n%s" % photo_pagination_response.data)
    image_info_list = re.findall('<article id="post-([\d]*)"[\s|\S]*?<img class="aligncenter" src="([^"]*)" />', article_data)
    if len(image_info_list) == 0:
        raise crawler.CrawlerException("正文匹配图片信息失败\n%s" % photo_pagination_response.data)
    image_id_2_url_list = {}
    for image_id, image_url in image_info_list:
        image_id_2_url_list[int(image_id)] = str(image_url)
    for image_id in sorted(image_id_2_url_list.keys(), reverse=True):
        result_image_info = {
            "image_id": image_id,  # 图片id
            "image_url": image_id_2_url_list[image_id],  # 图片地址
        }
        result["image_info_list"].append(result_image_info)
    return result


class YWKB(crawler.Crawler):
    def __init__(self):
        # 设置APP目录
        tool.PROJECT_APP_PATH = os.path.abspath(os.path.dirname(__file__))

        # 初始化参数
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        crawler.Crawler.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的图片id
        last_image_id = 0
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path)
            if not crawler.is_integer(file_save_info):
                log.error("存档内数据格式不正确")
                tool.process_exit()
            last_image_id = int(file_save_info)

        try:
            page_count = 1
            image_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的图片
            while not is_over:
                if not self.is_running():
                    tool.process_exit(0)
                log.step("开始解析第%s页日志" % page_count)

                try:
                    photo_pagination_response = get_one_page_photo(page_count)
                except crawler.CrawlerException, e:
                    log.error(" 第%s页图片解析失败，原因：%s" % (page_count, e.message))
                    raise

                if photo_pagination_response["is_over"]:
                    break

                # 寻找这一页符合条件的图片
                for image_info in photo_pagination_response["image_info_list"]:
                    # 检查是否达到存档记录
                    if image_info["image_id"] > last_image_id:
                        image_info_list.append(image_info)
                    else:
                        is_over = True
                        break

                page_count += 1

            log.step("需要下载的全部图片解析完毕，共%s张" % len(image_info_list))

            # 从最早的图片开始下载
            while len(image_info_list) > 0:
                if not self.is_running():
                    tool.process_exit(0)
                image_info = image_info_list.pop()
                log.step("开始下载%s的图片 %s" % (image_info["image_id"], image_info["image_url"]))

                file_type = image_info["image_url"].split(".")[-1]
                file_path = os.path.join(self.image_download_path, "%04d.%s" % (image_info["image_id"], file_type))
                try:
                    save_file_return = net.save_net_file(image_info["image_url"], file_path)
                    if save_file_return["status"] == 1:
                        log.step("%s的图片下载成功" % image_info["image_id"])
                    else:
                        log.error("%s的图片 %s 下载失败，原因：%s" % (image_info["image_id"], image_info["image_url"], crawler.download_failre(save_file_return["code"])))
                        continue
                except SystemExit:
                    log.step("提前退出")
                    break
                # 图片下载完毕
                self.total_image_count += 1  # 计数累加
                last_image_id = str(image_info["image_id"])  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存新的存档文件
        tool.write_file(str(last_image_id), self.save_data_path, tool.WRITE_FILE_TYPE_REPLACE)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


if __name__ == "__main__":
    YWKB().main()
