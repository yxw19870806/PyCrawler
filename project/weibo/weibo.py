# -*- coding:UTF-8  -*-
"""
微博图片爬虫
http://www.weibo.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from project.meipai import meipai
import weiboCommon
import os
import re
import threading
import time
import traceback
import urllib2

IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
INIT_SINCE_ID = "9999999999999999"
COOKIE_INFO = {"SUB": ""}


# 获取一页的图片信息
def get_one_page_photo(account_id, page_count):
    photo_pagination_url = "http://photo.weibo.com/photos/get_all"
    query_data = {
        "uid": account_id,
        "count": IMAGE_COUNT_PER_PAGE,
        "page": page_count,
        "type": "3",
    }
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    result = {
        "image_info_list": [],  # 全部图片信息
        "is_over": False,  # 是不是最后一页图片
    }
    photo_pagination_response = net.http_request(photo_pagination_url, method="GET", fields=query_data, cookies_list=cookies_list, json_decode=True)
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_JSON_DECODE_ERROR and photo_pagination_response.data.find('<p class="txt M_txtb">用户不存在或者获取用户信息失败</p>') >= 0:
        raise crawler.CrawlerException("账号不存在")
    elif photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(photo_pagination_response.status))
    if not crawler.check_sub_key(("data",), photo_pagination_response.json_data):
        raise crawler.CrawlerException("返回数据'data'字段不存在\n%s" % photo_pagination_response.json_data)
    if not crawler.check_sub_key(("total", "photo_list"), photo_pagination_response.json_data["data"]):
        raise crawler.CrawlerException("返回数据'data'字段格式不正确\n%s" % photo_pagination_response.json_data)
    if not crawler.is_integer(photo_pagination_response.json_data["data"]["total"]):
        raise crawler.CrawlerException("返回数据'total'字段类型不正确\n%s" % photo_pagination_response.json_data)
    if not isinstance(photo_pagination_response.json_data["data"]["photo_list"], list):
        raise crawler.CrawlerException("返回数据'photo_list'字段类型不正确\n%s" % photo_pagination_response.json_data)
    for image_info in photo_pagination_response.json_data["data"]["photo_list"]:
        result_image_info = {
            "image_time": None,  # 图片上传时间
            "image_url": None,  # 图片地址
        }
        # 获取图片上传时间
        if not crawler.check_sub_key(("timestamp",), image_info):
            raise crawler.CrawlerException("图片信息'timestamp'字段不存在\n%s" % image_info)
        if not crawler.check_sub_key(("timestamp",), image_info):
            raise crawler.CrawlerException("图片信息'timestamp'字段类型不正确\n%s" % image_info)
        result_image_info["image_time"] = int(image_info["timestamp"])
        # 获取图片地址
        if not crawler.check_sub_key(("pic_host", "pic_name"), image_info):
            raise crawler.CrawlerException("图片信息'pic_host'或者'pic_name'字段不存在\n%s" % image_info)
        result_image_info["image_url"] = str(image_info["pic_host"]) + "/large/" + str(image_info["pic_name"])
        result["image_info_list"].append(result_image_info)
    # 检测是不是还有下一页 总的图片数量 / 每页显示的图片数量 = 总的页数
    result["is_over"] = page_count >= (photo_pagination_response.json_data["data"]["total"] * 1.0 / IMAGE_COUNT_PER_PAGE)
    return result


# 获取一页的视频信息
# page_id -> 1005052535836307
def get_one_page_video(account_page_id, since_id):
    # http://weibo.com/p/aj/album/loading?type=video&since_id=9999999999999999&page_id=1005052535836307&page=1&ajax_call=1
    video_pagination_url = "http://weibo.com/p/aj/album/loading"
    query_data = {
        "type": "video",
        "since_id": since_id,
        "page_id": account_page_id,
        "ajax_call": "1",
        "__rnd": int(time.time() * 1000),
    }
    cookies_list = {"SUB": COOKIE_INFO["SUB"]}
    result = {
        "is_error": False,  # 是不是格式不符合
        "next_page_since_id": None,  # 下一页视频指针
        "video_play_url_list": [],  # 全部视频地址
    }
    video_pagination_response = net.http_request(video_pagination_url, method="GET", fields=query_data, cookies_list=cookies_list, json_decode=True)
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(video_pagination_response.status))
    if not crawler.check_sub_key(("code", "data"), video_pagination_response.json_data):
        raise crawler.CrawlerException("返回信息'code'或'data'字段不存在\n%s" % video_pagination_response.json_data)
    if not crawler.is_integer(video_pagination_response.json_data["code"]):
        raise crawler.CrawlerException("返回信息'code'字段类型不正确\n%s" % video_pagination_response.json_data)
    if int(video_pagination_response.json_data["code"]) != 100000:
        raise crawler.CrawlerException("返回信息'code'字段取值不正确\n%s" % video_pagination_response.json_data)
    page_html = video_pagination_response.json_data["data"].encode("UTF-8")
    # 获取视频播放地址
    video_play_url_list = re.findall('<a target="_blank" href="([^"]*)"><div ', page_html)
    if len(video_play_url_list) == 0:
        if since_id != INIT_SINCE_ID or page_html.find("还没有发布过视频") == -1:
            raise crawler.CrawlerException("返回信息匹配视频地址失败\n%s" % video_pagination_response.json_data)
    else:
        result["video_play_url_list"] = map(str, video_play_url_list)
    # 获取下一页视频的指针
    next_page_since_id = tool.find_sub_string(page_html, "type=video&owner_uid=&viewer_uid=&since_id=", '">')
    if next_page_since_id:
        if not crawler.is_integer(next_page_since_id):
            raise crawler.CrawlerException("返回信息截取下一页指针失败\n%s" % video_pagination_response.json_data)
        result["next_page_since_id"] = next_page_since_id
    return result


# 从视频播放页面中提取下载地址
def get_video_url(video_play_url):
    video_url = None
    # http://miaopai.com/show/Gmd7rwiNrc84z5h6S9DhjQ__.htm
    if video_play_url.find("miaopai.com/show/") >= 0:  # 秒拍
        video_id = tool.find_sub_string(video_play_url, "miaopai.com/show/", ".")
        video_info_url = "http://gslb.miaopai.com/stream/%s.json" % video_id
        query_data = {"token": ""}
        video_info_response = net.http_request(video_info_url, method="GET", fields=query_data, json_decode=True)
        if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException(crawler.request_failre(video_info_response.status))
        if not crawler.check_sub_key(("status", "result"), video_info_response.json_data):
            raise crawler.CrawlerException("返回信息'status'或'result'字段不存在\n%s" % video_info_response.json_data)
        if not crawler.is_integer(video_info_response.json_data["status"]):
            raise crawler.CrawlerException("返回信息'status'字段类型不正确\n%s" % video_info_response.json_data)
        if int(video_info_response.json_data["status"]) != 200:
            raise crawler.CrawlerException("返回信息'status'字段取值不正确\n%s" % video_info_response.json_data)
        if len(video_info_response.json_data["result"]) == 0:
            raise crawler.CrawlerException("返回信息'result'字段长度不正确\n%s" % video_info_response.json_data)
        for video_info in video_info_response.json_data["result"]:
            if crawler.check_sub_key(("path", "host", "scheme"), video_info):
                video_url = str(video_info["scheme"] + video_info["host"] + video_info["path"])
                break
        if video_url is None:
            raise crawler.CrawlerException("返回信息匹配视频地址失败\n%s" % video_info_response.json_data)
    # http://video.weibo.com/show?fid=1034:e608e50d5fa95410748da61a7dfa2bff
    elif video_play_url.find("video.weibo.com/show?fid=") >= 0:  # 微博视频
        cookies_list = {"SUB": COOKIE_INFO["SUB"]}
        video_play_response = net.http_request(video_play_url, method="GET", cookies_list=cookies_list)
        if video_play_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            video_url = tool.find_sub_string(video_play_response.data, "video_src=", "&")
            if not video_url:
                video_url = tool.find_sub_string(video_play_response.data, 'flashvars="list=', '"')
            if not video_url:
                raise crawler.CrawlerException("页面截取视频地址失败\n%s" % video_play_response.data)
            video_url = str(urllib2.unquote(video_url))
            if video_url.find("//") == 0:
                video_url = "http:" + video_url
        elif video_play_response.status == 404:
            video_url = ""
        else:
            raise crawler.CrawlerException(crawler.request_failre(video_play_response.status))
    # http://www.meipai.com/media/98089758
    elif video_play_url.find("www.meipai.com/media") >= 0:  # 美拍
        video_play_response = net.http_request(video_play_url, method="GET")
        if video_play_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise crawler.CrawlerException(crawler.request_failre(video_play_response.status))
        if video_play_response.data.find('<p class="error-p">为建设清朗网络空间，视频正在审核中，暂时无法播放。</p>') > 0:
            video_url = ""
        else:
            video_url_find = re.findall('<meta content="([^"]*)" property="og:video:url">', video_play_response.data)
            if len(video_url_find) != 1:
                raise crawler.CrawlerException("页面匹配加密视频信息失败\n%s" % video_play_response.data)
            video_url = meipai.decrypt_video_url(video_url_find[0])
            if video_url is None:
                raise crawler.CrawlerException("加密视频地址解密失败\n%s" % video_url_find[0])
    # http://v.xiaokaxiu.com/v/0YyG7I4092d~GayCAhwdJQ__.html
    elif video_play_url.find("v.xiaokaxiu.com/v/") >= 0:  # 小咖秀
        video_id = video_play_url.split("/")[-1].split(".")[0]
        video_url = "http://gslb.miaopai.com/stream/%s.mp4" % video_id
    else:  # 其他视频，暂时不支持，收集看看有没有
        raise crawler.CrawlerException("未知的第三方视频\n%s" % video_play_url)
    return video_url


class Weibo(crawler.Crawler):
    def __init__(self, extra_config=None):
        global COOKIE_INFO

        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_GET_COOKIE: {
                ".sina.com.cn": (),
                ".login.sina.com.cn": (),
            },
        }
        crawler.Crawler.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO.update(self.cookie_value)

        # 解析存档文件
        # account_id  image_count  last_image_time  video_count  last_video_url  (account_name)
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", ""])

        # 检测登录状态
        if not weiboCommon.check_login(COOKIE_INFO):
            # 如果没有获得登录相关的cookie，则模拟登录并更新cookie
            new_cookies_list = weiboCommon.generate_login_cookie(COOKIE_INFO)
            if new_cookies_list:
                COOKIE_INFO.update(new_cookies_list)
            # 再次检测登录状态
            if not weiboCommon.check_login(COOKIE_INFO):
                log.error("没有检测到登录信息")
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), self.total_image_count))


class Download(crawler.DownloadThread):
    def __init__(self, account_info, main_thread):
        crawler.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 6 and self.account_info[5]:
            self.account_name = self.account_info[5]
        else:
            self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载图片
    def get_crawl_image_list(self):
        page_count = 1
        unique_list = []
        image_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的图片
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页图片" % page_count)

            # 获取指定一页图片的信息
            try:
                photo_pagination_response = get_one_page_photo(self.account_id, page_count)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 第%s页图片解析失败，原因：%s" % (page_count, e.message))
                raise

            log.trace(self.account_name + "第%s页解析的全部图片信息：%s" % (page_count, photo_pagination_response["image_info_list"]))

            # 寻找这一页符合条件的图片
            for image_info in photo_pagination_response["image_info_list"]:
                # 检查是否达到存档记录
                if image_info["image_time"] > int(self.account_info[2]):
                    # 新增图片导致的重复判断
                    if image_info["image_url"] in unique_list:
                        continue
                    else:
                        image_info_list.append(image_info)
                        unique_list.append(image_info["image_url"])
                else:
                    is_over = True
                    break

            if not is_over:
                if photo_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1

        return image_info_list

    # 获取所有可下载视频
    def get_crawl_video_list(self):
        # 获取账号首页
        try:
            account_index_response = weiboCommon.get_account_index_page(self.account_id)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 首页解析失败，原因：%s" % e.message)
            raise

        video_play_url_list = []
        since_id = INIT_SINCE_ID
        is_over = False
        # 获取全部还未下载过需要解析的视频
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析%s后一页视频" % since_id)

            # 获取指定时间点后的一页视频信息
            try:
                video_pagination_response = get_one_page_video(account_index_response["account_page_id"], since_id)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " %s后的一页视频解析失败，原因：%s" % (since_id, e.message))
                raise

            log.trace(self.account_name + "since_id：%s解析的全部视频：%s" % (since_id, video_pagination_response["video_play_url_list"]))

            # 寻找这一页符合条件的视频
            for video_play_url in video_pagination_response["video_play_url_list"]:
                # 检查是否达到存档记录
                if self.account_info[4] != video_play_url:
                    video_play_url_list.append(video_play_url)
                else:
                    is_over = True
                    break

            if not is_over:
                if video_pagination_response["next_page_since_id"] is None:
                    is_over = True
                    # todo 没有找到历史记录如何处理
                    # 有历史记录，但此次直接获取了全部视频
                    if self.account_info[4] != "":
                        log.error(self.account_name + " 没有找到上次下载的最后一个视频地址")
                else:
                    # 设置下一页指针
                    since_id = video_pagination_response["next_page_since_id"]

        return video_play_url_list

    # 下载同一上传时间的所有图片
    def crawl_image(self, image_info_list):
        # 同一上传时间的所有图片
        image_index = int(self.account_info[1]) + 1
        for image_info in image_info_list:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始下载第%s张图片 %s" % (image_index, image_info["image_url"]))

            file_type = image_info["image_url"].split(".")[-1]
            if file_type.find("/") != -1:
                file_type = "jpg"
            image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_info["image_url"], image_file_path)
            if save_file_return["status"] == 1:
                if weiboCommon.check_image_invalid(image_file_path):
                    path.delete_dir_or_file(image_file_path)
                    log.error(self.account_name + " 第%s张图片 %s 资源已被删除，跳过" % (image_index, image_info["image_url"]))
                    continue
                else:
                    # 设置临时目录
                    self.temp_path_list.append(image_file_path)
                    log.step(self.account_name + " 第%s张图片下载成功" % image_index)
                    image_index += 1
            else:
                log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_info["image_url"], crawler.download_failre(save_file_return["code"])))
                continue

        # 图片下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1) - int(self.account_info[1])  # 计数累加
        self.account_info[1] = str(image_index - 1)  # 设置存档记录
        self.account_info[2] = str(image_info_list[0]["image_time"])  # 设置存档记录

    # 解析单个视频
    def crawl_video(self, video_play_url):
        video_index = int(self.account_info[3]) + 1
        # 获取这个视频的下载地址
        try:
            video_url = get_video_url(video_play_url)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 第%s个视频 %s 解析失败，原因：%s" % (video_index, video_play_url, e.message))
            raise

        if video_url is "":
            log.step(self.account_name + " 第%s个视频 %s 跳过" % (video_index, video_play_url))
            return

        self.main_thread_check()  # 检测主线程运行状态
        log.step(self.account_name + " 开始下载第%s个视频 %s" % (video_index, video_url))

        video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%04d.mp4" % video_index)
        save_file_return = net.save_net_file(video_url, video_file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 第%s个视频下载成功" % video_index)
        else:
            log.error(self.account_name + " 第%s个视频 %s（%s) 下载失败，原因：%s" % (video_index, video_play_url, video_url, crawler.download_failre(save_file_return["code"])))
            return

        # 视频下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[3] = str(video_index)  # 设置存档记录
        self.account_info[4] = video_play_url  # 设置存档记录

    def run(self):
        try:
            # 图片下载
            if self.main_thread.is_download_image:
                # 获取所有可下载图片
                image_info_list = self.get_crawl_image_list()
                log.step(self.account_name + " 需要下载的全部图片解析完毕，共%s张" % len(image_info_list))

                # 从最早的图片开始下载
                deal_image_info_list = []
                while len(image_info_list) > 0:
                    image_info = image_info_list.pop()
                    # 下一张图片的上传时间一致，合并下载
                    deal_image_info_list.append(image_info)
                    if len(image_info_list) > 0 and image_info_list[-1]["image_time"] == image_info["image_time"]:
                        continue

                    # 下载同一上传时间的所有图片
                    self.crawl_image(deal_image_info_list)
                    deal_image_info_list = []  # 累加图片地址清除
                    self.main_thread_check()  # 检测主线程运行状态

            # 视频下载
            if self.main_thread.is_download_video:
                # 获取所有可下载视频
                video_play_url_list = self.get_crawl_video_list()
                log.step(self.account_name + " 需要下载的全部视频片解析完毕，共%s个" % len(video_play_url_list))

                # 从最早的图片开始下载
                while len(video_play_url_list) > 0:
                    video_play_url = video_play_url_list.pop()
                    log.step(self.account_name + " 开始解析第%s个视频 %s" % (int(self.account_info[1]) + 1, video_play_url))
                    self.crawl_video(video_play_url)
                    self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示同一时间的图片正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Weibo().main()
