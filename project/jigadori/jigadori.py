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
        "image_info_list": [],  # 所有图片信息
    }
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        photo_list_selector = pq(photo_pagination_response.data.decode("UTF-8")).find("#wrapper .row .photo")
        for photo_index in range(0, photo_list_selector.size()):
            photo_selector = photo_list_selector.eq(photo_index)
            photo_selector_html = photo_selector.html().encode("UTF-8")
            extra_photo_info = {
                "account_name": "",  # twitter账号
                "tweet_id": 0,  # tweet id
                "image_url_list": [],  # 图片地址
                "time": None,  # tweet发布时间
            }
            # 获取tweet id
            tweet_url = photo_selector.find(".photo-link-outer a").eq(0).attr("href")
            if not tweet_url:
                raise robot.RobotException("图片信息选择器获取tweet地址失败\n%s" % photo_selector_html)
            tweet_id = tool.find_sub_string(tweet_url.strip(), "status/")
            if not robot.is_integer(tweet_id):
                raise robot.RobotException("tweet地址获取tweet id失败\n%s" % tweet_url)
            extra_photo_info["tweet_id"] = int(tweet_id)

            # 获取twitter账号
            account_name = photo_selector.find(".user-info .user-name .screen-name").text()
            if not account_name:
                raise robot.RobotException("图片信息选择器获取twitter账号失败\n%s" % photo_selector_html)
            extra_photo_info["account_name"] = str(account_name).strip().replace("@", "")

            # 获取tweet发布时间
            tweet_time = photo_selector.find(".tweet-text .tweet-created-at").text().strip()
            if not tweet_time:
                raise robot.RobotException("图片信息选择器获取tweet发布时间失败\n%s" % photo_selector_html)
            try:
                extra_photo_info["time"] = int(time.mktime(time.strptime(str(tweet_time).strip(), "%Y-%m-%d %H:%M:%S")))
            except ValueError:
                raise robot.RobotException("tweet发布时间文本格式不正确\n%s" % tweet_time)

            # 获取图片地址
            image_list_selector = photo_selector.find(".photo-link-outer a img")
            for image_index in range(0, image_list_selector.size()):
                image_url = image_list_selector.eq(image_index).attr("src")
                if not image_url:
                    raise robot.RobotException("图片列表获取图片地址失败\n%s" % image_list_selector.eq(image_index).html())
                extra_photo_info["image_url_list"].append(str(image_url).strip())

            extra_info["image_info_list"].append(extra_photo_info)
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(photo_pagination_response.status))
    photo_pagination_response.extra_info = extra_info
    return photo_pagination_response


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
            try:
                photo_pagination_response = get_one_page_photo(page_count)
            except robot.RobotException, e:
                log.error("第%s页图片访问失败，原因：%s" % (page_count, e.message))
                tool.process_exit()

            # 没有图片了
            if len(photo_pagination_response.extra_info["image_info_list"]) == 0:
                break

            for image_info in photo_pagination_response.extra_info["image_info_list"]:
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
