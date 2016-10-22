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

threadLock = threading.Lock()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


# 根据账号名字获得账号id（字母账号->数字账号)
def get_account_id(account_name):
    search_url = "https://www.instagram.com/web/search/topsearch/?context=blended&rank_token=1&query=%s" % account_name
    for i in range(0, 10):
        search_return_code, search_data = tool.http_request(search_url)[:2]
        if search_return_code == 1:
            try:
                search_data = json.loads(search_data)
            except ValueError:
                pass
            else:
                if robot.check_sub_key(("users", ), search_data):
                    for user in search_data["users"]:
                        if robot.check_sub_key(("user", ), user) and robot.check_sub_key(("username", "pk"), user["user"]):
                            if account_name.lower() == str(user["user"]["username"]).lower():
                                return user["user"]["pk"]
        time.sleep(5)
    return None


# 获取指定账号的全部粉丝列表（需要cookies）
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


# 获取指定一页的粉丝列表
def get_one_page_follow_by_list(account_id, cursor=None):
    follow_by_list_url = "https://www.instagram.com/query/"
    # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
    if cursor is None:
        follow_by_list_url += "?q=ig_user(%s){followed_by.first(%s){nodes{username},page_info}}" % (account_id, USER_COUNT_PER_PAGE)
    else:
        follow_by_list_url += "?q=ig_user(%s){followed_by.after(%s,%s){nodes{username},page_info}}" % (account_id, cursor, USER_COUNT_PER_PAGE)
    follow_by_list_return_code, follow_by_list_data = tool.http_request(follow_by_list_url)[:2]
    if follow_by_list_return_code == 1:
        try:
            follow_by_list_data = json.loads(follow_by_list_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("followed_by", ), follow_by_list_data):
                if robot.check_sub_key(("page_info", "nodes"), follow_by_list_data["followed_by"]):
                    if robot.check_sub_key(("end_cursor", "has_next_page"), follow_by_list_data["followed_by"]["page_info"]):
                        return follow_by_list_data["followed_by"]
    return None


# 获取指定账号的全部关注列表（需要cookies）
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


# 获取指定一页的关注列表
def get_one_page_follow_list(account_id, cursor=None):
    follow_list_url = "https://www.instagram.com/query/"
    # node支持的字段：id,is_verified,followed_by_viewer,requested_by_viewer,full_name,profile_pic_url,username
    if cursor is None:
        follow_list_url += "?q=ig_user(%s){follows.first(%s){nodes{username},page_info}}" % (account_id, USER_COUNT_PER_PAGE)
    else:
        follow_list_url += "?q=ig_user(%s){follows.after(%s,%s){nodes{username},page_info}}" % (account_id, cursor, USER_COUNT_PER_PAGE)
    follow_list_return_code, follow_list_data = tool.http_request(follow_list_url)[:2]
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
    media_page_url = "https://www.instagram.com/query/"
    # node支持的字段：caption,code,comments{count},date,dimensions{height,width},display_src,id,is_video,likes{count},owner{id},thumbnail_src,video_views
    media_page_url += "?q=ig_user(%s){media.after(%s,%s){nodes{code,date,display_src,is_video},page_info}}" % (account_id, cursor, IMAGE_COUNT_PER_PAGE)
    photo_page_return_code, media_page_response = tool.http_request(media_page_url)[:2]
    if photo_page_return_code == 1:
        try:
            media_page = json.loads(media_page_response)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("media", ), media_page):
                if robot.check_sub_key(("page_info", "nodes"), media_page["media"]):
                    if robot.check_sub_key(("has_next_page", "end_cursor", ), media_page["media"]["page_info"]):
                        return media_page["media"]
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

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if tool.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_name])
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
        tool.remove_dir(IMAGE_TEMP_PATH)
        tool.remove_dir(VIDEO_TEMP_PATH)

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_name = self.account_info[0]

        try:
            print_step_msg(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            account_id = get_account_id(account_name)
            if account_id is None:
                print_error_msg(account_name + " account id 查找失败")
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
                    print_error_msg(account_name + " 媒体列表解析异常")
                    tool.process_exit()

                nodes_data = media_data["nodes"]
                for photo_info in nodes_data:
                    if not robot.check_sub_key(("is_video", "display_src", "date"), photo_info):
                        print_error_msg(account_name + " 媒体信息解析异常")
                        break
                    if photo_info["is_video"] and not robot.check_sub_key(("code", ), photo_info):
                        print_error_msg(account_name + " 视频code解析异常")
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
                        print_step_msg(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))

                        # 第一张图片，创建目录
                        if need_make_image_dir:
                            if not tool.make_dir(image_path, 0):
                                print_error_msg(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_image_dir = False
                        file_type = image_url.split(".")[-1]
                        image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                        if tool.save_net_file(image_url, image_file_path):
                            print_step_msg(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            print_error_msg(account_name + " 第%s张图片 %s 下载失败" % (image_count, image_url))

                    # 视频
                    if IS_DOWNLOAD_VIDEO and photo_info["is_video"]:
                        # 根据日志ID获取视频下载地址
                        video_url = get_video_url(photo_info["code"])
                        if video_url is None:
                            print_error_msg(account_name + " 第%s个视频code：%s 无法访问" % (video_count, photo_info["code"]))
                            continue
                        if not video_url:
                            print_error_msg(account_name + " 第%s个视频code：%s 没有获取到下载地址" % (video_count, photo_info["code"]))
                            continue

                        print_step_msg(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                print_error_msg(account_name + " 创建视频下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False
                        file_type = video_url.split(".")[-1]
                        video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                        if tool.save_net_file(video_url, video_file_path):
                            print_step_msg(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            print_error_msg(account_name + " 第%s个视频 %s 下载失败" % (video_count, video_url))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    if media_data["page_info"]["has_next_page"]:
                        cursor = str(media_data["page_info"]["end_cursor"])
                    else:
                        is_over = True

            print_step_msg(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                        print_step_msg(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_created_time != "":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_created_time

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_name)
            threadLock.release()

            print_step_msg(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_name + " 提前退出")
            else:
                print_error_msg(account_name + " 异常退出")
        except Exception, e:
            print_error_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Instagram().main()
