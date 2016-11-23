# -*- coding:UTF-8  -*-
"""
唱吧歌曲爬虫
http://changba.com/
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


# 根据account_id获取user_id
def get_user_id(account_id):
    index_url = "http://changba.com/u/%s" % account_id
    index_return_code, index_page = tool.http_request(index_url)[:2]
    if index_return_code == 1:
        user_id = tool.find_sub_string(index_page, "var userid = '", "'")
        if user_id:
            return user_id
    return None


# 获取一页的歌曲信息，单条歌曲信息的格式：[歌曲id，歌曲名字，歌曲下载地址]
# user_id -> 4306405
def get_one_page_audio_list(user_id, page_count):
    # http://changba.com/member/personcenter/loadmore.php?userid=4306405&pageNum=1
    audio_album_url = "http://changba.com/member/personcenter/loadmore.php?userid=%s&pageNum=%s" % (user_id, page_count)
    audio_album_return_code, audio_album_page = tool.http_request(audio_album_url)[:2]
    if audio_album_return_code == 1:
        try:
            audio_album_page = json.loads(audio_album_page)
        except ValueError:
            pass
        else:
            audio_list = []
            for audio_info in audio_album_page:
                if robot.check_sub_key(("songname", "workid", "enworkid"), audio_info):
                    audio_id = str(audio_info["workid"])
                    audio_name = audio_info["songname"].encode("utf-8")
                    audio_url = str(audio_info["enworkid"])
                    audio_list.append([audio_id, audio_name, audio_url])
            return audio_list
    return None


# 获取歌曲的下载地址
# audio_en_word_id => w-ptydrV23KVyIPbWPoKsA
def get_audio_url(audio_en_word_id):
    audio_index_url = "http://changba.com/s/%s" % audio_en_word_id
    audio_index_return_code, audio_index_page = tool.http_request(audio_index_url)[:2]
    if audio_index_return_code == 1:
        audio_source_url = tool.find_sub_string(audio_index_page, 'var a="', '"')
        if audio_source_url:
            # 从JS处解析的规则
            special_find = re.findall("userwork/([abc])(\d+)/(\w+)/(\w+)\.mp3", audio_source_url)
            if len(special_find) == 0:
                return audio_source_url
            elif len(special_find) == 1:
                e = int(special_find[0][1], 8)
                f = int(special_find[0][2], 16) / e / e
                g = int(special_find[0][3], 16) / e / e
                if "a" == special_find[0][0] and g % 1000 == f:
                    return "http://a%smp3.changba.com/userdata/userwork/%s/%g.mp3" % (e, f, g)
                return "http://aliuwmp3.changba.com/userdata/userwork/%s.mp3" % g
    return None


class ChangBa(robot.Robot):
    def __init__(self):
        global GET_VIDEO_COUNT
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
             robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_VIDEO_COUNT = self.get_video_count
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  last_audio_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
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

        log.step("全部下载完毕，耗时%s秒，共计歌曲%s首" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)

            user_id = get_user_id(account_id)
            if user_id is None:
                log.error(account_name + " userid获取失败")
                tool.process_exit()

            page_count = 0
            video_count = 1
            first_audio_id = "0"
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                # 获取指定一页的歌曲信息
                audio_list = get_one_page_audio_list(user_id, page_count)

                if audio_list is None:
                    log.step(account_name + " 第%s页歌曲列表获取失败" % page_count)
                    first_audio_id = "0"
                    break  # 存档恢复

                # 如果为空，表示已经取完了
                if len(audio_list) == 0:
                    break

                for audio_info in list(audio_list):
                    audio_id = audio_info[0]

                    # 检查是否歌曲id小于上次的记录
                    if int(audio_id) <= int(self.account_info[1]):
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
                    audio_url = get_audio_url(audio_info[2])
                    log.step(account_name + " 开始下载第%s首歌曲 %s" % (video_count, audio_url))

                    # 第一首歌曲，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(video_path, 0):
                            log.error(account_name + " 创建歌曲下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    file_path = os.path.join(video_path, "%s - %s.mp3" % (audio_id, audio_info[1]))
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

            log.step(account_name + " 下载完毕，总共获得%s首歌曲" % (video_count - 1))

            # 新的存档记录
            if first_audio_id != "0":
                self.account_info[1] = first_audio_id

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
    ChangBa().main()
