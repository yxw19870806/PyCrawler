# -*- coding:UTF-8  -*-
"""
唱吧歌曲爬虫
http://changba.com/
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
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取账号首页页面
def get_account_index_page(account_id):
    account_index_url = "http://changba.com/u/%s" % account_id
    account_index_response = net.http_request(account_index_url)
    extra_info = {
        "user_id": None,  # 页面解析出的user id
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取user id
        user_id = tool.find_sub_string(account_index_response.data, "var userid = '", "'")
        if user_id and robot.is_integer(user_id):
            extra_info["user_id"] = str(user_id)
    account_index_response.extra_info = extra_info
    return account_index_response


# 获取指定页数的所有歌曲信息
# user_id -> 4306405
def get_one_page_audio(user_id, page_count):
    # http://changba.com/member/personcenter/loadmore.php?userid=4306405&pageNum=1
    audit_pagination_url = "http://changba.com/member/personcenter/loadmore.php?userid=%s&pageNum=%s" % (user_id, page_count - 1)
    audit_pagination_response = net.http_request(audit_pagination_url, json_decode=True)
    extra_info = {
        "audio_info_list": [],  # 页面解析出的歌曲信息列表
    }
    if audit_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        for audio_info in audit_pagination_response.json_data:
            extra_audio_info = {
                "audio_id": None,  # 视频自增id
                "audio_title": "",  # 视频标题
                "audio_key": None,  # 视频唯一key
                "type": None,  # 类型，0 MV，1/3 歌曲
                "json_data": audio_info,  # 原始数据
            }
            if (
                robot.check_sub_key(("workid", "songname", "enworkid", "type"), audio_info) and
                robot.is_integer(audio_info["workid"]) and
                robot.is_integer(audio_info["type"]) and int(audio_info["type"]) in (0, 1, 3)
            ):
                # 获取歌曲id
                extra_audio_info["audio_id"] = str(audio_info["workid"])
                # 获取歌曲标题
                extra_audio_info["audio_title"] = str(audio_info["songname"].encode("UTF-8"))
                # 获取歌曲key
                extra_audio_info["audio_key"] = str(audio_info["enworkid"])
                # 类型
                extra_audio_info["type"] = int(audio_info["type"])
            extra_info["audio_info_list"].append(extra_audio_info)
    audit_pagination_response.extra_info = extra_info
    return audit_pagination_response


# 获取指定id的歌曲播放页
# audio_en_word_id => w-ptydrV23KVyIPbWPoKsA
def get_audio_play_page(audio_en_word_id, type):
    audio_play_url = "http://changba.com/s/%s" % audio_en_word_id
    extra_info = {
        "audio_url": None,  # 页面解析出的user id
        "is_delete": False,  # 是不是已经被删除
    }
    audio_play_response = net.http_request(audio_play_url)
    if audio_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if audio_play_response.data.find("该作品可能含有不恰当内容将不能显示。") > -1:
            extra_info["is_delete"] = True
        else:
            # 获取歌曲下载地址
            if type == 1 or type == 3:
                audio_source_url = tool.find_sub_string(audio_play_response.data, 'var a="', '"')
                if audio_source_url:
                    # 从JS处解析的规则
                    special_find = re.findall("userwork/([abc])(\d+)/(\w+)/(\w+)\.mp3", audio_source_url)
                    if len(special_find) == 0:
                        extra_info["audio_url"] = str(audio_source_url)
                    elif len(special_find) == 1:
                        e = int(special_find[0][1], 8)
                        f = int(special_find[0][2], 16) / e / e
                        g = int(special_find[0][3], 16) / e / e
                        if "a" == special_find[0][0] and g % 1000 == f:
                            extra_info["audio_url"] = "http://a%smp3.changba.com/userdata/userwork/%s/%g.mp3" % (e, f, g)
                        else:
                            extra_info["audio_url"] = "http://aliuwmp3.changba.com/userdata/userwork/%s.mp3" % g
            # MV
            else:
                video_source_string = tool.find_sub_string(audio_play_response.data, "<script>jwplayer.utils.qn = '", "';</script>")
                try:
                    video_url = base64.b64decode(video_source_string)
                except TypeError:
                    pass
                else:
                    if video_url:
                        extra_info["audio_url"] = video_url
    audio_play_response.extra_info = extra_info
    return audio_play_response


class ChangBa(robot.Robot):
    def __init__(self):
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
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

            # 查找账号user id
            account_index_response = get_account_index_page(account_id)
            if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(account_name + " 主页访问失败，原因：%s" % robot.get_http_request_failed_reason(account_index_response.status))
                tool.process_exit()

            if not account_index_response.extra_info["user_id"]:
                log.error(account_name + " user id解析失败")
                tool.process_exit()

            page_count = 1
            video_count = 1
            first_audio_id = "0"
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页歌曲" % page_count)

                # 获取一页歌曲
                audit_pagination_response = get_one_page_audio(account_index_response.extra_info["user_id"], page_count)
                if audit_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error(account_name + " 第%s页歌曲访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(audit_pagination_response.status)))
                    tool.process_exit()

                # 如果为空，表示已经取完了
                if audit_pagination_response.extra_info["audio_info_list"] is []:
                    break

                log.trace(account_name + " 第%s页解析的所有歌曲：%s" % (page_count, audit_pagination_response.extra_info["audio_info_list"]))

                for audio_info in audit_pagination_response.extra_info["audio_info_list"]:
                    if audio_info["audio_id"] is None or audio_info["audio_key"] is None:
                        log.error(account_name + " 歌曲信息%s解析失败" % audio_info["json_data"])
                        tool.process_exit()

                    # 检查是否已下载到前一次的歌曲
                    if int(audio_info["audio_id"]) <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 将第一首歌曲的id做为新的存档记录
                    if first_audio_id == "0":
                        first_audio_id = audio_info["audio_id"]

                    # 新增歌曲导致的重复判断
                    if audio_info["audio_id"] in unique_list:
                        continue
                    else:
                        unique_list.append(audio_info["audio_id"])

                    # 获取歌曲播放页
                    audio_play_response = get_audio_play_page(audio_info["audio_key"], audio_info["type"])
                    if audio_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error(account_name + " 歌曲%s《%s》播放页面访问失败，原因：%s" % (audio_info["audio_key"], audio_info["audio_title"], robot.get_http_request_failed_reason(audio_play_response.status)))
                        tool.process_exit()

                    if audio_play_response.extra_info["is_delete"]:
                        continue

                    if audio_play_response.extra_info["audio_url"] is None:
                        log.error(account_name + " 歌曲%s《%s》下载地址解析失败" % (audio_info["audio_key"], audio_info["audio_title"]))
                        tool.process_exit()

                    audio_url = audio_play_response.extra_info["audio_url"]
                    log.step(account_name + " 开始下载第%s首歌曲《%s》 %s" % (video_count, audio_info["audio_title"], audio_url))

                    # 第一首歌曲，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(video_path, 0):
                            log.error(account_name + " 创建歌曲下载目录 %s 失败" % video_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    file_path = os.path.join(video_path, "%s - %s.mp3" % (audio_info["audio_id"], audio_info["audio_title"]))
                    save_file_return = net.save_net_file(audio_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 第%s首歌曲下载成功" % video_count)
                        video_count += 1
                    else:
                        log.error(account_name + " 第%s首歌曲《%s》 %s 下载失败，原因：%s" % (video_count, audio_info["audio_title"], audio_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                if not is_over:
                    # 获取的歌曲数量少于1页的上限，表示已经到结束了
                    # 如果歌曲数量正好是页数上限的倍数，则由下一页获取是否为空判断
                    if len(audit_pagination_response.extra_info["audio_info_list"]) < 20:
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
