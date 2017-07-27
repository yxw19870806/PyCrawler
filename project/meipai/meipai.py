# -*- coding:UTF-8  -*-
"""
美拍视频爬虫
http://www.meipai.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import base64
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
VIDEO_COUNT_PER_PAGE = 20  # 每次请求获取的视频数量
TOTAL_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取指定账号的所有关注列表
def get_follow_list(account_id):
    max_page_count = 1
    page_count = 1
    follow_list = {}
    while page_count <= max_page_count:
        follow_pagination_url = "http://www.meipai.com/user/%s/friends?p=%s" % (account_id, page_count)
        follow_pagination_response = net.http_request(follow_pagination_url)
        if follow_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            follow_list_find = re.findall('<div class="ucard-info">([\s|\S]*?)</div>', follow_pagination_response.data)
            for follow_info in follow_list_find:
                follow_account_id = tool.find_sub_string(follow_info, '<a hidefocus href="/user/', '"').strip()
                follow_account_name = tool.find_sub_string(follow_info, 'title="', '"')
                follow_list[follow_account_id] = follow_account_name
            if max_page_count == 1:
                page_info = tool.find_sub_string(follow_pagination_response.data, '<div class="paging-wrap">', "</div>")
                if page_info:
                    page_count_find = re.findall("friends\?p=(\d*)", page_info)
                    max_page_count = max(map(int, page_count_find))
            page_count += 1
        else:
            return None
    return follow_list


# 获取指定页数的所有视频
def get_one_page_video(account_id, page_count):
    # http://www.meipai.com/users/user_timeline?uid=22744352&page=1&count=20&single_column=1
    video_pagination_url = "http://www.meipai.com/users/user_timeline?uid=%s&page=%s&count=%s&single_column=1" % (account_id, page_count, VIDEO_COUNT_PER_PAGE)
    video_pagination_response = net.http_request(video_pagination_url, json_decode=True)
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "video_info_list": [],  # 页面解析出的所有视频信息列表
    }
    if video_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("medias",), video_pagination_response.json_data):
            for media_data in video_pagination_response.json_data["medias"]:
                extra_video_info = {
                    "video_id": None,  # 解析出的视频id
                    "video_url": None,  # 解析出的视频下载地址
                    "json_data": media_data,  # 原始数据
                }
                if robot.check_sub_key(("video", "id"), media_data):
                    # 获取视频id
                    extra_video_info["video_id"] = str(media_data["id"])
                    # 获取视频下载地址
                    # 破解于播放器swf文件中com.meitu.cryptography.meipai.Default.decode
                    loc1 = get_hex(str(media_data["video"]))
                    loc2 = get_dec(loc1["hex"])
                    loc3 = sub_str(loc1["str"], loc2["pre"])
                    try:
                        video_url = base64.b64decode(sub_str(loc3, get_pos(loc3, loc2["tail"])))
                    except TypeError:
                        pass
                    else:
                        if video_url.find("http") == 0:
                            extra_video_info["video_url"] = video_url
                extra_info["video_info_list"].append(extra_video_info)
    video_pagination_response.extra_info = extra_info
    return video_pagination_response


def get_hex(arg1):
    return {"str": arg1[4:], "hex": reduce(lambda x, y: y + x, arg1[0:4])}


def get_dec(arg1):
    loc1 = str(int(arg1, 16))
    return {"pre": [int(loc1[0]), int(loc1[1])], "tail": [int(loc1[2]), int(loc1[3])]}


def sub_str(arg1, arg2):
    loc1 = arg1[:arg2[0]]
    loc2 = arg1[arg2[0]: arg2[0] + arg2[1]]
    return loc1 + arg1[arg2[0]:].replace(loc2, "", 1)


def get_pos(arg1, arg2):
    arg2[0] = len(arg1) - arg2[0] - arg2[1]
    return arg2


class MeiPai(robot.Robot):
    def __init__(self):
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_url
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", ""])
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

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                video_path = os.path.join(VIDEO_TEMP_PATH, account_name)
            else:
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            page_count = 1
            video_count = 1
            first_video_id = "0"
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页视频" % page_count)

                # 获取一页视频
                video_pagination_response = get_one_page_video(account_id, page_count)
                if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error("第%s页视频访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(video_pagination_response.status)))
                    tool.process_exit()

                if video_pagination_response.extra_info["is_error"]:
                    log.error(account_name + " 第%s页视频解析失败" % video_count)
                    tool.process_exit()

                log.trace(account_name + " 第%s页解析的全部视频：%s" % (page_count, video_pagination_response.extra_info["video_info_list"]))

                for video_info in video_pagination_response.extra_info["video_info_list"]:
                    if video_info["video_id"] is None:
                        log.error(account_name + " 视频信息%s的视频id解析失败" % video_info["json_data"])
                        tool.process_exit()

                    # 检查是否已下载到前一次的视频
                    if int(video_info["video_id"]) <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 将第一张图片的上传时间做为新的存档记录
                    if first_video_id == "0":
                        first_video_id = video_info["video_id"]

                    # 新增视频导致的重复判断
                    if video_info["video_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(video_info["video_id"])

                    if video_info["video_url"] is None:
                        log.error(account_name + " 视频信息%s的视频地址解析失败" % video_info["json_data"])
                        tool.process_exit()

                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_info["video_url"]))

                    # 第一个视频，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(video_path, 0):
                            log.error(account_name + " 创建视频下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    file_path = os.path.join(video_path, "%04d.mp4" % video_count)
                    save_file_return = net.save_net_file(video_info["video_url"], file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s个视频下载成功" % video_count)
                        video_count += 1
                    else:
                        log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_info["video_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))

                if not is_over:
                    if len(video_pagination_response.extra_info["video_info_list"]) >= VIDEO_COUNT_PER_PAGE:
                        page_count += 1
                    else:
                        # 获取的数量小于请求的数量，已经没有剩余视频了
                        is_over = True

            log.step(account_name + " 下载完毕，总共获得%s个视频" % (video_count - 1))

            # 排序
            if IS_SORT and video_count > 1:
                log.step(account_name + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                if robot.sort_file(video_path, destination_path, int(self.account_info[1]), 4):
                    log.step(account_name + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_video_id != "0":
                self.account_info[1] = str(int(self.account_info[1]) + video_count - 1)
                self.account_info[2] = first_video_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
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
    MeiPai().main()
