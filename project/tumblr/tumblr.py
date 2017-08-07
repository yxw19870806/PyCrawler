# -*- coding:UTF-8  -*-
"""
tumblr图片和视频爬虫
http://www.tumblr.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os
import re
import threading
import time
import traceback
import urllib
import urlparse

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 获取一页的日志地址列表
def get_one_page_post(account_id, page_count):
    host = "http://%s.tumblr.com" % account_id
    post_pagination_url = "%s/page/%s" % (host, page_count)
    post_pagination_response = net.http_request(post_pagination_url)
    result = {
        "post_url_list": [],  # 所有日志地址
        "is_over": [],  # 是不是最后一页日志
    }
    if post_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        page_html = tool.find_sub_string(post_pagination_response.data, '<script type="application/ld+json">', "</script>").strip()
        if page_html:
            try:
                page_data = json.loads(page_html)
            except ValueError:
                raise robot.RobotException("日志信息加载失败\n%s" % page_html)
            if not robot.check_sub_key(("itemListElement",), page_data):
                raise robot.RobotException("日志信息'itemListElement'字段不存在\n%s" % page_data)

            # 获取所有日志地址
            for post_info in page_data["itemListElement"]:
                if not robot.check_sub_key(("url",), post_info):
                    raise robot.RobotException("日志信息'url'字段不存在\n%s" % page_data)
                post_url_split = urlparse.urlsplit(post_info["url"].encode("UTF-8"))
                post_url = post_url_split[0] + "://" + post_url_split[1] + urllib.quote(post_url_split[2])
                result["post_url_list"].append(str(post_url))
            if len(result["post_url_list"]) == 0:
                raise robot.RobotException("获取日志地址失败\n%s" % page_html)
        else:
            result["is_over"] = True
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(post_pagination_response.status))
    return result


# 获取日志页面
def get_post_page(post_url):
    post_response = net.http_request(post_url)
    result = {
        "has_video": False,  # 是不是包含视频
        "image_url_list": [],  # 所有图片地址
    }
    if post_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        post_page_head = tool.find_sub_string(post_response.data, "<head", "</head>", 3)
        if not post_page_head:
            raise robot.RobotException("页面截取正文失败\n%s" % post_response.data)
        # 获取og_type（页面类型的是视频还是图片或其他）
        og_type = tool.find_sub_string(post_page_head, '<meta property="og:type" content="', '" />')
        if not og_type:
            raise robot.RobotException("正文截取og_type失败\n%s" % post_page_head)
        # 空、音频、引用，跳过
        if og_type in ["tumblr-feed:entry", "tumblr-feed:audio", "tumblr-feed:quote", "tumblr-feed:link"]:
            pass
        else:
            # 视频
            if og_type == "tumblr-feed:video":
                result["has_video"] = True
                # 获取图片地址
                image_url = tool.find_sub_string(post_page_head, '<meta property="og:image" content="', '" />')
                if image_url and image_url != "http://assets.tumblr.com/images/og/fb_landscape_share.png":
                    result["image_url_list"].append(image_url)
            else:
                # 获取所有图片地址
                image_url_list = re.findall('"(http[s]?://\w*[.]?media.tumblr.com/[^"]*)"', post_page_head)
                new_image_url_list = {}
                for image_url in image_url_list:
                    # 头像，跳过
                    if image_url.find("/avatar_") != -1:
                        continue
                    image_id = image_url[image_url.find("media.tumblr.com/") + len("media.tumblr.com/"):].split("_")[0]
                    # 判断是否有分辨率更小的相同图片
                    if image_id in new_image_url_list:
                        resolution = image_url.split("_")[-1].split(".")[0]
                        if resolution[-1] == "h":
                            resolution = int(resolution[:-1])
                        else:
                            resolution = int(resolution)
                        old_resolution = new_image_url_list[image_id].split("_")[-1].split(".")[0]
                        if old_resolution[-1] == "h":
                            old_resolution = int(old_resolution[:-1])
                        else:
                            old_resolution = int(old_resolution)
                        if resolution < old_resolution:
                            continue
                    new_image_url_list[image_id] = image_url
                result["image_url_list"] = new_image_url_list.values()
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(post_response.status))
    return result


# 获取视频播放页面
def get_video_play_page(account_id, post_id):
    video_play_url = "http://www.tumblr.com/video/%s/%s/0" % (account_id, post_id)
    video_play_response = net.http_request(video_play_url)
    result = {
        "video_url": None,  # 视频地址
        "is_skip": False,  # 是不是第三方视频
    }
    if video_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        video_url_find = re.findall('src="(http[s]?://' + account_id + '.tumblr.com/video_file/[^"]*)" type="[^"]*"', video_play_response.data)
        if len(video_url_find) == 1:
            video_response = net.http_request(video_url_find[0], redirect=False)
            # 获取视频重定向页面
            if video_response.status == 302 and "Location" in video_response.headers:
                # http://vtt.tumblr.com/tumblr_okstty6tba1rssthv_r1_480.mp4#_=
                # ->
                # http://vtt.tumblr.com/tumblr_okstty6tba1rssthv_r1_720.mp4
                result["video_url"] = video_response.headers["Location"].replace("#_=_", "").replace("_r1_480", "_r1_720")
            else:
                # http://www.tumblr.com/video_file/t:YGdpA6jB1xslK7TtpYTgXw/110204932003/tumblr_nj59qwEQoV1qjl082/720
                # ->
                # http://vtt.tumblr.com/tumblr_nj59qwEQoV1qjl082.mp4
                # 去除视频指定分辨率
                temp_list = video_url_find[0].split("/")
                if temp_list[-1].isdigit():
                    video_id = temp_list[-2]
                else:
                    video_id = temp_list[-1]
                result["video_url"] = "http://vtt.tumblr.com/%s.mp4" % video_id
        elif len(video_url_find) == 0:
            # 第三方视频
            result["is_skip"] = True
        else:
            raise robot.RobotException("页面截取视频地址失败\n%s" % video_play_response.data)
    else:
        raise robot.RobotException(robot.get_http_request_failed_reason(video_play_response.status))
    return result


class Tumblr(robot.Robot):
    def __init__(self):
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  image_count  video_count  last_post_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if robot.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if robot.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id], self.thread_lock)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_id in ACCOUNTS:
                new_save_data_file.write("\t".join(account_list[account_id]) + "\n")
            new_save_data_file.close()

        # 删除临时文件夹
        self.finish_task()

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]

        try:
            log.step(account_id + " 开始")

            page_count = 1
            image_count = 1
            video_count = 1
            unique_list = []
            is_over = False
            first_post_id = None
            image_path = os.path.join(IMAGE_TEMP_PATH, account_id)
            video_path = os.path.join(VIDEO_TEMP_PATH, account_id)
            while not is_over:
                log.step(account_id + " 开始解析第%s页相册" % page_count)

                # 获取一页的日志地址
                try:
                    post_pagination_response = get_one_page_post(account_id, page_count)
                except robot.RobotException, e:
                    log.error(account_id + " 第%s页相册访问失败，原因：%s" % (page_count, e.message))
                    raise

                if post_pagination_response["is_over"]:
                    break

                log.trace(account_id + " 第%s页相册解析的所有日志：%s" % (page_count, post_pagination_response["post_url_list"]))

                for post_url in post_pagination_response["post_url_list"]:
                    post_id = tool.find_sub_string(post_url, "/post/").split("/")[0]

                    # 检查是否达到存档记录
                    if int(post_id) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 新的存档记录
                    if first_post_id is None:
                        first_post_id = post_id

                    # 新增信息页导致的重复判断
                    if post_id in unique_list:
                        continue
                    else:
                        unique_list.append(post_id)

                    log.step(account_id + " 开始解析日志 %s" % post_url)

                    # 获取日志
                    try:
                        post_response = get_post_page(post_url)
                    except robot.RobotException, e:
                        log.error(account_id + " 日志 %s 访问失败，原因：%s" % (post_url, e.message))
                        raise

                    # 视频下载
                    while IS_DOWNLOAD_VIDEO and post_response["has_video"]:
                        try:
                            video_play_response = get_video_play_page(account_id, post_id)
                        except robot.RobotException, e:
                            log.error(account_id + " 日志 %s 的视频播放页面访问失败，原因：%s" % (post_url, e.message))
                            raise

                        # 第三方视频，跳过
                        if video_play_response["is_skip"]:
                            log.error(account_id + " 日志 %s 存在第三方视频，跳过" % post_url)
                            break

                        video_url = video_play_response["video_url"]
                        log.step(account_id + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                        save_file_return = net.save_net_file(video_url, video_file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_id + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_id + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        break

                    # 图片下载
                    if IS_DOWNLOAD_IMAGE and len(post_response["image_url_list"]) > 0:
                        log.trace(account_id + " 日志 %s 解析的的所有图片：%s" % (post_url, post_response["image_url_list"]))
                        for image_url in post_response["image_url_list"]:
                            log.step(account_id + " 开始下载第%s张图片 %s" % (image_count, image_url))

                            file_type = image_url.split(".")[-1]
                            image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                            retry_count = 0
                            while True:
                                save_file_return = net.save_net_file(image_url, image_file_path)
                                if save_file_return["status"] == 1:
                                    log.step(account_id + " 第%s张图片下载成功" % image_count)
                                    image_count += 1
                                # 下载失败，并且http_code不是403和404，重试
                                elif save_file_return["status"] == 0 and save_file_return["code"] not in [403, 404] and retry_count <= 5:
                                    retry_count += 1
                                    continue
                                else:
                                    log.error(account_id + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                                break

                if not is_over:
                    page_count += 1

            log.step(account_id + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if image_count > 1:
                log.step(account_id + " 图片开始从下载目录移动到保存目录")
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_id)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_id + " 图片从下载目录移动到保存目录成功")
                else:
                    log.error(account_id + " 创建图片保存目录 %s 失败" % destination_path)
                    tool.process_exit()
            if video_count > 1:
                log.step(account_id + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)
                if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                    log.step(account_id + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_id + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_post_id is not None:
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_post_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            self.thread_lock.release()

            log.step(account_id + " 完成")
        except SystemExit, se:
            if se.code == 0:
                log.step(account_id + " 提前退出")
            else:
                log.error(account_id + " 异常退出")
        except Exception, e:
            log.error(account_id + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Tumblr().main()
