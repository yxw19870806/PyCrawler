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
import traceback


# 获取指定页数的全部图片
def get_one_page_photo(page_count):
    photo_pagination_url = "http://jigadori.fkoji.com/?p=%s" % page_count
    photo_pagination_response = net.http_request(photo_pagination_url)
    result = {
        "image_info_list": [],  # 全部图片信息
    }
    if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(photo_pagination_response.status))
    photo_list_selector = pq(photo_pagination_response.data.decode("UTF-8")).find("#wrapper .row .photo")
    for photo_index in range(0, photo_list_selector.size()):
        photo_selector = photo_list_selector.eq(photo_index)
        photo_selector_html = photo_selector.html().encode("UTF-8")
        result_photo_info = {
            "account_name": "",  # twitter账号
            "image_url_list": [],  # 图片地址
            "tweet_id": None,  # tweet id
            "tweet_time": None,  # tweet发布时间
        }
        # 获取tweet id
        tweet_url = photo_selector.find(".photo-link-outer a").eq(0).attr("href")
        if not tweet_url:
            raise robot.RobotException("图片信息截取tweet地址失败\n%s" % photo_selector_html)
        tweet_id = tool.find_sub_string(tweet_url.strip(), "status/")
        if not robot.is_integer(tweet_id):
            raise robot.RobotException("tweet地址截取tweet id失败\n%s" % tweet_url)
        result_photo_info["tweet_id"] = int(tweet_id)
        # 获取twitter账号
        account_name = photo_selector.find(".user-info .user-name .screen-name").text()
        if not account_name:
            raise robot.RobotException("图片信息截取twitter账号失败\n%s" % photo_selector_html)
        result_photo_info["account_name"] = str(account_name).strip().replace("@", "")
        # 获取tweet发布时间
        tweet_time = photo_selector.find(".tweet-text .tweet-created-at").text().strip()
        if not tweet_time:
            raise robot.RobotException("图片信息截取tweet发布时间失败\n%s" % photo_selector_html)
        try:
            result_photo_info["tweet_time"] = int(time.mktime(time.strptime(str(tweet_time).strip(), "%Y-%m-%d %H:%M:%S")))
        except ValueError:
            raise robot.RobotException("tweet发布时间文本格式不正确\n%s" % tweet_time)
        # 获取图片地址
        image_list_selector = photo_selector.find(".photo-link-outer a img")
        for image_index in range(0, image_list_selector.size()):
            image_url = image_list_selector.eq(image_index).attr("src")
            if not image_url:
                raise robot.RobotException("图片列表截取图片地址失败\n%s" % image_list_selector.eq(image_index).html())
            result_photo_info["image_url_list"].append(str(image_url).strip())
        result["image_info_list"].append(result_photo_info)
    return result


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
        # image_count  last_blog_time
        save_info = ["0", "0"]
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path).split("\t")
            if len(file_save_info) >= 2 and robot.is_integer(file_save_info[0]) and robot.is_integer(file_save_info[1]):
                save_info = file_save_info
            else:
                log.error("存档内数据格式不正确")
                tool.process_exit()
        total_image_count = 0
        temp_path_list = []

        try:
            page_count = 1
            unique_list = []
            image_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的图片
            while not is_over:
                log.step("开始解析第%s页图片" % page_count)

                # 获取一页图片
                try:
                    photo_pagination_response = get_one_page_photo(page_count)
                except robot.RobotException, e:
                    log.error("第%s页图片解析失败，原因：%s" % (page_count, e.message))
                    raise

                # 没有图片了
                if len(photo_pagination_response["image_info_list"]) == 0:
                    break

                log.trace("第%s页解析的全部图片：%s" % (page_count, photo_pagination_response["image_info_list"]))

                # 寻找这一页符合条件的图片
                for image_info in photo_pagination_response["image_info_list"]:
                    # 新增图片导致的重复判断
                    if image_info["tweet_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(image_info["tweet_id"])

                    # 检查是否达到存档记录
                    if image_info["tweet_time"] > int(save_info[1]):
                        image_info_list.append(image_info)
                    else:
                        is_over = True
                        break

                if not is_over:
                    page_count += 1

            log.step("需要下载的全部图片解析完毕，共%s个" % len(image_info_list))

            # 从最早的图片开始下载
            while len(image_info_list) > 0:
                image_info = image_info_list.pop()
                log.step("开始解析tweet %s的图片" % image_info["tweet_id"])

                image_index = int(save_info[0]) + 1
                for image_url in image_info["image_url_list"]:
                    log.step("开始下载第%s张图片 %s" % (image_index, image_url))

                    if image_url.rfind("/") > image_url.rfind("."):
                        file_type = "jpg"
                    else:
                        file_type = image_url.split(".")[-1]
                    file_path = os.path.join(self.image_download_path, "%05d_%s.%s" % (image_index, image_info["account_name"], file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        # 设置临时目录
                        temp_path_list.append(file_path)
                        log.step("第%s张图片下载成功" % image_index)
                        image_index += 1
                    else:
                        log.error("第%s张图片（account：%s) %s，下载失败，原因：%s" % (image_index, image_info["account_name"], image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # tweet内图片全部下载完毕
                temp_path_list = []  # 临时目录设置清除
                total_image_count += (image_index - 1) - int(save_info[0])  # 计数累加
                save_info[0] = str(image_index - 1)  # 设置存档记录
                save_info[1] = str(image_info["tweet_time"])  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
            # 如果临时目录变量不为空，表示某个日志正在下载中，需要把下载了部分的内容给清理掉
            if len(temp_path_list) > 0:
                for temp_path in temp_path_list:
                    path.delete_dir_or_file(temp_path)
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存新的存档文件
        tool.write_file("\t".join(save_info), self.save_data_path, 2)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    Jigadori().main()
