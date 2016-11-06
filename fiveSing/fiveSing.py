# -*- coding:UTF-8  -*-
"""
5sing歌曲爬虫
http://5sing.kugou.com/
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

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
GET_VIDEO_COUNT = 0
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取一页的歌曲信息列表，单条歌曲信息的格式：[歌曲id，歌曲标题]
# page_type 页面类型：yc - 原唱、fc - 翻唱
# account_id -> inory
def get_one_page_audio_list(account_id, page_type, page_count):
    # http://changba.com/member/personcenter/loadmore.php?userid=4306405&pageNum=1
    audio_album_url = "http://5sing.kugou.com/%s/%s/%s.html" % (account_id, page_type, page_count)
    audio_album_return_code, audio_album_page = tool.http_request(audio_album_url)[:2]
    if audio_album_return_code == 1:
        return re.findall('<a href="http://5sing.kugou.com/' + page_type + '/([\d]*).html" [\s|\S]*? title="([^"]*)">', audio_album_page)
    return None


# 根据歌曲类型和歌曲id获取歌曲下载地址
def get_audio_url(audio_id, song_type):
    audio_info_url = "http://service.5sing.kugou.com/song/getPermission?songId=%s&songType=%s" % (audio_id, song_type)
    audio_info_return_code, audio_info = tool.http_request(audio_info_url)[:2]
    if audio_info_return_code == 1:
        try:
            audio_info = json.loads(audio_info)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("success", "data"), audio_info):
                if audio_info["success"] and robot.check_sub_key(("fileName",), audio_info["data"]):
                    return str(audio_info["data"]["fileName"])
                elif not audio_info["success"]:
                    return ""
    return None


class FiveSing(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
             robot.SYS_DOWNLOAD_VIDEO: True,
             robot.SYS_SET_COOKIE: (".kugou.com",),
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  last_yc_audio_id  last_fc_audio_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
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
        tool.remove_dir(VIDEO_TEMP_PATH)

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计歌曲%s首" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


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

        # 原创、翻唱
        audio_type_to_index = {"yc": 1, "fc": 2}
        try:
            log.step(account_name + " 开始")

            video_count = 1
            for audio_type in audio_type_to_index.keys():
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name, audio_type)

                page_count = 1
                first_audio_id = "0"
                unique_list = []
                is_over = False
                need_make_download_dir = True
                while not is_over:
                    # 获取指定一页的歌曲信息列表
                    audio_list = get_one_page_audio_list(account_id, audio_type, page_count)

                    if audio_list is None:
                        log.step(account_name + " 第%s页%s歌曲页面获取失败" % (page_count, audio_type))
                        first_audio_id = "0"
                        break  # 存档恢复

                    # 如果为空，表示已经取完了
                    if len(audio_list) == 0:
                        break

                    for audio_info in list(audio_list):
                        audio_id = audio_info[0]
                        audio_title = audio_info[1]
                        for filter_char in ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]:
                            audio_title = audio_title.replace(filter_char, " ")  # 过滤一些windows文件名屏蔽的字符
                        audio_title = audio_title.strip().rstrip(".")  # 去除前后空格以及后缀的.

                        # 检查是否歌曲id小于上次的记录
                        if int(audio_id) <= int(self.account_info[audio_type_to_index[audio_type]]):
                            is_over = True
                            break

                        # 新增歌曲导致的重复判断
                        if audio_id in unique_list:
                            continue
                        else:
                            unique_list.append(audio_id)
                        # 将第一首歌曲id做为新的存档记录
                        if first_audio_id == "0":
                            first_audio_id = str(audio_id)

                        # 获取歌曲的下载地址
                        audio_url = get_audio_url(audio_id, audio_type_to_index[audio_type])
                        if audio_url is None:
                            log.step(account_name + " %s歌曲ID %s，下载地址获取失败" % (audio_type, audio_id))
                            continue
                        if not audio_url:
                            log.step(account_name + " %s歌曲ID %s，暂不提供下载地址" % (audio_type, audio_id))
                            continue

                        log.step(account_name + " 开始下载第%s首歌曲 %s" % (video_count, audio_url))

                        # 第一个视频，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(video_path, 0):
                                log.error(account_name + " 创建视频下载目录 %s 失败" % video_path)
                                tool.process_exit()
                            need_make_download_dir = False

                        file_path = os.path.join(video_path, "%s - %s.mp3" % (audio_id, audio_title))
                        if tool.save_net_file(audio_url, file_path):
                            log.step(account_name + " 第%s首歌曲下载成功" % video_count)
                            video_count += 1
                        else:
                            log.error(account_name + " 第%s首歌曲 %s 下载失败" % (video_count, audio_url))

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_VIDEO_COUNT < video_count:
                            is_over = True
                            break

                    if not is_over:
                        # 获取的歌曲数量少于1页的上限，表示已经到结束了
                        # 如果歌曲数量正好是页数上限的倍数，则由下一页获取是否为空判断
                        if len(audio_list) < 20:
                            is_over = True
                        else:
                            page_count += 1

                # 新的存档记录
                if first_audio_id != "0":
                    self.account_info[audio_type_to_index[audio_type]] = first_audio_id

            log.step(account_name + " 下载完毕，总共获得%s首歌曲" % (video_count - 1))

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
    FiveSing().main()
