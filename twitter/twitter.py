# -*- coding:UTF-8  -*-
"""
Twitter图片爬虫
https://twitter.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import sys
import threading
import time
import traceback
import urllib

ACCOUNTS = []
INIT_MAX_ID = "999999999999999999"
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
GET_IMAGE_COUNT = 0
GET_VIDEO_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 根据账号名字获得账号id（字母账号->数字账号)
def get_account_index_page(account_name):
    account_index_url = "https://twitter.com/%s" % account_name
    account_index_response = net.http_request(account_index_url)
    extra_info = {
        "account_id": None,  # 页面解析出的account id
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_id = tool.find_sub_string(account_index_response.data, '<div class="ProfileNav" role="navigation" data-user-id="', '">')
        if account_id and robot.is_integer(account_id):
            extra_info["account_id"] = account_id
    account_index_response.extra_info = extra_info
    return account_index_response


# 获取一页的媒体信息
def get_one_page_media(account_name, position_blog_id):
    media_pagination_url = "https://twitter.com/i/profiles/show/%s/media_timeline" % account_name
    media_pagination_url += "?include_available_features=1&include_entities=1&max_position=%s" % position_blog_id
    media_pagination_response = net.http_request(media_pagination_url, json_decode=True)
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "is_over": False,  # 是不是已经结束（没有获取到任何内容）
        "media_info_list": [],  # 页面解析出的媒体信息列表
        "next_page_position": None  # 页面解析出的下一页指针
    }
    if media_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if (
            robot.check_sub_key(("has_more_items", "items_html", "new_latent_count", "min_position"), media_pagination_response.json_data) and
            robot.is_integer(media_pagination_response.json_data["new_latent_count"]) and
            (robot.is_integer(media_pagination_response.json_data["min_position"]) or media_pagination_response.json_data["min_position"] is None)
        ):
            # 没有任何内容
            if int(media_pagination_response.json_data["new_latent_count"]) == 0 and not str(media_pagination_response.json_data["items_html"]).strip():
                extra_info["is_skip"] = True
            else:
                # tweet信息分组
                temp_tweet_data_list = media_pagination_response.json_data["items_html"].replace("\n", "").replace('<li class="js-stream-item stream-item stream-item"', '\n<li class="js-stream-item stream-item stream-item"').split("\n")
                tweet_data_list = []
                for tweet_data in temp_tweet_data_list:
                    if len(tweet_data) < 50:
                        continue
                    tweet_data = tweet_data.encode("utf-8")
                    # 被圈出来的用户，追加到前面的页面中
                    if tweet_data.find('<div class="account  js-actionable-user js-profile-popup-actionable') >= 0:
                        tweet_data_list[-1] += tweet_data
                    else:
                        tweet_data_list.append(tweet_data)
                if int(media_pagination_response.json_data["new_latent_count"]) == len(tweet_data_list) > 0:
                    for tweet_data in tweet_data_list:
                        extra_media_info = {
                            "blog_id": None,  # 页面解析出的日志id
                            "has_video": False,  # 是不是包含视频
                            "image_url_list": [],  # 页面解析出的图片地址列表
                        }
                        # 获取日志id
                        blog_id = tool.find_sub_string(tweet_data, 'data-tweet-id="', '"')
                        if blog_id and robot.is_integer(blog_id):
                            extra_media_info["blog_id"] = str(blog_id)
                        else:
                            extra_info["is_error"] = True
                            extra_info["media_info_list"] = []
                            break
                        # 获取图片地址列表
                        image_url_list = re.findall('data-image-url="([^"]*)"', tweet_data)
                        extra_media_info["image_url_list"] = map(str, image_url_list)
                        # 判断是不是有视频
                        extra_media_info["has_video"] = tweet_data.find("PlayableMedia--video") >= 0

                        extra_info["media_info_list"].append(extra_media_info)
                    # 判断有没有下一页
                    if media_pagination_response.json_data["has_more_items"]:
                        extra_info["next_page_position"] = str(media_pagination_response.json_data["min_position"])
                else:
                    extra_info["is_error"] = True
        else:
            extra_info["is_error"] = True
    media_pagination_response.extra_info = extra_info
    return media_pagination_response


# 根据视频所在推特的ID，获取视频的下载地址
def get_video_play_page(tweet_id):
    video_play_url = "https://twitter.com/i/videos/tweet/%s" % tweet_id
    video_play_response = net.http_request(video_play_url)
    extra_info = {
        "video_url": None,  # 页面解析出的视频地址
    }
    if video_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 包含m3u8文件地址的处理
        # https://video.twimg.com/ext_tw_video/749759483224600577/pu/pl/DzYugRHcg3WVgeWY.m3u8
        m3u8_file_url = tool.find_sub_string(video_play_response.data, "&quot;video_url&quot;:&quot;", ".m3u8&quot;")
        if m3u8_file_url:
            m3u8_file_url = m3u8_file_url.replace("\\/", "/") + ".m3u8"
            file_url_protocol, file_url_path = urllib.splittype(m3u8_file_url)
            file_url_host = urllib.splithost(file_url_path)[0]
            m3u8_file_response = net.http_request(m3u8_file_url)
            while m3u8_file_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                # 是否包含的是m3u8文件（不同分辨率）
                include_m3u8_file_list = re.findall("(/[\S]*.m3u8)", m3u8_file_response.data)
                if len(include_m3u8_file_list) > 0:
                    # 生成最高分辨率视频所在的m3u8文件地址
                    m3u8_file_url = "%s://%s%s" % (file_url_protocol, file_url_host, include_m3u8_file_list[-1])
                    m3u8_file_response = net.http_request(m3u8_file_url)
                    if m3u8_file_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        break
                ts_url_find = re.findall("(/[\S]*.ts)", m3u8_file_response.data)
                if len(ts_url_find) > 0:
                    ts_url_list = []
                    for ts_file_path in ts_url_find:
                        ts_url_list.append("%s://%s%s" % (file_url_protocol, file_url_host, str(ts_file_path)))
                    extra_info["video_url"] = ts_url_list
                break
        else:
            # 直接包含视频播放地址的处理
            video_url = tool.find_sub_string(video_play_response.data, "&quot;video_url&quot;:&quot;", "&quot;")
            if video_url:
                extra_info["video_url"] = video_url.replace("\\/", "/")
            else:
                # 直接包含视频播放地址的处理
                vmap_file_url = tool.find_sub_string(video_play_response.data, "&quot;vmap_url&quot;:&quot;", "&quot;")
                if vmap_file_url:
                    vmap_file_url = vmap_file_url.replace("\\/", "/")
                    vmap_file_response = net.http_request(vmap_file_url)
                    if vmap_file_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                        video_url = tool.find_sub_string(vmap_file_response.data, "<![CDATA[", "]]>")
                        if video_url:
                            extra_info["video_url"] = str(video_url.replace("\\/", "/"))
    video_play_response.extra_info = extra_info
    return video_play_response


class Twitter(robot.Robot):
    def __init__(self, extra_config=None):
        global GET_IMAGE_COUNT
        global GET_VIDEO_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        GET_VIDEO_COUNT = self.get_video_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_name  image_count  last_image_time
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "", "0", "0", "0"])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(account_list.keys()):
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
            thread = Download(account_list[account_name], self.thread_lock)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(ACCOUNTS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for account_name in ACCOUNTS:
                # account_name  image_count  last_image_time
                new_save_data_file.write("\t".join(account_list[account_name]) + "\n")
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

        account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            account_index_response = get_account_index_page(account_name)
            if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(account_name + " 首页访问访问失败，原因：%s" % robot.get_http_request_failed_reason(account_index_response.status))
                tool.process_exit()
            if account_index_response.extra_info["account_id"] is None:
                log.error(account_name + " account id 解析失败")
                tool.process_exit()

            if self.account_info[1] == "":
                self.account_info[1] = account_index_response.extra_info["account_id"]
            else:
                if self.account_info[1] != account_index_response.extra_info["account_id"]:
                    log.error(account_name + " account id 不符合，原账号已改名")
                    tool.process_exit()

            image_count = 1
            video_count = 1
            position_blog_id = INIT_MAX_ID
            first_tweet_id = "0"
            is_over = False
            is_download_image = IS_DOWNLOAD_IMAGE
            is_download_video = IS_DOWNLOAD_VIDEO
            need_make_image_dir = True
            need_make_video_dir = True
            while not is_over:
                log.step(account_name + " 开始解析position %s后的一页媒体列表" % position_blog_id)

                # 获取指定时间点后的一页图片信息
                media_pagination_response = get_one_page_media(account_name, position_blog_id)
                if media_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " position %s后的一页媒体列表访问失败，原因：%s" % (position_blog_id, robot.get_http_request_failed_reason(media_pagination_response.status)))
                    tool.process_exit()

                if media_pagination_response.extra_info["is_error"]:
                    log.error(account_name + " position %s后的一页媒体列表解析失败" % position_blog_id)
                    tool.process_exit()

                if media_pagination_response.extra_info["is_over"]:
                    break

                log.step(account_name + " position %s后一页解析的所有媒体信息：%s" % (position_blog_id, media_pagination_response.extra_info["media_info_list"]))

                for media_info in media_pagination_response.extra_info["media_info_list"]:
                    if media_info["blog_id"] is None:
                        log.error(account_name + " 媒体数据里的日志id解析失败%s" % media_info)
                        continue

                    log.step(account_name + " 开始解析日志 %s" % media_info["blog_id"])

                    # 检查是否tweet的id小于上次的记录
                    if int(media_info["blog_id"]) <= int(self.account_info[4]):
                        is_over = True
                        break

                    # 将第一个tweet的id做为新的存档记录
                    if first_tweet_id == "0":
                        first_tweet_id = media_info["blog_id"]

                    # 视频
                    if is_download_video and media_info["has_video"]:
                        # 获取视频播放地址
                        video_play_response = get_video_play_page(media_info["blog_id"])
                        if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                            log.error(account_name + " 日志%s的视频播放页访问失败，原因：%s" % (media_info["blog_id"], robot.get_http_request_failed_reason(video_play_response.status)))
                            tool.process_exit()

                        if video_play_response.extra_info["video_url"] is None:
                            log.error(account_name + " 日志%s的视频下载地址解析失败" % media_info["blog_id"])
                            tool.process_exit()

                        video_url = video_play_response.extra_info["video_url"]
                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        # 分割后的ts格式视频
                        if isinstance(video_url, list):
                            video_file_path = os.path.join(video_path, "%04d.ts" % video_count)
                            save_file_return = net.save_net_file_list(video_url, video_file_path)
                        # 其他格式的视频
                        else:
                            video_file_type = video_url.split(".")[-1]
                            video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, video_file_type))
                            save_file_return = net.save_net_file(video_url, video_file_path)

                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url))

                        # 达到配置文件中的下载数量，结束图片下载
                        if 0 < GET_IMAGE_COUNT < image_count:
                            is_download_image = False

                    # 图片
                    if is_download_image:
                        for image_url in media_info["image_url_list"]:
                            log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                            # 第一张图片，创建目录
                            if need_make_image_dir:
                                if not tool.make_dir(image_path, 0):
                                    log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                    tool.process_exit()
                                need_make_image_dir = False

                            file_type = image_url.split(".")[-1].split(":")[0]
                            image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                            for retry_count in range(0, 5):
                                save_file_return = net.save_net_file(image_url, image_file_path)
                                if save_file_return["status"] == 1:
                                    log.step(account_name + " 第%s张图片下载成功" % image_count)
                                    image_count += 1
                                elif save_file_return["status"] == 0 and save_file_return["code"] == 404:
                                    log.error(account_name + " 第%s张图片 %s 已被删除，跳过" % (image_count, image_url))
                                elif save_file_return["status"] == 0 and save_file_return["code"] == 500:
                                    log.step(account_name + " 第%s张图片 %s 下载异常，重试" % (image_count, image_url))
                                    continue
                                else:
                                    log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                                break

                        # 达到配置文件中的下载数量，结束视频下载
                        if 0 < GET_VIDEO_COUNT < video_count:
                            is_download_video = False

                    # 全部达到配置文件中的下载数量，结束
                    if not is_download_image and not is_download_video:
                        is_over = True
                        break

                if not is_over:
                    # 下一页的指针
                    if media_pagination_response.extra_info["next_page_position"] is None:
                        is_over = True
                    else:
                        position_blog_id = media_pagination_response.extra_info["next_page_position"]

            log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    log.step(account_name + " 图片开始从下载目录移动到保存目录")
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[2]), 4):
                        log.step(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建图片子目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    log.step(account_name + " 视频开始从下载目录移动到保存目录")
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                        log.step(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_tweet_id != "0":
                self.account_info[2] = str(int(self.account_info[2]) + image_count - 1)
                self.account_info[3] = str(int(self.account_info[3]) + video_count - 1)
                self.account_info[4] = first_tweet_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_name)
            self.thread_lock.release()

            log.step(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Twitter().main()
