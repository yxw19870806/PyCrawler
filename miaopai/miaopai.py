# -*- coding:UTF-8  -*-
"""
秒拍视频爬虫
http://www.miaopai.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True


# 获取指定账号的所有关注列表
# suid -> 0r9ewgQ0v7UoDptu
def get_follow_list(suid):
    page_count = 1
    follow_list = {}
    while True:
        follow_page_url = "http://www.miaopai.com/gu/follow?page=%s&suid=%s" % (page_count, suid)
        follow_page_response = net.http_request(follow_page_url, json_decode=True)
        if follow_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if robot.check_sub_key(("msg", "stat"), follow_page_response.json_data) and follow_page_response.json_data["stat"].isdigit():
                stat = int(follow_page_response.json_data["stat"]["stat"])
                if stat == 1 or stat == 2:
                    one_page_follow_list = re.findall('<a title="([^"]*)" href="http://www.miaopai.com/u/paike_([^"]*)">', follow_page_response.json_data["msg"])
                    for account_name, account_id in one_page_follow_list:
                        follow_list[account_id] = account_name
                    if stat == 1:
                        page_count += 1
                        continue
        return follow_list


# 获取用户的suid，作为查找指定用户的视频页的凭证
# account_id -> mi9wmdhhof
def get_user_id(account_id):
    index_page_url = "http://www.miaopai.com/u/paike_%s/relation/follow.htm" % account_id
    index_page_response = net.http_request(index_page_url)
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        user_id = tool.find_sub_string(index_page_response.data, '<button class="guanzhu gz" suid="', '" heade="1" token="')
        if user_id:
            return user_id
    return None


# 获取指定页数的所有视频
# suid -> 0r9ewgQ0v7UoDptu
def get_one_page_video(suid, page_count):
    # http://www.miaopai.com/gu/u?page=1&suid=0r9ewgQ0v7UoDptu&fen_type=channel
    index_page_url = "http://www.miaopai.com/gu/u?page=%s&suid=%s&fen_type=channel" % (page_count, suid)
    index_page_response = net.http_request(index_page_url, json_decode=True)
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "video_id_list": [],  # 页面解析出的所有视频id
        "is_over": False  # 是不是最后一页视频
    }
    if index_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取页面中的所有视频id列表
        if robot.check_sub_key(("isall", "msg"), index_page_response.json_data):
            extra_info["is_over"] = bool(index_page_response.json_data["isall"])
            video_id_list = re.findall('data-scid="([^"]*)"', index_page_response.json_data["msg"])
            extra_info["video_id_list"] = map(str, video_id_list)
        else:
            extra_info["is_error"] = True
    index_page_response.extra_info = extra_info
    return index_page_response


# 获取指定id视频的详情页
def get_video_info_page(video_id):
    video_info_page_url = "http://gslb.miaopai.com/stream/%s.json?token=" % video_id
    video_info_page_response = net.http_request(video_info_page_url, json_decode=True)
    extra_info = {
        "video_url": None,  # 页面解析出的视频下载地址
    }
    if video_info_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if robot.check_sub_key(("result",), video_info_page_response.json_data):
            for result in video_info_page_response.json_data["result"]:
                if robot.check_sub_key(("path", "host", "scheme"), result):
                    extra_info["video_url"] = str(result["scheme"]) + str(result["host"]) + str(result["path"])
                    break
    video_info_page_response.extra_info = extra_info
    return video_info_page_response


class MiaoPai(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  video_count  last_video_url
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "", ""])
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

            user_id = get_user_id(account_id)
            if user_id is None:
                log.error(account_name + " suid解析失败")
                tool.process_exit()

            page_count = 1
            video_count = 1
            first_video_id = ""
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页视频" % page_count)

                # 获取指定一页的视频信息
                index_page_response = get_one_page_video(user_id, page_count)
                if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页视频访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(index_page_response.status)))
                    tool.process_exit()

                if index_page_response.extra_info["is_error"]:
                    log.error(account_name + " 第%s页视频解析失败" % page_count)
                    tool.process_exit()

                # 没有视频了
                if index_page_response.extra_info["is_over"] and len(index_page_response.extra_info["video_id_list"]) == 0:
                    if self.account_info[2] != "":
                        log.error(account_name + " 没有找到上次下载的最后一个视频地址")
                    break

                if len(index_page_response.extra_info["video_id_list"]) == 0:
                    log.error(account_name + " 第%s页没有找到视频" % page_count)
                    tool.process_exit()

                log.trace(account_name + " 第%s页解析的所有视频：%s" % (page_count, index_page_response.extra_info["video_id_list"]))

                for video_id in index_page_response.extra_info["video_id_list"]:
                    video_id = str(video_id)

                    # 检查是否已下载到前一次的图片
                    if video_id == self.account_info[2]:
                        is_over = True
                        break

                    # 将第一个视频的id做为新的存档记录
                    if first_video_id == "":
                        first_video_id = video_id

                    # 新增视频导致的重复判断
                    if video_id in unique_list:
                        continue
                    else:
                        unique_list.append(video_id)

                    # 获取视频下载地址
                    video_info_page_response = get_video_info_page(video_id)
                    if video_info_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 视频%s信息页访问失败，原因：%s" % (video_id, robot.get_http_request_failed_reason(video_info_page_response.status)))
                        tool.process_exit()
                    if video_info_page_response.extra_info["video_url"] is None:
                        log.error(account_name + " 视频%s下载地址解析失败" % video_id)
                        tool.process_exit()

                    video_url = video_info_page_response.extra_info["video_url"]
                    log.step(account_name + " 开始下载第%s个视频 %s" % (video_count, video_url))

                    # 第一个视频，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(video_path, 0):
                            log.error(account_name + " 创建视频下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    file_path = os.path.join(video_path, "%04d.mp4" % video_count)
                    save_file_return = net.save_net_file(video_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s个视频下载成功" % video_count)
                        video_count += 1
                    else:
                        log.error(account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_count, video_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_VIDEO_COUNT < video_count:
                        is_over = True
                        break

                if not is_over:
                    page_count += 1

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
            if first_video_id != "":
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
    MiaoPai().main()
