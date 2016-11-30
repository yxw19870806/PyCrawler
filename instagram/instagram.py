# -*- coding:utf-8  -*-
"""
Instagram图片&视频爬虫
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
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


# 获取csr_token和session_id并设置全局变量，后续需要设置header才能进行访问数据
def set_token_and_session():
    global CSRF_TOKEN
    global SESSION_ID
    index_url = "https://www.instagram.com/instagram"
    index_page_response = tool.http_request(index_url)
    if index_page_response[0] == 1:
        set_cookie_info = tool.get_response_info(index_page_response[2].info(), 'Set-Cookie')
        if set_cookie_info is not None:
            csrf_token = tool.find_sub_string(set_cookie_info, "csrftoken=", ";")
            session_id = tool.find_sub_string(set_cookie_info, "sessionid=", ";")
            if csrf_token and session_id:
                CSRF_TOKEN = csrf_token
                SESSION_ID = session_id
                return True
    return False


# 根据账号名字获得账号id（字母账号->数字账号)
def get_account_id(account_name):
    search_url = "https://www.instagram.com/web/search/topsearch/?context=blended&rank_token=1&query=%s" % account_name
    for i in range(0, 10):
        search_return_code, search_data = tool.http_request(search_url)[:2]
        if search_return_code == 1:
            try:
                search_data = json.loads(search_data)
            except ValueError:
                continue
            if robot.check_sub_key(("users",), search_data):
                for user in search_data["users"]:
                    if robot.check_sub_key(("user",), user) and robot.check_sub_key(("username", "pk"), user["user"]):
                        if account_name.lower() == str(user["user"]["username"]).lower():
                            return user["user"]["pk"]
        time.sleep(5)
    return None


# 获取指定账号的全部粉丝列表（需要cookies）
# account_id -> 490060609
def get_follow_by_list(account_id):
    cursor = None
    follow_by_list = []
    while True:
        follow_by_page_data = get_one_page_follow_by_list(account_id, cursor)
        if follow_by_page_data is not None:
            for node in follow_by_page_data["nodes"]:
                if robot.check_sub_key(("username", ), node):
                    follow_by_list.append(node["username"])
            if follow_by_page_data["page_info"]["has_next_page"]:
                cursor = follow_by_page_data["page_info"]["end_cursor"]
            else:
                break
        else:
            break
    return follow_by_list


# 获取指定一页的粉丝列表（需要cookies）
# account_id -> 490060609
def get_one_page_follow_by_list(account_id, cursor=None):
    query_url = "https://www.instagram.com/query/"
    # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
    params = "nodes{username},page_info"
    if cursor is None:
        post_data = "q=ig_user(%s){followed_by.first(%s){%s}}" % (account_id, USER_COUNT_PER_PAGE, params)
    else:
        post_data = "q=ig_user(%s){followed_by.after(%s,%s){%s}}" % (account_id, cursor, USER_COUNT_PER_PAGE, params)
    # todo session id error
    # IGSCdaccb7f76627fa16a0d418f32a733030cb4cdeefaaddc5464a3da52eb8acfe06%3AID8fxYoOH96eMPpf4kEWwIhLA9ihMLuO%3A%7B%22_token_ver%22%3A2%2C%22_auth_user_id%22%3A3539660450%2C%22_token%22%3A%223539660450%3Amm50iieIxyG0NWWxuFifs0j23vhA5WpR%3Afd860ccd5c16e35eadf3e0946c00178b50fce7b45a9d09c62498dbbffdc8fa2b%22%2C%22asns%22%3A%7B%2247.89.39.193%22%3A45102%2C%22time%22%3A1480388199%7D%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22last_refreshed%22%3A1480392303.831638%2C%22_platform%22%3A4%2C%22_auth_user_hash%22%3A%22%22%7D
    header_list = {
        "Referer": "https://www.instagram.com/",
        "X-CSRFToken": CSRF_TOKEN,
        "Cookie": "csrftoken=%s; sessionid=%s;" % (CSRF_TOKEN, SESSION_ID),
    }
    follow_by_list_return_code, follow_by_list_data = tool.http_request(query_url, post_data, header_list)[:2]
    if follow_by_list_return_code == 1:
        try:
            follow_by_list_data = json.loads(follow_by_list_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("followed_by",), follow_by_list_data):
                followed_by_data = follow_by_list_data["followed_by"]
                if robot.check_sub_key(("page_info", "nodes"), followed_by_data):
                    if robot.check_sub_key(("end_cursor", "has_next_page"), followed_by_data["page_info"]):
                        return followed_by_data
    return None


# 获取指定账号的全部关注列表（需要cookies）
# account_id -> 490060609
def get_follow_list(account_id):
    cursor = None
    follow_list = []
    while True:
        follow_page_data = get_one_page_follow_list(account_id, cursor)
        if follow_page_data is not None:
            for node in follow_page_data["nodes"]:
                if robot.check_sub_key(("username", ), node):
                    follow_list.append(node["username"])
            if follow_page_data["page_info"]["has_next_page"]:
                cursor = follow_page_data["page_info"]["end_cursor"]
            else:
                break
        else:
            break
    return follow_list


# 获取指定一页的关注列表（需要cookies）
# account_id -> 490060609
def get_one_page_follow_list(account_id, cursor=None):
    query_url = "https://www.instagram.com/query/"
    # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
    params = "nodes{username},page_info"
    if cursor is None:
        post_data = "q=ig_user(%s){follows.first(%s){%s}}" % (account_id, USER_COUNT_PER_PAGE, params)
    else:
        post_data = "q=ig_user(%s){follows.after(%s,%s){%s}}" % (account_id, cursor, USER_COUNT_PER_PAGE, params)
    # todo session id error
    # IGSCdaccb7f76627fa16a0d418f32a733030cb4cdeefaaddc5464a3da52eb8acfe06%3AID8fxYoOH96eMPpf4kEWwIhLA9ihMLuO%3A%7B%22_token_ver%22%3A2%2C%22_auth_user_id%22%3A3539660450%2C%22_token%22%3A%223539660450%3Amm50iieIxyG0NWWxuFifs0j23vhA5WpR%3Afd860ccd5c16e35eadf3e0946c00178b50fce7b45a9d09c62498dbbffdc8fa2b%22%2C%22asns%22%3A%7B%2247.89.39.193%22%3A45102%2C%22time%22%3A1480388199%7D%2C%22_auth_user_backend%22%3A%22accounts.backends.CaseInsensitiveModelBackend%22%2C%22last_refreshed%22%3A1480392303.831638%2C%22_platform%22%3A4%2C%22_auth_user_hash%22%3A%22%22%7D
    header_list = {
        "Referer": "https://www.instagram.com/",
        "X-CSRFToken": CSRF_TOKEN,
        "Cookie": "csrftoken=%s; sessionid=%s;" % (CSRF_TOKEN, SESSION_ID),
    }
    follow_list_return_code, follow_list_data = tool.http_request(query_url, post_data, header_list)[:2]
    if follow_list_return_code == 1:
        try:
            follow_list_data = json.loads(follow_list_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("follows", ), follow_list_data):
                if robot.check_sub_key(("page_info", "nodes"), follow_list_data["follows"]):
                    if robot.check_sub_key(("end_cursor", "has_next_page"), follow_list_data["follows"]["page_info"]):
                        return follow_list_data["follows"]
    return None


# 获取一页的媒体信息
# account_id -> 490060609
def get_one_page_media_data(account_id, cursor):
    # https://www.instagram.com/query/?q=ig_user(490060609){media.after(9999999999999999999,12){nodes{code,date,display_src,is_video},page_info}}
    # node支持的字段：caption,code,comments{count},date,dimensions{height,width},display_src,id,is_video,likes{count},owner{id},thumbnail_src,video_views
    media_page_url = "https://www.instagram.com/query/"
    params = "nodes{code,date,display_src,is_video},page_info"
    post_data = "q=ig_user(%s){media.after(%s,%s){%s}}" % (account_id, cursor, IMAGE_COUNT_PER_PAGE, params)
    header_list = {
        "Referer": "https://www.instagram.com/",
        "X-CSRFToken": CSRF_TOKEN,
        "Cookie": "csrftoken=%s; sessionid=%s;" % (CSRF_TOKEN, SESSION_ID),
    }
    media_data_return_code, media_data,  = tool.http_request(media_page_url, post_data, header_list)[:2]
    if media_data_return_code == 1:
        try:
            media_data = json.loads(media_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("media", ), media_data):
                if robot.check_sub_key(("page_info", "nodes"), media_data["media"]):
                    if robot.check_sub_key(("has_next_page", "end_cursor", ), media_data["media"]["page_info"]):
                        return media_data["media"]
    return None


# 根据日志ID，获取视频下载地址
# post_id -> BKdvRtJBGou
def get_video_url(post_id):
    post_page_url = "https://www.instagram.com/p/%s/" % post_id
    post_page_return_code, post_page = tool.http_request(post_page_url)[:2]
    if post_page_return_code == 1:
        return tool.find_sub_string(post_page, '<meta property="og:video:secure_url" content="', '" />')
    return None


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
        robot.Robot.__init__(self, sys_config, extra_config)

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

        if not set_token_and_session():
            log.error("token和session获取查找失败")
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

            account_id = get_account_id(account_name)
            if account_id is None:
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
                # 获取指定时间后的一页媒体信息
                media_data = get_one_page_media_data(account_id, cursor)
                if media_data is None:
                    log.error(account_name + " 媒体列表解析异常")
                    tool.process_exit()

                nodes_data = media_data["nodes"]
                for photo_info in nodes_data:
                    if not robot.check_sub_key(("is_video", "display_src", "date"), photo_info):
                        log.error(account_name + " 媒体信息解析异常")
                        break
                    if photo_info["is_video"] and not robot.check_sub_key(("code", ), photo_info):
                        log.error(account_name + " 视频code解析异常")
                        break

                    # 检查是否已下载到前一次的图片
                    if int(photo_info["date"]) <= int(self.account_info[3]):
                        is_over = True
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_created_time == "0":
                        first_created_time = str(int(photo_info["date"]))

                    # 图片
                    if IS_DOWNLOAD_IMAGE:
                        image_url = str(photo_info["display_src"].split("?")[0])
                        log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_image_dir:
                            if not tool.make_dir(image_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_image_dir = False

                        file_type = image_url.split(".")[-1]
                        image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                        if tool.save_net_file(image_url, image_file_path):
                            log.step(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error(account_name + " 第%s张图片 %s 下载失败" % (image_count, image_url))

                    # 视频
                    if IS_DOWNLOAD_VIDEO and photo_info["is_video"]:
                        # 根据日志ID获取视频下载地址
                        video_url = get_video_url(photo_info["code"])
                        if video_url is None:
                            log.error(account_name + " 第%s个视频code：%s 无法访问" % (video_count, photo_info["code"]))
                            continue
                        if not video_url:
                            log.error(account_name + " 第%s个视频code：%s 没有获取到下载地址" % (video_count, photo_info["code"]))
                            continue

                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建视频下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                        if tool.save_net_file(video_url, video_file_path):
                            log.step(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    if media_data["page_info"]["has_next_page"]:
                        cursor = str(media_data["page_info"]["end_cursor"])
                    else:
                        is_over = True

            log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        log.step(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
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
