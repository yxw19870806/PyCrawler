# -*- coding:UTF-8  -*-
"""
グラドル自画撮り部 图片爬虫
http://jigadori.fkoji.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as pq
import os
import time


# 获取指定页数的所有图片
def get_one_page_photo(page_count):
    photo_pagination_url = "http://jigadori.fkoji.com/?p=%s" % page_count
    photo_pagination_response = net.http_request(photo_pagination_url)
    extra_info = {
        "image_info_list": [],  # 页面解析出的图片信息列表
    }
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        photo_list_selector = pq(photo_pagination_response.data).find("#wrapper .row .photo")
        for photo_index in range(0, photo_list_selector.size()):
            photo_selector = photo_list_selector.eq(photo_index)
            extra_photo_info = {
                "is_error": False,  # 是不是格式不符合
                "account_name": "",  # 页面解析出的账号名字
                "tweet_id": 0,  # 页面解析出的tweet id
                "image_url_list": [],  # 页面解析出的图片地址
                "time": 0,  # 页面解析出的图片上传时间
                "html": photo_selector.html().encode("UTF-8"),  # 原始页面
            }
            account_name = photo_selector.find(".user-info .user-name .screen-name").text()
            tweet_time = photo_selector.find(".tweet-text .tweet-created-at").text()
            tweet_url = photo_selector.find(".photo-link-outer a").eq(0).attr("href")
            if tweet_url:
                tweet_id = tool.find_sub_string(tweet_url.strip(), "status/")
            else:
                tweet_id = None
            if account_name and tweet_time and robot.is_integer(tweet_id):
                extra_photo_info["account_name"] = account_name.strip().replace("@", "")
                extra_photo_info["time"] = int(time.mktime(time.strptime(tweet_time.strip(), "%Y-%m-%d %H:%M:%S")))
                extra_photo_info["tweet_id"] = int(tweet_id)
                image_list_selector = photo_selector.find(".photo-link-outer a img")
                for image_index in range(0, image_list_selector.size()):
                    image_url = image_list_selector.eq(image_index).attr("src")
                    if image_url:
                        extra_photo_info["image_url_list"].append(str(image_url).strip())
                    else:
                        extra_photo_info["is_error"] = True
            else:
                extra_photo_info["is_error"] = True
            extra_info["image_info_list"].append(extra_photo_info)
    photo_pagination_response.extra_info = extra_info
    return photo_pagination_response


# 从图片页面中解析获取推特发布时间的时间戳
def get_tweet_created_time(photo_info):
    tweet_created_time_find = photo_info.findAll("div", "tweet-created-at")
    if len(tweet_created_time_find) == 1:
        tweet_created_time_string = tweet_created_time_find[0].text
        return int(time.mktime(time.strptime(tweet_created_time_string, "%Y-%m-%d %H:%M:%S")))
    return None


class Jigadori(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_SET_PROXY: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件
        last_blog_time = 0
        image_start_index = 0
        if os.path.exists(self.save_data_path):
            save_info = tool.read_file(self.save_data_path).split("\t")
            if len(save_info) >= 2:
                image_start_index = int(save_info[0])
                last_blog_time = int(save_info[1])

        page_count = 1
        image_count = 1
        unique_list = []
        is_over = False
        first_blog_time = None
        while not is_over:
            log.step("开始解析第%s页图片" % page_count)

            # 获取一页图片
            photo_pagination_response = get_one_page_photo(page_count)
            if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页图片访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(photo_pagination_response.status)))
                tool.process_exit()

            # 没有图片了
            if len(photo_pagination_response.extra_info["image_info_list"]) == 0:
                break

            for image_info in photo_pagination_response.extra_info["image_info_list"]:
                if image_info["is_error"]:
                    log.error("第%s张图片所在页面%s解析失败" % (page_count, image_info["html"]))
                    tool.process_exit()

                # 检查是否达到存档记录
                if image_info["time"] <= last_blog_time:
                    is_over = True
                    break

                # 新的存档记录
                if first_blog_time is None:
                    first_blog_time = str(image_info["time"])

                # 新增图片导致的重复判断
                if image_info["tweet_id"] in unique_list:
                    continue
                else:
                    unique_list.append(image_info["tweet_id"])

                for image_url in image_info["image_url_list"]:
                    log.step("开始下载第%s张图片 %s" % (image_count, image_url))

                    file_type = image_url.split(".")[-1]
                    if file_type.find("/") != -1:
                        file_type = "jpg"
                    file_path = os.path.join(self.image_temp_path, "%05d_%s.%s" % (image_count, image_info["account_name"], file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step("第%s张图片下载成功" % image_count)
                        image_count += 1
                    else:
                        log.error("第%s张图片（account_id：%s) %s，下载失败，原因：%s" % (image_count, image_info["account_name"], image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

            if not is_over:
                page_count += 1

        log.step("下载完毕")

        # 排序复制到保存目录
        if image_count > 1:
            log.step("图片开始从下载目录移动到保存目录")

            file_list = tool.get_dir_files_name(self.image_temp_path, "desc")
            for file_name in file_list:
                image_path = os.path.join(self.image_temp_path, file_name)
                file_name_list = file_name.split(".")
                file_type = file_name_list[-1]
                account_id = "_".join(".".join(file_name_list[:-1]).split("_")[1:])

                image_start_index += 1
                destination_file_name = "%05d_%s.%s" % (image_start_index, account_id, file_type)
                destination_path = os.path.join(self.image_download_path, destination_file_name)
                tool.copy_files(image_path, destination_path)

            log.step("图片从下载目录移动到保存目录成功")

            # 删除临时文件夹
            tool.remove_dir_or_file(self.image_temp_path)

        # 保存新的存档文件
        if first_blog_time is not None:
            tool.write_file(str(image_start_index) + "\t" + first_blog_time, self.save_data_path, 2)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))


if __name__ == "__main__":
    Jigadori().main()
