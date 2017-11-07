# -*- coding:UTF-8  -*-
"""
模板
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import json
import os
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_VIDEO_COUNT = 0
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""


# 获取账号全部视频信息
# account_id => 15614906
def get_account_index_page(account_id):
    # http://www.nicovideo.jp/mylist/15614906#+page=1
    account_index_url = "http://www.nicovideo.jp/mylist/%s" % account_id
    account_index_response = net.http_request(account_index_url, method="GET")
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        all_video_info = tool.find_sub_string(account_index_response.data, "Mylist.preload(%s," % account_id, ");").strip()
        try:
            all_video_info = json.loads(all_video_info)
        except ValueError:
            pass
        else:
            # 倒序排列，时间越晚的越前面
            all_video_info.reverse()
            for video_info in all_video_info:
                if robot.check_sub_key(("item_data", "item_id"), video_info) and robot.check_sub_key(("watch_id", "title"), video_info["item_data"]):
                    print video_info["item_data"]["item_id"]  # 投稿时间
                    print video_info["item_data"]["watch_id"]
    return account_index_response


# 根据视频id，获取视频的下载地址
def get_video_url(video_id):
    api_url = "http://api.dmc.nico:2805/api/sessions?_format=xml&suppress_response_codes=true"
    binary_data = '''
<session>
    <recipe_id>nicovideo-sm31207604</recipe_id>
    <content_id>out1</content_id>
    <content_type>movie</content_type>
    <protocol>
        <name>http</name>
        <parameters>
            <http_parameters>
                <method>GET</method>
                <parameters>
                    <http_output_download_parameters>
                        <file_extension>flv</file_extension>
                    </http_output_download_parameters>
                </parameters>
            </http_parameters>
        </parameters>
    </protocol>
    <priority>0.4</priority>
    <content_src_id_sets>
        <content_src_id_set>
            <content_src_ids>
                <src_id_to_mux>
                    <video_src_ids>
                        <string>archive_h264_600kbps_360p</string>
                        <string>archive_h264_300kbps_360p</string>
                    </video_src_ids>
                    <audio_src_ids>
                        <string>archive_aac_64kbps</string>
                    </audio_src_ids>
                </src_id_to_mux>
            </content_src_ids>
        </content_src_id_set>
    </content_src_id_sets>
    <keep_method>
        <heartbeat>
            <lifetime>60000</lifetime>
        </heartbeat>
    </keep_method>
    <timing_constraint>unlimited</timing_constraint>
    <session_operation_auth>
        <session_operation_auth_by_signature>
            <token>
                {"service_id":"nicovideo","player_id":"nicovideo-6-BJ8HluQeSt_1495531398370","recipe_id":"nicovideo-sm31207604","service_user_id":"36746249","protocols":[{"name":"http","auth_type":"ht2"}],"videos":["archive_h264_300kbps_360p","archive_h264_600kbps_360p"],"audios":["archive_aac_64kbps"],"movies":[],"created_time":1495531398000,"expire_time":1495617798000,"content_ids":["out1"],"heartbeat_lifetime":60000,"content_key_timeout":600000,"priority":0.4,"transfer_presets":[]}
            </token>
            <signature>c60d3948e158938e06edce69ecfa52f0cf720ebcadb7bf4846926a33dce747c6</signature>
        </session_operation_auth_by_signature>
    </session_operation_auth>
    <content_auth>
        <auth_type>ht2</auth_type>
        <service_id>nicovideo</service_id>
        <service_user_id>36746249</service_user_id>
        <max_content_count>10</max_content_count>
        <content_key_timeout>600000</content_key_timeout>
    </content_auth>
    <client_info>
        <player_id>nicovideo-6-BJ8HluQeSt_1495531398370</player_id>
    </client_info>
</session>
'''
    # 方便阅读，处理掉空格换行
    binary_data = binary_data.replace("\n", "").replace(" ", "")
    api_response = net.http_request(api_url, method="POST", binary_data=binary_data)
    if api_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        pass
    return api_response


class NicoNico(robot.Robot):
    def __init__(self):
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH

        sys_config = {
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  last_video_id
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

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), TOTAL_VIDEO_COUNT))


class Download(robot.DownloadThread):
    def __init__(self, account_info, thread_lock):
        robot.DownloadThread.__init__(self, account_info, thread_lock)

    def run(self):
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            # 获取视频信息列表
            account_index_response = get_account_index_page(account_id)
            if account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error(account_name + " 视频列表访问失败，原因：%s" % robot.get_http_request_failed_reason(account_index_response.status))
                tool.process_exit()

            video_count = 1
            first_video_id = None
            video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
            for video_info in account_index_response.extra_info["video_info_list"]:
                if not robot.check_sub_key(("item_data",), video_info) or \
                        not robot.check_sub_key(("watch_id", "title"), video_info["item_data"]):
                    log.error(account_name + " 视频信息%s解析失败" % video_info)
                    tool.process_exit()

                # sm30043563
                video_id = str(video_info["item_data"]["watch_id"])

                # 过滤标题中不支持的字符
                video_title = robot.filter_text(video_info["item_data"]["title"])

                # 获取视频下载地址
                video_url = get_video_url(video_id)
                log.step(account_name + " 开始下载第%s个视频 %s %s" % (video_count, video_id, video_url))
                print video_title
                print "%s %s" % (video_id, video_title)
                file_path = os.path.join(video_path, "%s %s.mp4" % (video_id, video_title))
                if net.save_net_file(video_url, file_path):
                    log.step(account_name + " 第%s个视频下载成功" % video_count)
                    video_count += 1
                else:
                    log.error(account_name + " 第%s个视频 %s %s 下载失败" % (video_count, video_id, video_url))

            log.step(account_name + " 下载完毕，总共获得%s个视频" % (video_count - 1))

            # 排序
            if video_count > 1:
                log.step(account_name + " 视频开始从下载目录移动到保存目录")
                destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_name)
                if robot.sort_file(video_path, destination_path, int(self.account_info[3]), 4):
                    log.step(account_name + " 视频从下载目录移动到保存目录成功")
                else:
                    log.error(account_name + " 创建视频保存目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_video_id is not None:
                self.account_info[1] = first_video_id

            # 保存最后的信息
            self.thread_lock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
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
    NicoNico().main()
