# -*- coding:UTF-8  -*-
"""
微博图片&视频爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import weiboCommon
import base64
import os
import random
import re
import threading
import time
import traceback
import urllib2

ACCOUNTS = []
INIT_SINCE_ID = "9999999999999999"
IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
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
COOKIE_INFO = {"SUB": ""}


# 获取一页的图片信息
def get_one_page_photo(account_id, page_count):
    photo_pagination_url = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (account_id, IMAGE_COUNT_PER_PAGE, page_count)
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    extra_info = {
        "is_error": True,  # 是不是格式不符合
        "image_info_list": [],  # 页面解析出的所有图片信息列表
        "is_over": False,  # 是不是最后一页图片
    }
    photo_pagination_response = net.http_request(photo_pagination_url, cookies_list=cookies_list, json_decode=True)
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if (
            robot.check_sub_key(("data",), photo_pagination_response.json_data) and
            robot.check_sub_key(("total", "photo_list"), photo_pagination_response.json_data["data"]) and
            robot.is_integer(photo_pagination_response.json_data["data"]["total"])
        ):
            extra_info["is_error"] = False
            for image_info in photo_pagination_response.json_data["data"]["photo_list"]:
                extra_image_info = {
                    "image_time": None,  # 页面解析出的图片上传时间
                    "image_url": None,  # 页面解析出的图片地址
                    "json_data": image_info,  # 原始数据
                }
                # 获取图片上传时间
                if robot.check_sub_key(("timestamp",), image_info) and robot.is_integer(image_info["timestamp"]):
                    extra_image_info["image_time"] = int(image_info["timestamp"])
                else:
                    extra_info["is_error"] = True
                    break
                # 获取图片地址
                if robot.check_sub_key(("pic_host", "pic_name"), image_info):
                    extra_image_info["image_url"] = str(image_info["pic_host"]) + "/large/" + str(image_info["pic_name"])
                else:
                    extra_info["is_error"] = True
                    break

                extra_info["image_info_list"].append(extra_image_info)
            # 检测是不是还有下一页 总的图片数量 / 每页显示的图片数量 = 总的页数
            extra_info["is_over"] = page_count >= (photo_pagination_response.json_data["data"]["total"] * 1.0 / IMAGE_COUNT_PER_PAGE)
    photo_pagination_response.extra_info = extra_info
    return photo_pagination_response


# 获取一页的视频信息
# page_id -> 1005052535836307
def get_one_page_video(account_page_id, since_id):
    # http://weibo.com/p/aj/album/loading?type=video&since_id=9999999999999999&page_id=1005052535836307&page=1&ajax_call=1
    video_pagination_url = "http://weibo.com/p/aj/album/loading"
    video_pagination_url += "?type=video&since_id=%s&page_id=%s&page=1&ajax_call=1&__rnd=%s" % (since_id, account_page_id, int(time.time() * 1000))
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "video_play_url_list": [],  # 页面解析出的所有视频地址列表
        "next_page_since_id": None,  # 页面解析出的下一页视频的指针
    }
    video_pagination_response = net.http_request(video_pagination_url, cookies_list=cookies_list, json_decode=True)
    if video_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if(
            robot.check_sub_key(("code", "data"), video_pagination_response.json_data) and
            robot.is_integer(video_pagination_response.json_data["code"]) and
            int(video_pagination_response.json_data["code"]) == 100000
        ):
            page_html = video_pagination_response.json_data["data"].encode("UTF-8")
            # 获取视频播放地址类别
            video_play_url_list = re.findall('<a target="_blank" href="([^"]*)"><div ', page_html)
            if len(video_play_url_list) == 0:
                if since_id != INIT_SINCE_ID or page_html.find("还没有发布过视频") == -1:
                    extra_info["is_error"] = True
            else:
                extra_info["video_play_url_list"] = map(str, video_play_url_list)
            # 获取下一页视频的指针
            next_page_since_id = tool.find_sub_string(page_html, "type=video&owner_uid=&viewer_uid=&since_id=", '">')
            if robot.is_integer(next_page_since_id):
                extra_info["next_page_since_id"] = next_page_since_id
        else:
            extra_info["is_error"] = True
    video_pagination_response.extra_info = extra_info
    return video_pagination_response


# 从视频播放页面中提取下载地址
def get_video_url(video_play_url):
    video_url = None
    # http://miaopai.com/show/Gmd7rwiNrc84z5h6S9DhjQ__.htm
    if video_play_url.find("miaopai.com/show/") >= 0:  # 秒拍
        video_id = tool.find_sub_string(video_play_url, "miaopai.com/show/", ".")
        video_info_url = "http://gslb.miaopai.com/stream/%s.json?token=" % video_id
        video_info_response = net.http_request(video_info_url, json_decode=True)
        if video_info_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if (
                robot.check_sub_key(("status", "result"), video_info_response.json_data) and
                robot.is_integer(video_info_response.json_data["status"]) and
                int(video_info_response.json_data["status"]) == 200
            ):
                for video_info in video_info_response.json_data["result"]:
                    if robot.check_sub_key(("path", "host", "scheme"), video_info):
                        video_url = str(video_info["scheme"] + video_info["host"] + video_info["path"])
                        break
    # http://video.weibo.com/show?fid=1034:e608e50d5fa95410748da61a7dfa2bff
    elif video_play_url.find("video.weibo.com/show?fid=") >= 0:  # 微博视频
        cookies_list = {"SUB": COOKIE_INFO["SUB"]}
        video_play_response = net.http_request(video_play_url, cookies_list=cookies_list)
        if video_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            video_url = tool.find_sub_string(video_play_response.data, "video_src=", "&")
            if not video_url:
                video_url = tool.find_sub_string(video_play_response.data, 'flashvars="list=', '"')
            if video_url:
                video_url = str(urllib2.unquote(video_url))
            else:
                video_url = None
        elif video_play_response.status == 404:
            video_url = ""
    # http://www.meipai.com/media/98089758
    elif video_play_url.find("www.meipai.com/media") >= 0:  # 美拍
        video_play_response = net.http_request(video_play_url)
        if video_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            video_url_find = re.findall('<meta content="([^"]*)" property="og:video:url">', video_play_response.data)
            if len(video_url_find) == 1:
                loc1 = meipai_get_hex(video_url_find[0])
                loc2 = meipai_get_dec(loc1["hex"])
                loc3 = meipai_sub_str(loc1["str"], loc2["pre"])
                try:
                    video_url = base64.b64decode(meipai_sub_str(loc3, meipai_get_pos(loc3, loc2["tail"])))
                except TypeError:
                    pass
                else:
                    if video_url.find("http") != 0:
                        video_url = None
    # http://v.xiaokaxiu.com/v/0YyG7I4092d~GayCAhwdJQ__.html
    elif video_play_url.find("v.xiaokaxiu.com/v/") >= 0:  # 小咖秀
        video_id = video_play_url.split("/")[-1].split(".")[0]
        video_url = "http://gslb.miaopai.com/stream/%s.mp4" % video_id
    # http://www.weishi.com/t/2000546051794045
    elif video_play_url.find("www.weishi.com/t/") >= 0:  # 微视
        video_play_response = net.http_request(video_play_url)
        if video_play_response == net.HTTP_RETURN_CODE_SUCCEED:
            video_id_find = re.findall('<div class="vBox js_player"[\s]*id="([^"]*)"', video_play_response.data)
            if len(video_id_find) == 1:
                video_id = video_play_url.split("/")[-1]
                video_info_url = "http://wsi.weishi.com/weishi/video/downloadVideo.php?vid=%s&device=1&id=%s" % (video_id_find[0], video_id)
                video_info_response = net.http_request(video_info_url, json_decode=True)
                if video_info_response.status == net.HTTP_RETURN_CODE_SUCCEED:
                    if robot.check_sub_key(("data",), video_info_response.json_data) and robot.check_sub_key(("url",), video_play_response.json_data["data"]):
                        video_url = str(random.choice(video_info_response.json_data["data"]["url"]))
    else:  # 其他视频，暂时不支持，收集看看有没有
        log.error("其他第三方视频：" + video_play_url)
        video_url = ""
    return video_url


def meipai_get_hex(arg1):
    return {"str": arg1[4:], "hex": reduce(lambda x, y: y + x, arg1[0:4])}


def meipai_get_dec(arg1):
    loc1 = str(int(arg1, 16))
    return {"pre": [int(loc1[0]), int(loc1[1])], "tail": [int(loc1[2]), int(loc1[3])]}


def meipai_sub_str(arg1, arg2):
    loc1 = arg1[:arg2[0]]
    loc2 = arg1[arg2[0]: arg2[0] + arg2[1]]
    return loc1 + arg1[arg2[0]:].replace(loc2, "", 1)


def meipai_get_pos(arg1, arg2):
    arg2[0] = len(arg1) - arg2[0] - arg2[1]
    return arg2


class Weibo(robot.Robot):
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
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_GET_COOKIE: {
                ".sina.com.cn": (),
                ".login.sina.com.cn": (),
            },
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
        COOKIE_INFO.update(self.cookie_value)

    def main(self):
        global ACCOUNTS
        global COOKIE_INFO

        # 检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
            new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
            if new_cookies_list:
                COOKIE_INFO.update(new_cookies_list)
            # 再次检测登录状态
            if not weiboCommon.check_login(COOKIE_INFO):
                log.error("没有检测到您的登录信息，无法获取图片或视频，自动退出程序！")
                tool.process_exit()

        # 解析存档文件
        # account_id  image_count  last_image_time  video_count  last_video_url  (account_name)
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", ""])
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
        if len(self.account_info) >= 6 and self.account_info[5]:
            account_name = self.account_info[5]
        else:
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

            # 图片
            image_count = 1
            page_count = 1
            first_image_time = "0"
            unique_list = []
            is_over = False
            need_make_image_dir = True
            while IS_DOWNLOAD_IMAGE and (not is_over):
                log.step(account_name + " 开始解析第%s页图片" % page_count)

                # 获取指定一页图片的信息
                photo_pagination_response = get_one_page_photo(account_id, page_count)
                if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页图片访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(photo_pagination_response.status)))
                    tool.process_exit()

                if photo_pagination_response.extra_info["is_error"]:
                    log.error(account_name + " 第%s页图片%s解析失败" % (page_count, photo_pagination_response.json_data))
                    tool.process_exit()

                log.trace(account_name + "第%s页解析的全部图片信息：%s" % (page_count, photo_pagination_response.extra_info["image_info_list"]))

                for image_info in photo_pagination_response.extra_info["image_info_list"]:
                    if image_info["image_time"] is None:
                        log.error(account_name + " 第%s页图片%s解析失败" % (page_count, photo_pagination_response.json_data))
                        tool.process_exit()

                    # 检查是否图片时间小于上次的记录
                    if image_info["image_time"] <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_image_time == "0":
                        first_image_time = str(image_info["image_time"])

                    # 新增图片导致的重复判断
                    if image_info["image_url"] in unique_list:
                        continue
                    else:
                        unique_list.append(image_info["image_url"])

                    log.step(account_name + " 开始下载第%s张图片 %s" % (image_count, image_info["image_url"]))

                    # 第一张图片，创建目录
                    if need_make_image_dir:
                        if not tool.make_dir(image_path, 0):
                            log.error(account_name + " 创建图片下载目录 %s 失败" % image_path)
                            tool.process_exit()
                        need_make_image_dir = False

                    file_type = image_info["image_url"].split(".")[-1]
                    if file_type.find("/") != -1:
                        file_type = "jpg"
                    image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                    save_file_return = net.save_net_file(image_info["image_url"], image_file_path)
                    if save_file_return["status"] == 1:
                        if weiboCommon.check_image_invalid(image_file_path):
                            os.remove(tool.change_path_encoding(image_file_path))
                            log.error(account_name + " 第%s张图片 %s 资源已被删除，跳过" % (image_count, image_info["image_url"]))
                        else:
                            log.step(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                    else:
                        log.error(account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_count, image_info["image_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if not is_over:
                    if photo_pagination_response.extra_info["is_over"]:
                        is_over = True
                    else:
                        page_count += 1

            # 视频
            video_count = 1
            first_video_url = ""
            while IS_DOWNLOAD_VIDEO:
                # 获取账号首页
                account_index_response = weiboCommon.get_account_index_page(account_id)
                if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 首页访问失败，原因：%s" % robot.get_http_request_failed_reason(account_index_response.status))
                    break

                if account_index_response.extra_info["account_page_id"] is None:
                    log.error(account_name + " 账号page id解析失败")
                    break

                is_over = False
                need_make_video_dir = True
                since_id = INIT_SINCE_ID
                while not is_over:
                    log.step(account_name + " 开始解析%s后一页视频" % since_id)

                    # 获取指定时间点后的一页视频信息
                    video_pagination_response = get_one_page_video(account_index_response.extra_info["account_page_id"], since_id)
                    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " %s后的一页视频访问失败，原因：%s" % (since_id, robot.get_http_request_failed_reason(video_pagination_response.status)))
                        first_video_url = ""  # 存档恢复
                        break

                    if video_pagination_response.extra_info["is_error"]:
                        log.error(account_name + " %s后的一页视频%s解析失败" % (since_id, video_pagination_response.json_data))
                        first_video_url = ""  # 存档恢复
                        break

                    # 匹配获取全部的视频页面
                    log.trace(account_name + "since_id：%s中的全部视频：%s" % (since_id, video_pagination_response.extra_info["video_play_url_list"]))

                    for video_play_url in video_pagination_response.extra_info["video_play_url_list"]:
                        # 检查是否是上一次的最后视频
                        if self.account_info[4] == video_play_url:
                            is_over = True
                            break

                        # 将第一个视频的地址做为新的存档记录
                        if first_video_url == "":
                            first_video_url = video_play_url

                        log.step(account_name + " 开始解析第%s个视频 %s" % (video_count, video_play_url))

                        # 获取这个视频的下载地址
                        video_url = get_video_url(video_play_url)
                        if video_url is None:
                            log.error(account_name + " 第%s个视频 %s 没有解析到下载地址" % (video_count, video_play_url))
                            continue

                        if video_url is "":
                            continue

                        log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                        # 第一个视频，创建目录
                        if need_make_video_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建图片下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_video_dir = False

                        video_file_path = os.path.join(video_path, "%04d.mp4" % video_count)
                        save_file_return = net.save_net_file(video_url, video_file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " 第%s个视频下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s个视频 %s（%s) 下载失败，原因：%s" % (video_count, video_play_url, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_VIDEO_COUNT < video_count:
                            is_over = True
                            break

                    if not is_over:
                        # 获取下一页的since_id
                        since_id = video_pagination_response.extra_info["next_page_since_id"]
                        if not since_id:
                            break

                # 有历史记录，并且此次没有获得正常结束的标记，说明历史最后的视频已经被删除了
                if self.account_info[4] != "" and first_video_url != "" and not is_over:
                    log.error(account_name + " 没有找到上次下载的最后一个视频地址")

                break

            log.step(account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if first_image_time != "0":
                    log.step(account_name + " 图片开始从下载目录移动到保存目录")
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        log.step(account_name + " 图片从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if first_video_url != "":
                    log.step(account_name + " 视频开始从下载目录移动到保存目录")
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                        log.step(account_name + " 视频从下载目录移动到保存目录成功")
                    else:
                        log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_image_time != "0":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_image_time
            if first_video_url != "":
                self.account_info[3] = str(int(self.account_info[3]) + video_count - 1)
                self.account_info[4] = first_video_url

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
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
    Weibo().main()
