# -*- coding:UTF-8  -*-
"""
美拍视频爬虫
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
TOTAL_VIDEO_COUNT = 0
VIDEO_COUNT_PER_PAGE = 20  # 每次请求获取的视频数量
GET_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True

threadLock = threading.Lock()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


# 获取一页的视频信息
def get_video_page_data(account_id, page_count):
    video_page_url = "http://www.meipai.com/users/user_timeline"
    video_page_url += "?uid=%s&page=%s&count=%s&single_column=1" % (account_id, page_count, VIDEO_COUNT_PER_PAGE)
    video_page_return_code, video_page = tool.http_request(video_page_url)[:2]
    if video_page_return_code == 1:
        try:
            video_page = json.loads(video_page)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("medias", ), video_page):
                return video_page["medias"]
    return None


class MeiPai(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        robot.Robot.__init__(self)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        start_time = time.time()

        if not self.is_download_video:
            print_error_msg("下载视频没有开启，请检查配置！")
            tool.process_exit()

        # 创建视频保存目录
        print_step_msg("创建视频根目录 %s" % VIDEO_DOWNLOAD_PATH)
        if not tool.make_dir(VIDEO_DOWNLOAD_PATH, 0):
            print_error_msg("创建视频根目录 %s 失败" % VIDEO_DOWNLOAD_PATH)
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not tool.set_cookie(self.cookie_path, self.browser_version, ("weibo.com", ".sina.com.cn")):
            print_error_msg("导入浏览器cookies失败")
            tool.process_exit()

        # 寻找存档，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  video_count  last_video_url
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", ""])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("存档文件 %s 不存在" % self.save_data_path)
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
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
            thread = Download(account_list[account_id])
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
        tool.remove_dir(VIDEO_TEMP_PATH)

        # 重新排序保存存档文件
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时%s秒，共计视频%s个" % (duration_time, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]

        try:
            print_step_msg(account_id + " 开始")

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                video_path = os.path.join(VIDEO_TEMP_PATH, account_id)
            else:
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)

            page_count = 1
            video_count = 1
            first_video_id = "0"
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                # 获取指定一页的视频信息
                medias_data = get_video_page_data(account_id, page_count)
                if medias_data is None:
                    print_error_msg(account_id + " 视频列表解析错误")
                    tool.process_exit()

                for media in medias_data:
                    if not robot.check_sub_key(("video", "id"), media):
                        print_error_msg(account_id + " 第%s个视频信：%s解析错误" % (video_count, media))
                        continue

                    video_id = str(media["id"])
                    # 新增视频导致的重复判断
                    if video_id in unique_list:
                        continue
                    else:
                        unique_list.append(video_id)
                    # 将第一张图片的上传时间做为新的存档记录
                    if first_video_id == "0":
                        first_video_id = video_id
                    # 检查是否图片时间小于上次的记录
                    if int(video_id) <= int(self.account_info[2]):
                        is_over = True
                        break

                    video_url = str(media["video"])
                    print_step_msg(account_id + " 开始下载第%s个视频 %s" % (video_count, video_url))
                    file_path = os.path.join(video_path, "%04d.mp4" % video_count)
                    # 第一个视频，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(video_path, 0):
                            print_error_msg(account_id + " 创建视频下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_download_dir = False
                    if tool.save_net_file(video_url, file_path):
                        print_step_msg(account_id + " 第%s个视频下载成功" % video_count)
                        video_count += 1
                    else:
                        print_error_msg(account_id + " 第%s个视频 %s 下载失败" % (video_count, video_url))

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_VIDEO_COUNT < video_count:
                        is_over = True
                        break

                if not is_over:
                    if len(medias_data) >= VIDEO_COUNT_PER_PAGE:
                        page_count += 1
                    else:
                        # 获取的数量小于请求的数量，已经没有剩余视频了
                        is_over = True

            print_step_msg(account_id + " 下载完毕，总共获得%s个视频" % (video_count - 1))

            # 排序
            if IS_SORT and video_count > 1:
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)
                if robot.sort_file(video_path, destination_path, int(self.account_info[1]), 4):
                    print_step_msg(account_id + " 视频从下载目录移动到保存目录成功")
                else:
                    print_error_msg(account_id + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_video_id != "":
                self.account_info[1] = str(int(self.account_info[1]) + video_count - 1)
                self.account_info[2] = first_video_id

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_id + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_id + " 提前退出")
            else:
                print_error_msg(account_id + " 异常退出")
        except Exception, e:
            print_step_msg(account_id + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    MeiPai().main()
