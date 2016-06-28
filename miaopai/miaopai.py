# -*- coding:UTF-8  -*-
'''
Created on 2016-6-16

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool
import json
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ''
VIDEO_DOWNLOAD_PATH = ''
NEW_SAVE_DATA_PATH = ''
IS_SORT = 1
IS_DOWNLOAD_VIDEO = 1

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


def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


class Miaopai(robot.Robot):
    def __init__(self):
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_VIDEO

        robot.Robot.__init__(self)

        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path

        IS_SORT = self.is_sort
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        start_time = time.time()

        # 视频保存目录
        if IS_DOWNLOAD_VIDEO == 1:
            print_step_msg("创建视频根目录：" + VIDEO_DOWNLOAD_PATH)
            if not tool.make_dir(VIDEO_DOWNLOAD_PATH, 0):
                print_error_msg("创建视频根目录：" + VIDEO_DOWNLOAD_PATH + " 失败，程序结束！")
                tool.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not tool.set_cookie(self.cookie_path, self.browser_version, ('weibo.com', '.sina.com.cn')):
            print_error_msg("导入浏览器cookies失败，程序结束！")
            tool.process_exit()

        # 寻找存档，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  video_count  last_video_url
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", ""])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("存档文件：" + self.save_data_path + "不存在，程序结束！")
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
        print_step_msg("全部下载完毕，耗时" + str(duration_time) + "秒，共计视频" + str(TOTAL_VIDEO_COUNT) + "个")


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]

        try:
            print_step_msg(account_id + " 开始")

            # 初始化数据
            last_video_url = self.account_info[2]
            self.account_info[2] = ""  # 置空，存放此次的最后视频地址
            page_count = 1
            video_count = 1
            need_make_download_dir = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                video_path = os.path.join(VIDEO_TEMP_PATH, account_id)
            else:
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)

            suid = ""
            index_page_url = "http://www.miaopai.com/u/paike_%s" % account_id
            [index_page_return_code, index_page] = tool.http_request(index_page_url)[:2]
            if index_page_return_code == 1:
                suid_find = re.findall('<button class="guanzhu gz" suid="([^"]*)" heade="1" token="">\+关注</button>', index_page)
                if len(suid_find) == 1:
                    suid = suid_find[0]
                    trace(account_id + " suid: " + suid)
                else:
                    print_error_msg(account_id + " suid获取失败")
            else:
                print_error_msg(account_id + " 无法访问首页" + index_page_url)

            while suid != "" and IS_DOWNLOAD_VIDEO == 1:
                media_page_url = "http://www.miaopai.com/gu/u?page=%s&suid=%s&fen_type=channel" % (page_count, suid)

                [media_page_return_code, media_page] = tool.http_request(media_page_url)[:2]
                if media_page_return_code != 1:
                    print_error_msg(account_id + " 第" + str(page_count) + "页视频列表获取失败")
                    break

                try:
                    media_page = json.loads(media_page)
                except:
                    print_error_msg(account_id + " 返回的视频列表不是一个JSON数据")
                    break
                if 'isall' not in media_page:
                    print_error_msg(account_id + " 在视频列表：" + str(media_page) + " 中没有找到'isall'字段")
                    break
                if "msg" not in media_page:
                    print_error_msg(account_id + " 在视频列表：" + str(media_page) + " 中没有找到'msg'字段")
                    break

                msg_data = media_page['msg']
                scid_list = re.findall('data-scid="([^"]*)"', msg_data)
                if len(scid_list) > 0:
                    for scid in scid_list:
                        video_url = "http://wsqncdn.miaopai.com/stream/%s.mp4" % str(scid)

                        # 文件类型
                        file_path = os.path.join(video_path, str("%04d" % video_count) + ".mp4")

                        # 保存视频
                        print_step_msg(account_id + " 开始下载第 " + str(video_count) + "个视频：" + video_url)
                        # 第一个视频，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(video_path, 0):
                                print_error_msg(account_id + " 创建视频下载目录： " + video_path + " 失败，程序结束！")
                                tool.process_exit()
                            need_make_download_dir = False
                        if tool.save_image(video_url, file_path):
                            print_step_msg(account_id + " 第" + str(video_count) + "个视频下载成功")
                            video_count += 1
                        else:
                            print_error_msg(account_id + " 第" + str(video_count) + "个视频 " + video_url + " 下载失败")
                else:
                    print_error_msg(account_id + " 在视频列表：" + str(media_page) + " 中没有找到视频scid")
                    break

                if media_page['isall']:
                    break

                page_count += 1

            # 如果有错误且没有发现新的视频，复原旧数据
            if self.account_info[2] == "" and last_video_url != "":
                self.account_info[2] = last_video_url

            print_step_msg(account_id + " 下载完毕，总共获得" + str(video_count - 1) + "个视频")

            # 排序
            if IS_SORT == 1:
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[4]), 4):
                        print_step_msg(account_id + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_id + " 创建视频保存目录： " + destination_path + " 失败，程序结束！")
                        tool.process_exit()

            self.account_info[1] = str(int(self.account_info[1]) + video_count - 1)

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_id + " 完成")
        except Exception, e:
            print_step_msg(account_id + " 异常")
            print_error_msg(str(e) + "\n" + str(traceback.print_exc()))


if __name__ == "__main__":
    tool.restore_process_status()
    Miaopai().main()
