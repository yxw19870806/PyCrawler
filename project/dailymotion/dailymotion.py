# -*- coding:UTF-8  -*-
"""
dailymotion视频爬虫
http://www.dailymotion.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import json
import os
import random
import threading
import time
import traceback
from common import *

AUTHORIZATION = None
FIRST_CHOICE_RESOLUTION = 720


# 初始化session。获取authorization
def init_session():
    global AUTHORIZATION
    index_url = "http://www.dailymotion.com"
    index_page_response = net.http_request(index_url, method="GET")
    page_data = tool.find_sub_string(index_page_response.data, "var __PLAYER_CONFIG__ = ", ";\n")
    if index_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException("首页，" + crawler.request_failre(index_page_response.status))
    if not page_data:
        raise crawler.CrawlerException("页面信息截取失败\n%s" % index_page_response.data)
    page_data = tool.json_decode(page_data)
    if page_data is None:
        raise crawler.CrawlerException("页面信息加载失败\n%s" % index_page_response.data)
    if not crawler.check_sub_key(("context",), page_data):
        raise crawler.CrawlerException("页面信息'context'字段不存在\n%s" % page_data)
    if not crawler.check_sub_key(("api",), page_data["context"]):
        raise crawler.CrawlerException("页面信息'api'字段不存在\n%s" % page_data)
    if not crawler.check_sub_key(("auth_url", "client_id", "client_secret", ), page_data["context"]["api"]):
        raise crawler.CrawlerException("页面信息'api'字段不存在\n%s" % page_data)
    post_data = {
        "client_id": page_data["context"]["api"]["client_id"],
        "client_secret": page_data["context"]["api"]["client_secret"],
        "grant_type": "client_credentials",
        "visitor_id": tool.generate_random_string(32, 6),
        "traffic_segment": random.randint(100000, 999999)
    }
    oauth_response = net.http_request(page_data["context"]["api"]["auth_url"], method="POST", fields=post_data, json_decode=True)
    if oauth_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException("获取token页%s，%s\n%s" % (page_data["context"]["api"]["auth_url"], crawler.request_failre(oauth_response.status), post_data))
    if not crawler.check_sub_key(("access_token", ), oauth_response.json_data):
        raise crawler.CrawlerException("授权返回信息'access_token'字段不存在\n%s" % oauth_response.json_data)
    AUTHORIZATION = oauth_response.json_data["access_token"]


# 获取视频列表
def get_one_page_video(account_id, page_count):
    api_url = "https://graphql.api.dailymotion.com/"
    post_data = {
        "operationName": "CHANNEL_VIDEOS_QUERY",
        "variables": {
            "channel_xid": account_id,
            "uri": "/%s/videos" % account_id,
            "page": page_count,
            "sort": "recent",
        },
        "query": "fragment CHANNEL_BASE_FRAGMENT on Channel {\n  id\n  xid\n  name\n  displayName\n  isArtist\n  logoURL(size: \"x60\")\n  isFollowed\n  accountType\n  __typename\n}\n\nfragment CHANNEL_IMAGES_FRAGMENT on Channel {\n  coverURLx375: coverURL(size: \"x375\")\n  __typename\n}\n\nfragment CHANNEL_UPDATED_FRAGMENT on Channel {\n  isFollowed\n  stats {\n    views {\n      total\n      __typename\n    }\n    followers {\n      total\n      __typename\n    }\n    videos {\n      total\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment CHANNEL_COMPLETE_FRAGMENT on Channel {\n  ...CHANNEL_BASE_FRAGMENT\n  ...CHANNEL_IMAGES_FRAGMENT\n  ...CHANNEL_UPDATED_FRAGMENT\n  description\n  coverURL1024x: coverURL(size: \"1024x\")\n  coverURL1920x: coverURL(size: \"1920x\")\n  externalLinks {\n    facebookURL\n    twitterURL\n    websiteURL\n    instagramURL\n    __typename\n  }\n  __typename\n}\n\nfragment CHANNEL_FRAGMENT on Channel {\n  id\n  xid\n  name\n  displayName\n  isArtist\n  logoURL(size: \"x60\")\n  coverURLx375: coverURL(size: \"x375\")\n  isFollowed\n  __typename\n}\n\nfragment VIDEO_FRAGMENT on Video {\n  id\n  xid\n  title\n  viewCount\n  duration\n  createdAt\n  channel {\n    ...CHANNEL_FRAGMENT\n    __typename\n  }\n  thumbURLx240: thumbnailURL(size: \"x240\")\n  thumbURLx360: thumbnailURL(size: \"x360\")\n  thumbURLx480: thumbnailURL(size: \"x480\")\n  thumbURLx720: thumbnailURL(size: \"x720\")\n  __typename\n}\n\nfragment METADATA_FRAGMENT on Neon {\n  web(uri: $uri) {\n    author\n    description\n    title\n    metadatas {\n      attributes {\n        name\n        content\n        __typename\n      }\n      __typename\n    }\n    language {\n      codeAlpha2\n      __typename\n    }\n    country {\n      codeAlpha2\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment LOCALIZATION_FRAGMENT on Localization {\n  me {\n    id\n    country {\n      codeAlpha2\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nquery CHANNEL_VIDEOS_QUERY($channel_xid: String!, $sort: String, $page: Int!, $uri: String!) {\n  localization {\n    ...LOCALIZATION_FRAGMENT\n    __typename\n  }\n  views {\n    id\n    neon {\n      id\n      ...METADATA_FRAGMENT\n      __typename\n    }\n    __typename\n  }\n  channel(xid: $channel_xid) {\n    ...CHANNEL_COMPLETE_FRAGMENT\n    channel_videos_all_videos: videos(sort: $sort, page: $page, first: 30) {\n      pageInfo {\n        hasNextPage\n        nextPage\n        __typename\n      }\n      edges {\n        node {\n          ...VIDEO_FRAGMENT\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
    }
    header_list = {
        "authorization": "Bearer " + AUTHORIZATION,
        "origin": "http://www.dailymotion.com",
    }
    result = {
        "is_over": False,  # 是不是最后一页
        "video_info_list": [],  # 全部视频信息
    }
    api_response = net.http_request(api_url, method="POST", binary_data=json.dumps(post_data), header_list=header_list, json_decode=True)
    if api_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(api_response.status))
    if not crawler.check_sub_key(("data",), api_response.json_data):
        raise crawler.CrawlerException("返回信息'data'字段不存在\n%s" % api_response.json_data)
    if not crawler.check_sub_key(("channel",), api_response.json_data["data"]):
        raise crawler.CrawlerException("返回信息'channel'字段不存在\n%s" % api_response.json_data)
    if not crawler.check_sub_key(("channel_videos_all_videos",), api_response.json_data["data"]["channel"]):
        raise crawler.CrawlerException("返回信息'channel_videos_all_videos'字段不存在\n%s" % api_response.json_data)
    # 获取所有视频
    if not crawler.check_sub_key(("edges",), api_response.json_data["data"]["channel"]["channel_videos_all_videos"]):
        raise crawler.CrawlerException("返回信息'edges'字段不存在\n%s" % api_response.json_data)
    if not isinstance(api_response.json_data["data"]["channel"]["channel_videos_all_videos"]["edges"], list):
        raise crawler.CrawlerException("返回信息'edges'字段类型不正确\n%s" % api_response.json_data)
    for video_info in api_response.json_data["data"]["channel"]["channel_videos_all_videos"]["edges"]:
        result_video_info = {
            "video_id": None,  # 视频id
            "video_time": None,  # 视频上传时间
            "video_title": "",  # 视频标题
        }
        if not crawler.check_sub_key(("node",), video_info):
            raise crawler.CrawlerException("视频信息'node'字段不存在\n%s" % video_info)
        # 获取视频id
        if not crawler.check_sub_key(("xid",), video_info["node"]):
            raise crawler.CrawlerException("视频信息'xid'字段不存在\n%s" % video_info)
        result_video_info["video_id"] = str(video_info["node"]["xid"])
        # 获取视频上传时间
        if not crawler.check_sub_key(("createdAt",), video_info["node"]):
            raise crawler.CrawlerException("视频信息'createdAt'字段不存在\n%s" % video_info)
        result_video_info["video_time"] = int(time.mktime(time.strptime(video_info["node"]["createdAt"], "%Y-%m-%dT%H:%M:%S+00:00")))
        # 获取视频标题
        if not crawler.check_sub_key(("title",), video_info["node"]):
            raise crawler.CrawlerException("视频信息'title'字段不存在\n%s" % video_info)
        result_video_info["video_title"] = video_info["node"]["title"].encode("UTF-8")
        result["video_info_list"].append(result_video_info)
    # 判断是不是最后一页
    if not crawler.check_sub_key(("pageInfo",), api_response.json_data["data"]["channel"]["channel_videos_all_videos"]):
        raise crawler.CrawlerException("返回信息'pageInfo'字段不存在\n%s" % api_response.json_data)
    if not crawler.check_sub_key(("hasNextPage",), api_response.json_data["data"]["channel"]["channel_videos_all_videos"]["pageInfo"]):
        raise crawler.CrawlerException("返回信息'hasNextPage'字段不存在\n%s" % api_response.json_data)
    if api_response.json_data["data"]["channel"]["channel_videos_all_videos"]["pageInfo"]["hasNextPage"] is False:
        result["is_over"] = True
    return result


# 获取指定视频
def get_video_page(video_id):
    # 获取视频播放页
    # http://www.dailymotion.com/video/x6lgrfa
    video_play_url = "http://www.dailymotion.com/video/%s" % video_id
    video_play_response = net.http_request(video_play_url, method="GET")
    result = {
        "video_url": None,  # 视频地址
    }
    if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_play_response.status))
    video_data = tool.find_sub_string(video_play_response.data, "var __PLAYER_CONFIG__ = ", ";\n")
    if not video_data:
        raise crawler.CrawlerException("截取视频信息失败\n%s" % video_play_response.data)
    video_data = tool.json_decode(video_data)
    if video_data is None:
        raise crawler.CrawlerException("视频信息加载失败\n%s" % video_play_response.data)
    if not crawler.check_sub_key(("metadata",), video_data):
        raise crawler.CrawlerException("视频信息'metadata'字段不存在\n%s" % video_data)
    # 查找最高分辨率的视频源地址
    if not crawler.check_sub_key(("qualities",), video_data["metadata"]):
        raise crawler.CrawlerException("视频信息'qualities'字段不存在\n%s" % video_data["metadata"])
    # 各个分辨率下的视频地址
    resolution_to_url = {}
    for video_resolution in video_data["metadata"]["qualities"]:
        if not crawler.is_integer(video_resolution):
            continue
        if int(video_resolution) not in [144, 240, 380, 480, 720, 1080]:
            log.error("unknown video quality " + video_resolution)
        for video_info in video_data["metadata"]["qualities"][video_resolution]:
            if not crawler.check_sub_key(("type", "url"), video_info):
                raise crawler.CrawlerException("最高分辨率视频信息'type'或'url'字段不存在\n%s" % video_info)
            if str(video_info["type"]) == "video/mp4":
                resolution_to_url[int(video_resolution)] = str(video_info["url"])
    if len(resolution_to_url) == 0:
        raise crawler.CrawlerException("匹配不同分辨率视频源失败\n%s" % video_data["metadata"]["qualities"])
    # 优先使用配置中的分辨率
    if FIRST_CHOICE_RESOLUTION in resolution_to_url:
        result["video_url"] = resolution_to_url[FIRST_CHOICE_RESOLUTION]
    # 如果没有这个分辨率的视频
    else:
        # 大于配置中分辨率的所有视频中分辨率最小的那个
        for resolution in sorted(resolution_to_url.keys()):
            if resolution > FIRST_CHOICE_RESOLUTION:
                result["video_url"] = resolution_to_url[FIRST_CHOICE_RESOLUTION]
                break
        # 如果还是没有，则所有视频中分辨率最大的那个
        if result["video_url"] is None:
            result["video_url"] = resolution_to_url[max(resolution_to_url)]
    return result


class DailyMotion(crawler.Crawler):
    def __init__(self):
        global FIRST_CHOICE_RESOLUTION
        sys_config = {
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_APP_CONFIG: (
                ("VIDEO_QUALITY", 6, crawler.CONFIG_ANALYSIS_MODE_INTEGER),
            ),
        }
        crawler.Crawler.__init__(self, sys_config)
        video_quality = self.app_config["VIDEO_QUALITY"]
        if video_quality == 1:
            FIRST_CHOICE_RESOLUTION = 144
        elif video_quality == 2:
            FIRST_CHOICE_RESOLUTION = 240
        elif video_quality == 3:
            FIRST_CHOICE_RESOLUTION = 380
        elif video_quality == 4:
            FIRST_CHOICE_RESOLUTION = 480
        elif video_quality == 5:
            FIRST_CHOICE_RESOLUTION = 720
        elif video_quality == 6:
            FIRST_CHOICE_RESOLUTION = 1080
        else:
            log.error("配置文件config.ini中key为'video_quality'的值必须是一个1~6的整数，使用程序默认设置")

        # 解析存档文件
        # account_id  video_time
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

        # 生成authorization，用于访问视频页
        try:
            init_session()
        except crawler.CrawlerException, e:
            log.error("生成authorization失败，原因：%s" % e.message)
            raise

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
    is_find = False

    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        log.step(self.account_id + " 开始")

    # 获取所有可下载视频
    def get_crawl_list(self):
        page_count = 1
        video_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的相册
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_id + " 开始解析第%s页视频" % page_count)

            try:
                blog_pagination_response = get_one_page_video(self.account_id, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_id + " 视频列表解析失败，原因：%s" % e.message)
                raise

            log.trace(self.account_id + " 解析的全部视频：%s" % blog_pagination_response["video_info_list"])

            # 寻找这一页符合条件的日志
            for video_info in blog_pagination_response["video_info_list"]:
                # 检查是否达到存档记录
                if video_info["video_time"] > int(self.account_info[1]):
                    video_info_list.append(video_info)
                else:
                    is_over = True

            if not is_over:
                if blog_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1
        return video_info_list

    # 解析单个视频
    def crawl_video(self, video_info):
        # 获取指定视频信息
        try:
            video_response = get_video_page(video_info["video_id"])
        except crawler.CrawlerException, e:
            log.error(self.account_id + " 视频%s解析失败，原因：%s" % (video_info["video_id"], e.message))
            raise

        self.main_thread_check()  # 检测主线程运行状态
        log.step(self.account_id + " 开始下载视频%s 《%s》 %s" % (video_info["video_id"], video_info["video_title"], video_response["video_url"]))

        video_file_path = os.path.join(self.main_thread.video_download_path, self.account_id, "%s - %s.mp4" % (video_info["video_id"], path.filter_text(video_info["video_title"])))
        save_file_return = net.save_net_file(video_response["video_url"], video_file_path)
        if save_file_return["status"] == 1:
            # 设置临时目录
            log.step(self.account_id + " 视频%s 《%s》下载成功" % (video_info["video_id"], video_info["video_title"]))
        else:
            log.error(self.account_id + " 视频%s 《%s》 %s 下载失败，原因：%s" % (video_info["video_id"], video_info["video_title"], video_response["video_url"], crawler.download_failre(save_file_return["code"])))

        # 媒体内图片和视频全部下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = str(video_info["video_time"])  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载视频
            video_info_list = self.get_crawl_list()
            log.step(self.account_id + " 需要下载的全部视频解析完毕，共%s个" % len(video_info_list))

            # 从最早的视频开始下载
            while len(video_info_list) > 0:
                video_info = video_info_list.pop()
                log.step(self.account_id + " 开始解析视频%s" % video_info["video_id"])
                self.crawl_video(video_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_id + " 提前退出")
            else:
                log.error(self.account_id + " 异常退出")
        except Exception, e:
            log.error(self.account_id + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_id + " 下载完毕，总共获得%s个视频" % self.total_video_count)
        self.notify_main_thread()


if __name__ == "__main__":
    DailyMotion().main()
