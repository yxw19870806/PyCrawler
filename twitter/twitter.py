# -*- coding:UTF-8  -*-
"""
Twitter图片爬虫
https://twitter.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import json
import os
import re
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


# 从cookie中获取auth_token
def get_auth_token():
    from common import robot
    config = robot.read_config(os.path.join(os.getcwd(), "..\\common\\config.ini"))
    # 操作系统&浏览器
    browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
    # cookie
    is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
    if is_auto_get_cookie:
        cookie_path = robot.tool.get_default_browser_cookie_path(browser_type)
    else:
        cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
    return tool.get_cookie_value_from_browser("auth_token", cookie_path, browser_type, (".twitter.com",))


# 根据账号名字获得账号id（字母账号->数字账号)
def get_account_id(account_name):
    account_index_url = "https://twitter.com/%s" % account_name
    account_index_return_code, account_index_page = tool.http_request(account_index_url)[:2]
    if account_index_return_code == 1:
        account_id = tool.find_sub_string(account_index_page, '<div class="ProfileNav" role="navigation" data-user-id="', '">')
        if account_id:
            return account_id
    return None


# 关注指定账号（需要cookies）
# account_id -> 103436496
def follow_account(auth_token, account_id):
    follow_url = "https://twitter.com/i/user/follow"
    follow_data = {"user_id": account_id}
    header_list = {"Cookie": "auth_token=%s;" % auth_token, "Referer": "https://twitter.com/"}
    follow_return_code, follow_data = tool.http_request(follow_url, follow_data, header_list)[:2]
    if follow_return_code == 1:
        try:
            follow_data = json.loads(follow_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("new_state",), follow_data) and follow_data["new_state"] == "following":
                return True
    return False


# 取消关注指定账号（需要cookies）
# account_id -> 103436496
def unfollow_account(auth_token, account_id):
    unfollow_url = "https://twitter.com/i/user/unfollow"
    unfollow_data = {"user_id": account_id}
    header_list = {"Cookie": "auth_token=%s;" % auth_token, "Referer": "https://twitter.com/"}
    unfollow_return_code, unfollow_data = tool.http_request(unfollow_url, unfollow_data, header_list)[:2]
    if unfollow_return_code == 1:
        if robot.check_sub_key(("new_state",), unfollow_data) and unfollow_data["new_state"] == "not-following":
            return True
    return False


# 获取指定账号的全部关注列表（需要cookies）
def get_follow_list(account_name):
    position_id = "2000000000000000000"
    follow_list = []
    # 从cookies中获取auth_token
    auth_token = get_auth_token()
    if auth_token is None:
        return None
    while True:
        follow_page_data = get_follow_page_data(account_name, auth_token, position_id)
        if follow_page_data is not None:
            profile_list = re.findall('<div class="ProfileCard[^>]*data-screen-name="([^"]*)"[^>]*>', follow_page_data["items_html"])
            if len(profile_list) > 0:
                follow_list += profile_list
            if follow_page_data["has_more_items"]:
                position_id = follow_page_data["min_position"]
            else:
                break
        else:
            break
    return follow_list


# 获取指定一页的关注列表
def get_follow_page_data(account_name, auth_token, position_id):
    follow_list_url = "https://twitter.com/%s/following/users?max_position=%s" % (account_name, position_id)
    header_list = {"Cookie": "auth_token=%s;" % auth_token}
    follow_list_return_code, follow_list_data = tool.http_request(follow_list_url, header_list=header_list)[:2]
    if follow_list_return_code == 1:
        try:
            follow_list_data = json.loads(follow_list_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("min_position", "has_more_items", "items_html"), follow_list_data):
                return follow_list_data
    return None


# 获取一页的媒体信息
def get_media_page_data(account_name, data_tweet_id):
    media_page_url = "https://twitter.com/i/profiles/show/%s/media_timeline" % account_name
    media_page_url += "?include_available_features=1&include_entities=1&max_position=%s" % data_tweet_id
    media_page_return_code, media_page_response = tool.http_request(media_page_url)[:2]
    if media_page_return_code == 1:
        try:
            media_page = json.loads(media_page_response)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("has_more_items", "items_html", "new_latent_count", "min_position"), media_page):
                return media_page
    return None


# 从媒体列表中将不同的媒体信息拆分组
def get_tweet_list(media_page_items_html):
    media_page_items_html = media_page_items_html.replace("\n", "").replace('<li class="js-stream-item stream-item stream-item"', '\n<li class="js-stream-item stream-item stream-item"')
    tweet_data_list = media_page_items_html.split("\n")
    tweet_id_list = []
    for tweet_data in tweet_data_list:
        if len(tweet_data) < 50:
            continue
        tweet_data = tweet_data.encode("utf-8")
        # 被圈出来的用户，追加到前面的页面中
        if tweet_data.find('<div class="account  js-actionable-user js-profile-popup-actionable') >= 0:
            tweet_id_list[-1] += tweet_data
        else:
            tweet_id_list.append(tweet_data)
    return tweet_id_list


# 检查tweet中是否包含视频
def check_has_video(tweet_data):
    return tweet_data.find("PlayableMedia--video") >= 0


# 根据视频所在推特的ID，获取视频的下载地址
def get_video_url_list(tweet_id):
    video_page_url = "https://twitter.com/i/videos/tweet/%s" % tweet_id
    video_page_return_code, video_page = tool.http_request(video_page_url)[:2]
    if video_page_return_code == 1:
        # 包含m3u8文件地址的处理
        # https://video.twimg.com/ext_tw_video/749759483224600577/pu/pl/DzYugRHcg3WVgeWY.m3u8
        m3u8_file_url = tool.find_sub_string(video_page, "&quot;video_url&quot;:&quot;", ".m3u8&quot;")
        if m3u8_file_url:
            m3u8_file_url = m3u8_file_url.replace("\\/", "/") + ".m3u8"
            file_url_protocol, file_url_path = urllib.splittype(m3u8_file_url)
            file_url_host = urllib.splithost(file_url_path)[0]
            m3u8_file_return_code, m3u8_file_data = tool.http_request(m3u8_file_url)[:2]
            if m3u8_file_return_code != 1:
                return "ts", []
            # 是否包含的是m3u8文件（不同分辨率）
            include_m3u8_file_list = re.findall("(/[\S]*.m3u8)", m3u8_file_data)
            if len(include_m3u8_file_list) > 0:
                # 生成最高分辨率视频所在的m3u8文件地址
                m3u8_file_url = "%s://%s%s" % (file_url_protocol, file_url_host, include_m3u8_file_list[-1])
                m3u8_file_return_code, m3u8_file_data = tool.http_request(m3u8_file_url)[:2]
                if m3u8_file_return_code != 1:
                    return "ts", []
            ts_url_find = re.findall("(/[\S]*.ts)", m3u8_file_data)
            if len(ts_url_find) > 0:
                ts_url_list = []
                for ts_file_path in ts_url_find:
                    ts_url_list.append("%s://%s%s" % (file_url_protocol, file_url_host, ts_file_path))
                return "ts", ts_url_list
            return "ts", []
        # 直接包含视频播放地址的处理
        video_url = tool.find_sub_string(video_page, "&quot;video_url&quot;:&quot;", "&quot;")
        if video_url:
            video_url = video_url.replace("\\/", "/")
            file_type = video_url.split(".")[-1]
            return file_type, [video_url]
        vmap_file_url = tool.find_sub_string(video_page, "&quot;vmap_url&quot;:&quot;", "&quot;")
        if vmap_file_url:
            vmap_file_url = vmap_file_url.replace("\\/", "/")
            vmap_file_return_code, vmap_file = tool.http_request(vmap_file_url)[:2]
            if vmap_file_return_code:
                media_file_url = tool.find_sub_string(vmap_file, "<![CDATA[", "]]>")
                if media_file_url:
                    file_type = media_file_url.split(".")[-1].split("?")[0]
                    return file_type, media_file_url
    return "", []


# 获取推特中的全部图片下载地址
def get_image_url_list(tweet_data):
    return re.findall('data-image-url="([^"]*)"', tweet_data)


# 将多个ts文件的地址保存为本地视频文件
def save_video(ts_file_list, file_path):
    file_handle = open(file_path, "wb")
    for ts_file_url in ts_file_list:
        ts_file_return_code, ts_file_data = tool.http_request(ts_file_url)[:2]
        if ts_file_return_code == 1:
            file_handle.write(ts_file_data)
        else:
            return False
    file_handle.close()
    return True


# 将图片的二进制数据保存为本地文件
def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


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
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])
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

            image_count = 1
            video_count = 1
            data_tweet_id = INIT_MAX_ID
            first_tweet_id = "0"
            is_over = False
            is_download_image = IS_DOWNLOAD_IMAGE
            is_download_video = IS_DOWNLOAD_VIDEO
            need_make_image_dir = True
            need_make_video_dir = True
            while not is_over:
                log.step(account_name + " 开始解析%s后的一页媒体列表" % data_tweet_id)

                # 获取指定时间点后的一页图片信息
                media_page = get_media_page_data(account_name, data_tweet_id)
                if media_page is None:
                    log.error(account_name + " 媒体列表解析失败")
                    tool.process_exit()

                # 上一页正好获取了全部的媒体信息，所以这一页没有任何内容，完成了，直接退出
                if media_page["new_latent_count"] == 0 and not media_page["has_more_items"]:
                    break

                # 没有返回任何信息
                if not media_page["items_html"].strip():
                    break

                tweet_list = get_tweet_list(media_page["items_html"])
                if len(tweet_list) == 0:
                    log.error(account_name + " 媒体列表拆分失败，items_html：%s" % str(media_page["items_html"]))
                    tool.process_exit()

                if media_page["new_latent_count"] != len(tweet_list):
                    log.error(account_name + " 解析的媒体数量不等于new_latent_count的数值")
                    # tool.process_exit()

                for tweet_data in tweet_list:
                    # 获取tweet_id
                    tweet_id = tool.find_sub_string(tweet_data, 'data-tweet-id="', '"')
                    if not tweet_id:
                        log.error(account_name + " tweet id解析失败，tweet数据：%s" % tweet_data)
                        continue

                    log.step(account_name + " 开始解析tweet %s" % tweet_id)

                    # 检查是否tweet的id小于上次的记录
                    if int(tweet_id) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 将第一个tweet的id做为新的存档记录
                    if first_tweet_id == "0":
                        first_tweet_id = tweet_id

                    # 视频
                    if is_download_video:
                        # 这个tweet是否包含视频
                        if check_has_video(tweet_data):
                            video_file_type, video_url_list = get_video_url_list(tweet_id)
                            if len(video_url_list) > 0:
                                log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url_list))

                                # 第一个视频，创建目录
                                if need_make_video_dir:
                                    if not tool.make_dir(video_path, 0):
                                        log.error(account_name + " 创建图片下载目录 %s 失败" % video_path)
                                        tool.process_exit()
                                    need_make_video_dir = False

                                video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, video_file_type))
                                if save_video(video_url_list, video_file_path):
                                    log.step(account_name + " 第%s个视频下载成功" % video_count)
                                    video_count += 1
                                else:
                                    log.error(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url_list))
                            else:
                                log.error(account_name + " 第%s个视频 没有解析到源地址，tweet id：%s" % (video_count, tweet_id))

                        # 达到配置文件中的下载数量，结束图片下载
                        if 0 < GET_IMAGE_COUNT < image_count:
                            is_download_image = False

                    # 图片
                    if is_download_image:
                        # 匹配获取全部的图片地址
                        image_url_list = get_image_url_list(tweet_data)
                        for image_url in image_url_list:
                            image_url = str(image_url)
                            log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                            image_return_code, image_byte = tool.http_request(image_url)[:2]
                            # 404，不算做错误，图片已经被删掉了
                            if image_return_code == -404:
                                log.error(account_name + " 第%s张图片 %s 已被删除，跳过" % (image_count, image_url))
                            elif image_return_code == 1:
                                # 第一张图片，创建目录
                                if need_make_image_dir:
                                    if not tool.make_dir(image_path, 0):
                                        log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                        tool.process_exit()
                                    need_make_image_dir = False

                                file_type = image_url.split(".")[-1].split(":")[0]
                                image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                                save_image(image_byte, image_file_path)
                                log.step(account_name + " 第%s张图片下载成功" % image_count)
                                image_count += 1
                            else:
                                log.error(account_name + " 第%s张图片 %s 下载失败" % (image_count, image_url))

                        # 达到配置文件中的下载数量，结束视频下载
                        if 0 < GET_VIDEO_COUNT < video_count:
                            is_download_video = False

                    # 全部达到配置文件中的下载数量，结束
                    if not is_download_image and not is_download_video:
                        is_over = True
                        break

                if not is_over:
                    # 查找下一页的data_tweet_id
                    if media_page["has_more_items"]:
                        data_tweet_id = str(media_page["min_position"])
                    else:
                        is_over = True

            log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    log.step(account_name + " 图片开始从下载目录移动到保存目录")
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        log.step(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建图片子目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    log.step(account_name + " 视频开始从下载目录移动到保存目录")
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                        log.step(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_tweet_id != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_tweet_id

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
