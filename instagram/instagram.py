# -*- coding:utf-8  -*-
"""
Instagram图片&视频爬虫
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import json
import os
import threading
import time
import traceback

ACCOUNTS = []
INIT_CURSOR = "9999999999999999999"
CSRF_TOKEN = ""
SESSION_ID = ""
IMAGE_COUNT_PER_PAGE = 12
USER_COUNT_PER_PAGE = 50
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True


# 获取csr_token并设置全局变量，后续需要设置header才能进行访问数据
def set_csrf_token():
    global CSRF_TOKEN
    home_page_url = "https://www.instagram.com/instagram"
    home_page_response = net.http_request(home_page_url)
    if home_page_response.status == net.HTTP_RETURN_CODE_SUCCEED and "Set-Cookie" in home_page_response.headers:
        csrf_token = tool.find_sub_string(home_page_response.headers["Set-Cookie"], "csrftoken=", ";")
        if csrf_token:
            CSRF_TOKEN = csrf_token
            return True
    return False


# 从cookie中获取登录的sessionid
def set_session_id():
    global SESSION_ID
    config = robot.read_config(os.path.join(os.getcwd(), "..\\common\\config.ini"))
    # 操作系统&浏览器
    browser_type = robot.get_config(config, "BROWSER_TYPE", 2, 1)
    # cookie
    is_auto_get_cookie = robot.get_config(config, "IS_AUTO_GET_COOKIE", True, 4)
    if is_auto_get_cookie:
        cookie_path = robot.tool.get_default_browser_cookie_path(browser_type)
    else:
        cookie_path = robot.get_config(config, "COOKIE_PATH", "", 0)
    all_cookie_from_browser = tool.get_all_cookie_from_browser(browser_type, cookie_path)
    if "www.instagram.com" in all_cookie_from_browser and "sessionid" in all_cookie_from_browser["www.instagram.com"]:
        SESSION_ID = all_cookie_from_browser["www.instagram.com"]["sessionid"]


# 获取指定账号的所有粉丝列表（需要cookies）
# account_id -> 490060609
def get_follow_by_list(account_id):
    # 从cookies中获取session id的值
    set_session_id()
    # 从页面中获取csrf token的值
    if not CSRF_TOKEN:
        set_csrf_token()

    cursor = None
    follow_by_list = []
    while True:
        query_page_url = "https://www.instagram.com/query/"
        # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
        if cursor is None:
            post_data = {"q": "ig_user(%s){followed_by.first(%s){nodes{username},page_info}}" % (account_id, USER_COUNT_PER_PAGE)}
        else:
            post_data = {"q": "ig_user(%s){followed_by.after(%s,%s){nodes{username},page_info}}" % (account_id, cursor, USER_COUNT_PER_PAGE)}
        header_list = {"Referer": "https://www.instagram.com/", "X-CSRFToken": CSRF_TOKEN, "Cookie": "csrftoken=%s; sessionid=%s;" % (CSRF_TOKEN, SESSION_ID)}
        follow_by_page_response = net.http_request(query_page_url, post_data=post_data, header_list=header_list, json_decode=True)
        if follow_by_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if robot.check_sub_key(("followed_by",), follow_by_page_response.json_data) \
                    and robot.check_sub_key(("page_info", "nodes"), follow_by_page_response.json_data["followed_by"]):
                for node in follow_by_page_response.json_data["followed_by"]["nodes"]:
                    if robot.check_sub_key(("username",), node):
                        follow_by_list.append(node["username"])
                if robot.check_sub_key(("end_cursor", "has_next_page"), follow_by_page_response.json_data["followed_by"]["page_info"]):
                    if follow_by_page_response.json_data["followed_by"]["page_info"]["has_next_page"]:
                        cursor = follow_by_page_response.json_data["followed_by"]["page_info"]["end_cursor"]
                        continue
        break
    return follow_by_list


# 获取指定账号的所有关注列表（需要cookies）
# account_id -> 490060609
def get_follow_list(account_id):
    # 从cookies中获取session id的值
    set_session_id()
    # 从页面中获取csrf token的值
    if not CSRF_TOKEN:
        set_csrf_token()

    cursor = None
    follow_list = []
    while True:
        query_page_url = "https://www.instagram.com/query/"
        # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
        if cursor is None:
            post_data = {"q": "ig_user(%s){follows.first(%s){nodes{username},page_info}}" % (account_id, USER_COUNT_PER_PAGE)}
        else:
            post_data = {"q": "ig_user(%s){follows.after(%s,%s){nodes{username},page_info}}" % (account_id, cursor, USER_COUNT_PER_PAGE)}
        header_list = {"Referer": "https://www.instagram.com/", "X-CSRFToken": CSRF_TOKEN, "Cookie": "csrftoken=%s; sessionid=%s;" % (CSRF_TOKEN, SESSION_ID)}
        follow_page_response = net.http_request(query_page_url, post_data=post_data, header_list=header_list, json_decode=True)
        if follow_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if robot.check_sub_key(("follows",), follow_page_response.json_data) \
                    and robot.check_sub_key(("page_info", "nodes"), follow_page_response.json_data["follows"]):
                for node in follow_page_response.json_data["follows"]["nodes"]:
                    if robot.check_sub_key(("username",), node):
                        follow_list.append(node["username"])
                if robot.check_sub_key(("end_cursor", "has_next_page"), follow_page_response.json_data["follows"]["page_info"]):
                    if follow_page_response.json_data["follows"]["page_info"]["has_next_page"]:
                        cursor = follow_page_response.json_data["follows"]["page_info"]["end_cursor"]
                        continue
        break
    return follow_list


# 根据账号名字获得账号id（字母账号->数字账号)
def get_owner_id(account_name):
    search_page_url = "https://www.instagram.com/web/search/topsearch/?context=blended&rank_token=1&query=%s" % account_name
    for i in range(0, 10):
        search_page_response = net.http_request(search_page_url, json_decode=True)
        if search_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if robot.check_sub_key(("users",), search_page_response.json_data):
                for user in search_page_response.json_data["users"]:
                    if robot.check_sub_key(("user",), user) and robot.check_sub_key(("username", "pk"), user["user"]):
                        if account_name.lower() == str(user["user"]["username"]).lower():
                            return user["user"]["pk"]
        time.sleep(5)
    return None


# 获取指定页数的所有媒体
# account_id -> 490060609
def get_one_page_media(account_id, cursor):
    # https://www.instagram.com/query/?q=ig_user(490060609){media.after(9999999999999999999,12){nodes{code,date,display_src,is_video},page_info}}
    # node支持的字段：caption,code,comments{count},date,dimensions{height,width},display_src,id,is_video,likes{count},owner{id},thumbnail_src,video_views
    query_page_url = "https://www.instagram.com/query/"
    post_data = {"q": "ig_user(%s){media.after(%s,%s){nodes{code,date,display_src,is_video},page_info}}" % (account_id, cursor, IMAGE_COUNT_PER_PAGE)}
    header_list = {"Referer": "https://www.instagram.com/", "X-CSRFToken": CSRF_TOKEN, "Cookie": "csrftoken=%s" % CSRF_TOKEN}
    return net.http_request(query_page_url, post_data=post_data, header_list=header_list, json_decode=True)


# 获取指定id的视频播放页
# post_id -> BKdvRtJBGou
def get_video_play_page(post_id):
    video_play_page_url = "https://www.instagram.com/p/%s/" % post_id
    video_play_page_response = net.http_request(video_play_page_url)
    extra_info = {
        "video_url": None,  # 页面解析出的图片地址列表
    }
    if video_play_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        extra_info["video_url"] = tool.find_sub_string(video_play_page_response.data, '<meta property="og:video:secure_url" content="', '" />')
    video_play_page_response.extra_info = extra_info
    return video_play_page_response


class Instagram(robot.Robot):
    def __init__(self, extra_config=None):
        global GET_IMAGE_COUNT
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
        robot.Robot.__init__(self, sys_config, extra_config, use_urllib3=True)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
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
        # account_name  image_count  video_count  last_created_time
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])
        ACCOUNTS = account_list.keys()

        if not set_csrf_token():
            log.error("token设置失败")
            tool.process_exit()

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

            owner_id = get_owner_id(account_name)
            if owner_id is None:
                log.error(account_name + " account id 查找失败")
                tool.process_exit()

            image_count = 1
            video_count = 1
            cursor = INIT_CURSOR
            first_created_time = "0"
            is_over = False
            need_make_image_dir = True
            need_make_video_dir = True
            while not is_over:
                log.step(account_name + " 开始解析cursor %s的媒体信息" % cursor)

                # 获取指定时间后的一页媒体信息
                media_page_response = get_one_page_media(owner_id, cursor)
                if media_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " cursor %s的媒体信息访问失败，原因：%s" % (cursor, robot.get_http_request_failed_reason(media_page_response.status)))
                    tool.process_exit()

                if not robot.check_sub_key(("media",), media_page_response.json_data) or not robot.check_sub_key(("page_info", "nodes"), media_page_response.json_data["media"]) \
                        or not robot.check_sub_key(("has_next_page", "end_cursor"), media_page_response.json_data["media"]["page_info"]):
                    log.error(account_name + " cursor %s的媒体信息%s解析失败" % (cursor, media_page_response.json_data))
                    tool.process_exit()

                log.trace(account_name + " cursor %s获取的所有媒体信息：%s" % (cursor, media_page_response.json_data["media"]["nodes"]))

                for media_info in media_page_response.json_data["media"]["nodes"]:
                    if not robot.check_sub_key(("is_video", "display_src", "date"), media_info):
                        log.error(account_name + " 媒体信息解析异常")
                        break
                    if media_info["is_video"] and not robot.check_sub_key(("code",), media_info):
                        log.error(account_name + " 视频code解析异常")
                        break

                    # 检查是否已下载到前一次的图片
                    if int(media_info["date"]) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_created_time == "0":
                        first_created_time = str(int(media_info["date"]))

                    # 图片
                    if IS_DOWNLOAD_IMAGE:
                        image_url = str(media_info["display_src"].split("?")[0])
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_image_dir:
                            if not tool.make_dir(image_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_image_dir = False

                        file_type = image_url.split(".")[-1]
                        image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                        save_file_return = net.save_net_file(image_url, image_file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 视频
                    if IS_DOWNLOAD_VIDEO and media_info["is_video"]:
                        # 获取视频播放页
                        video_play_page_response = get_video_play_page(media_info["code"])
                        if video_play_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                            log.error(account_name + " 第%s个视频 %s 播放页访问失败，原因：%s" % (video_count, media_info["code"], robot.get_http_request_failed_reason(video_play_page_response.status)))
                            tool.process_exit()
                        if not video_play_page_response.extra_info["video_url"]:
                            log.error(account_name + " 第%s个视频 %s 下载地址解析失败" % (video_count, media_info["code"]))
                            continue

                        video_url = video_play_page_response.extra_info["video_url"]
                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建视频下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                        save_file_return = net.save_net_file(video_url, video_file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    if media_page_response.json_data["media"]["page_info"]["has_next_page"]:
                        cursor = str(media_page_response.json_data["media"]["page_info"]["end_cursor"])
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
                        log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
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
            if first_created_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_created_time

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
    Instagram().main()
