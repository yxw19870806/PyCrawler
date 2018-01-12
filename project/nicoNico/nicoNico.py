# -*- coding:UTF-8  -*-
"""
nico nico视频爬虫
http://www.nicovideo.jp/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import HTMLParser
import json
import os
import threading
import time
import traceback

COOKIE_INFO = {}


# 检测登录状态
def check_login():
    if not COOKIE_INFO:
        return False
    index_url = "http://www.nicovideo.jp/"
    index_response = net.http_request(index_url, method="GET", cookies_list=COOKIE_INFO)
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        return index_response.data.find('<span id="siteHeaderUserNickNameContainer">') >= 0
    return False


# 获取账号全部视频信息
# account_id => 15614906
def get_account_index_page(account_id):
    # http://www.nicovideo.jp/mylist/15614906
    account_index_url = "http://www.nicovideo.jp/mylist/%s" % account_id
    account_index_response = net.http_request(account_index_url, method="GET")
    result = {
        "video_info_list": [],  # 所有视频信息
    }
    if account_index_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    elif account_index_response.status == 403:
        raise crawler.CrawlerException("账号发布视频未公开")
    elif account_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(account_index_response.status))
    all_video_info = tool.find_sub_string(account_index_response.data, "Mylist.preload(%s," % account_id, ");").strip()
    if not all_video_info:
        raise crawler.CrawlerException("截取视频列表失败\n%s" % account_index_response.data)
    try:
        all_video_info = json.loads(all_video_info)
    except ValueError:
        raise crawler.CrawlerException("视频列表加载失败\n%s" % account_index_response.data)
    # 倒序排列，时间越晚的越前面
    all_video_info.reverse()
    for video_info in all_video_info:
        result_video_info = {
            "video_id": None,  # 视频id
            "video_title": "",  # 视频标题
        }
        if not crawler.check_sub_key(("item_data",), video_info):
            raise crawler.CrawlerException("视频信息'item_data'字段不存在\n%s" % video_info)
        # 获取视频id
        if not crawler.check_sub_key(("video_id",), video_info["item_data"]):
            raise crawler.CrawlerException("视频信息'video_id'字段不存在\n%s" % video_info)
        video_id = str(video_info["item_data"]["video_id"])
        result_video_info["video_id"] = video_id.replace("sm", "")
        # 获取视频辩题
        if not crawler.check_sub_key(("title",), video_info["item_data"]):
            raise crawler.CrawlerException("视频信息'video_id'字段不存在\n%s" % video_info)
        result_video_info["video_title"] = str(video_info["item_data"]["title"].encode("UTF-8"))
        result["video_info_list"].append(result_video_info)
    return result


# 根据视频id，获取视频的下载地址
def get_video_info(video_id):
    video_play_url = "http://www.nicovideo.jp/watch/sm%s" % video_id
    video_play_response = net.http_request(video_play_url, method="GET", cookies_list=COOKIE_INFO)
    result = {
        "extra_cookie": {},  # 额外的cookie
        "is_delete": False,  # 是否已删除
        "video_url": None,  # 视频地址
    }
    if video_play_response.status == 403:
        result["is_delete"] = True
        return result
    elif video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException("视频播放页访问失败，" + crawler.request_failre(video_play_response.status))
    video_info_string = tool.find_sub_string(video_play_response.data, 'data-api-data="', '" data-environment="')
    if not video_info_string:
        if video_play_response.data.find("<p>この動画が投稿されている公開コミュニティはありません。</p>") > 0:
            result["is_delete"] = True
            return result
        raise crawler.CrawlerException("视频信息截取失败\n%s" % video_play_response.data)
    video_info_string = HTMLParser.HTMLParser().unescape(video_info_string)
    try:
        video_info = json.loads(video_info_string)
    except ValueError:
        raise crawler.CrawlerException("视频信息加载失败\n%s" % video_play_response.data)
    if not crawler.check_sub_key(("video",), video_info):
        raise crawler.CrawlerException("视频信息'video'字段不存在\n%s" % video_info)
    # 旧版本，直接存放视频地址
    # http://www.nicovideo.jp/watch/sm7647845
    if crawler.check_sub_key(("smileInfo",), video_info["video"]):
        if not crawler.check_sub_key(("url",), video_info["video"]["smileInfo"]):
            raise crawler.CrawlerException("视频信息'url'字段不存在\n%s" % video_info)
        result["video_url"] = str(video_info["video"]["smileInfo"]["url"])
        # 返回的cookies
        set_cookie = net.get_cookies_from_response_header(video_play_response.headers)
        result["extra_cookie"] = set_cookie
        return result
    # 新版本，需要再次访问获取视频地址
    if not crawler.check_sub_key(("dmcInfo",), video_info["video"]):
        raise crawler.CrawlerException("视频信息'dmcInfo'字段不存在\n%s" % video_info)
    if not crawler.check_sub_key(("session_api",), video_info["video"]["dmcInfo"]):
        raise crawler.CrawlerException("视频信息'session_api'字段不存在\n%s" % video_info)
    if not crawler.check_sub_key(("player_id", "token", "signature", "recipe_id"), video_info["video"]["dmcInfo"]["session_api"]):
        raise crawler.CrawlerException("视频信息'player_id'、'token'、'signature'字段不存在\n%s" % video_info)
    api_url = "http://api.dmc.nico:2805/api/sessions?_format=json"
    post_data = {
        "session": {
            "recipe_id": video_info["video"]["dmcInfo"]["session_api"]["recipe_id"],
            "content_id": "out1",
            "content_type": "movie",
            "content_src_id_sets": [{
                "content_src_ids": [{
                    "src_id_to_mux": {
                        "video_src_ids": ["archive_h264_2000kbps_720p"],
                        "audio_src_ids": ["archive_aac_192kbps"]
                    }
                }]
            }],
            "timing_constraint": "unlimited",
            "keep_method": {
                "heartbeat": {
                    "lifetime": 120000
                }
            },
            "protocol": {
                "name": "http",
                "parameters": {
                    "http_parameters": {
                        "parameters": {
                            "http_output_download_parameters": {
                                "use_well_known_port": "no",
                                "use_ssl": "no"
                            }
                        }
                    }
                }
            },
            "content_uri": "",
            "session_operation_auth": {
                "session_operation_auth_by_signature": {
                    "token": video_info["video"]["dmcInfo"]["session_api"]["token"],
                    "signature": video_info["video"]["dmcInfo"]["session_api"]["signature"],
                }
            },
            "content_auth": {
                "auth_type": "ht2",
                "content_key_timeout": 600000,
                "service_id": "nicovideo",
                "service_user_id": "36746249"
            },
            "client_info": {
                "player_id": video_info["video"]["dmcInfo"]["session_api"]["player_id"],
            },
            "priority": 0.4
        }
    }
    api_response = net.http_request(api_url, method="POST", binary_data=json.dumps(post_data))
    print api_response.status
    print api_response.data
    if api_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        pass
    return api_response


class NicoNico(crawler.Crawler):
    def __init__(self):
        global COOKIE_INFO

        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_SET_PROXY: True,
            crawler.SYS_GET_COOKIE: {".nicovideo.jp": ()},
        }
        crawler.Crawler.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO = self.cookie_value

        # 解析存档文件
        # account_id  last_video_id
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

        # 检测登录状态
        if not check_login():
            log.error("没有检测到账号登录状态，退出程序！")
            tool.process_exit()

    def main(self):
        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_id], self)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            self.wait_sub_thread()

        # 未完成的数据保存
        if len(self.account_list) > 0:
            tool.write_file(tool.list_to_string(self.account_list.values()), self.temp_save_data_path)

        # 重新排序保存存档文件
        crawler.rewrite_save_file(self.temp_save_data_path, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计视频%s个" % (self.get_run_time(), self.total_video_count))


class Download(crawler.DownloadThread):
    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 3 and self.account_info[2]:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载图片
    def get_crawl_list(self):
        # 获取视频信息列表
        try:
            account_index_response = get_account_index_page(self.account_id)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 视频列表解析失败，原因：%s" % e.message)
            raise

        video_info_list = []
        # 寻找这一页符合条件的视频
        for video_info in account_index_response["video_info_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 检查是否达到存档记录
            if int(video_info["video_id"]) > int(self.account_info[1]):
                video_info_list.append(video_info)
            else:
                break

        return video_info_list

    # 解析单个视频
    def crawl_video(self, video_info):
        try:
            video_info_response = get_video_info(video_info["video_id"])
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 视频%s 《%s》解析失败，原因：%s" % (video_info["video_id"], video_info["video_title"], e.message))
            return

        if video_info_response["is_delete"]:
            log.error(self.account_name + " 视频%s 《%s》已删除，跳过" % (video_info["video_id"], video_info["video_title"]))
            return

        log.step(self.account_name + " 视频%s 《%s》 %s 开始下载" % (video_info["video_id"], video_info["video_title"], video_info_response["video_url"]))

        video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%08d - %s.mp4" % (int(video_info["video_id"]), path.filter_text(video_info["video_title"])))
        cookies_list = COOKIE_INFO
        if video_info_response["extra_cookie"]:
            cookies_list.update(video_info_response["extra_cookie"])
        save_file_return = net.save_net_file(video_info_response["video_url"], video_file_path, cookies_list=cookies_list)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 视频%s 《%s》下载成功" % (video_info["video_id"], video_info["video_title"]))
        else:
            log.error(self.account_name + " 视频%s 《%s》 %s 下载失败，原因：%s" % (video_info["video_id"], video_info["video_title"], video_info_response["video_url"], crawler.download_failre(save_file_return["code"])))
            return

        # 视频下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = video_info["video_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载视频
            video_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_info_list))

            # 从最早的视频开始下载
            while len(video_info_list) > 0:
                video_info = video_info_list.pop()
                log.step(self.account_name + " 开始解析视频 %s 《%s》" % (video_info["video_id"], video_info["video_title"]))
                self.crawl_video(video_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 完成")
        self.notify_main_thread()


if __name__ == "__main__":
    NicoNico().main()
