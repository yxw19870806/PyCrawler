# -*- coding:UTF-8  -*-
"""
一直播图片&视频爬虫
http://www.yizhibo.com/
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


# 获取全部图片地址列表
def get_image_index_page(account_id):
    # http://www.yizhibo.com/member/personel/user_photos?memberid=6066534
    image_index_url = "http://www.yizhibo.com/member/personel/user_photos"
    query_data = {"memberid": account_id}
    image_index_response = net.http_request(image_index_url, method="GET", fields=query_data)
    result = {
        "image_url_list": [],  # 全部图片地址
    }
    if image_index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.get_http_request_failed_reason(image_index_response.status))
    if image_index_response.data == '<script>window.location.href="/404.html";</script>':
        raise crawler.CrawlerException("账号不存在")
    # 获取全部图片地址
    if image_index_response.data.find("还没有照片哦") == -1:
        image_url_list = re.findall('<img src="([^"]*)@[^"]*" alt="" class="index_img_main">', image_index_response.data)
        if len(image_url_list) == 0:
            raise crawler.CrawlerException("页面匹配图片地址失败\n%s" % image_index_response.data)
        result["image_url_list"] = map(str, image_url_list)
    return result


#  获取图片的header
def get_image_header(image_url):
    image_head_response = net.http_request(image_url, method="HEAD")
    result = {
        "image_time": None, # 图片上传时间
    }
    if image_head_response.status == 404:
        return result
    elif image_head_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.get_http_request_failed_reason(image_head_response.status))
    last_modified = image_head_response.headers.get("Last-Modified")
    if last_modified is None:
        raise crawler.CrawlerException("图片header'Last-Modified'字段不存在\n%s" % image_head_response.headers)
    try:
        last_modified_time = time.strptime(last_modified, "%a, %d %b %Y %H:%M:%S %Z")
    except ValueError:
        raise crawler.CrawlerException("图片上传时间文本格式不正确\n%s" % last_modified)
    result["image_time"] = int(time.mktime(last_modified_time)) - time.timezone
    return result


# 获取全部视频ID列表
def get_video_index_page(account_id):
    # http://www.yizhibo.com/member/personel/user_videos?memberid=6066534
    video_pagination_url = "http://www.yizhibo.com/member/personel/user_videos"
    query_data = {"memberid": account_id}
    video_pagination_response = net.http_request(video_pagination_url, method="GET", fields=query_data)
    result = {
        "is_exist": True,  # 是不是存在视频
        "video_id_list": [],  # 全部视频id
    }
    if video_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.get_http_request_failed_reason(video_pagination_response.status))
    if video_pagination_response.data == '<script>window.location.href="/404.html";</script>':
        raise crawler.CrawlerException("账号不存在")
    if video_pagination_response.data.find("还没有直播哦") == -1:
        video_id_list = re.findall('<div class="scid" style="display:none;">([^<]*?)</div>', video_pagination_response.data)
        if len(video_id_list) == 0:
            raise crawler.CrawlerException("页面匹配视频id失败\n%s" % video_pagination_response.data)
        result["video_id_list"] = map(str, video_id_list)
    return result


# 根据video id获取指定视频的详细信息（上传时间、视频列表的下载地址等）
# video_id -> qxonW5XeZru03nUB
def get_video_info_page(video_id):
    # http://api.xiaoka.tv/live/web/get_play_live?scid=xX9-TLVx0xTiSZ69
    video_info_url = "http://api.xiaoka.tv/live/web/get_play_live"
    query_data = {"scid": video_id}
    video_info_response = net.http_request(video_info_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "video_time": False,  # 视频上传时间
        "video_url_list": [],  # 全部视频分集地址
    }
    if video_info_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.get_http_request_failed_reason(video_info_response.status))
    if not crawler.check_sub_key(("result", "data"), video_info_response.json_data):
        raise crawler.CrawlerException("返回信息'result'或'data'字段不存在\n%s" % video_info_response.json_data)
    if not crawler.is_integer(video_info_response.json_data["result"]):
        raise crawler.CrawlerException("返回信息'result'字段类型不正确\n%s" % video_info_response.json_data)
    if int(video_info_response.json_data["result"]) != 1:
        raise crawler.CrawlerException("返回信息'result'字段取值不正确\n%s" % video_info_response.json_data)
    # 获取视频上传时间
    if not crawler.check_sub_key(("createtime",), video_info_response.json_data["data"]):
        raise crawler.CrawlerException("返回信息'createtime'字段不存在\n%s" % video_info_response.json_data)
    if not crawler.is_integer(video_info_response.json_data["data"]["createtime"]):
        raise crawler.CrawlerException("返回信息'createtime'字段类型不正确\n%s" % video_info_response.json_data)
    result["video_time"] = int(video_info_response.json_data["data"]["createtime"])
    # 获取视频地址所在文件地址
    if not crawler.check_sub_key(("linkurl",), video_info_response.json_data["data"]):
        raise crawler.CrawlerException("返回信息'linkurl'字段不存在\n%s" % video_info_response.json_data)
    video_file_url = str(video_info_response.json_data["data"]["linkurl"])
    video_file_response = net.http_request(video_file_url, method="GET")
    if video_file_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        ts_id_list = re.findall("([\S]*.ts)", video_file_response.data)
        if len(ts_id_list) == 0:
            raise crawler.CrawlerException("分集文件匹配视频地址失败\n%s" % video_info_response.json_data)
        # http://alcdn.hls.xiaoka.tv/20161122/6b6/c5f/xX9-TLVx0xTiSZ69/
        prefix_url = video_file_url[:video_file_url.rfind("/") + 1]
        for ts_id in ts_id_list:
            result["video_url_list"].append(prefix_url + str(ts_id))
    else:
        raise crawler.CrawlerException(crawler.get_http_request_failed_reason(video_info_response.status))
    return result


class YiZhiBo(crawler.Crawler):
    def __init__(self):
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_DOWNLOAD_VIDEO: True,
        }
        crawler.Crawler.__init__(self, sys_config)

        # 解析存档文件
        # account_id  video_count  last_video_time  image_count  last_image_time(account_name)
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0", "0", "0", "0"])

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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), self.total_image_count, self.total_video_count))


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
        # 获取全部图片地址列表
        try:
            image_index_response = get_image_index_page(self.account_id)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 图片首页解析失败，原因：%s" % e.message)
            return []

        # 寻找这一页符合条件的图片
        image_info_list = []
        for image_url in image_index_response["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析图片%s" % image_url)

            try:
                image_head_response = get_image_header(image_url)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 图片%s解析失败，原因：%s" % (image_url, e.message))
                return []

            # 检查是否达到存档记录
            if image_head_response["image_time"] > int(self.account_info[4]):
                image_info_list.append({"image_url": image_url, "image_time": image_head_response["image_time"]})
            else:
                break

        return image_info_list

    # 解析单张图片
    def crawl_image(self, image_info):
        image_index = int(self.account_info[3]) + 1
        file_type = image_info["image_url"].split(".")[-1].split(":")[0]
        image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
        save_file_return = net.save_net_file(image_info["image_url"], image_file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 第%s张图片下载成功" % image_index)
        else:
            log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_info["image_url"], crawler.get_save_net_file_failed_reason(save_file_return["code"])))
            return

        # 图片下载完毕
        self.total_image_count += 1  # 计数累加
        self.account_info[3] = str(image_index)  # 设置存档记录
        self.account_info[4] = str(image_info["image_time"])  # 设置存档记录

    # 获取所有可下载视频
    def get_crawl_video_list(self):
        video_info_list = []
        # 获取全部视频ID列表
        try:
            video_pagination_response = get_video_index_page(self.account_id)
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 视频首页解析失败，原因：%s" % e.message)
            return []

        # 寻找这一页符合条件的视频
        for video_id in video_pagination_response["video_id_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析视频%s" % video_id)

            # 获取视频的时间和下载地址
            try:
                video_info_response = get_video_info_page(video_id)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 视频%s解析失败，原因：%s" % (video_id, e.message))
                return []

            # 检查是否达到存档记录
            if video_info_response["video_time"] > int(self.account_info[2]):
                video_info_list.append(video_info_response)
            else:
                break

        return video_info_list

    # 解析单个视频
    def crawl_video(self, video_info):
        video_index = int(self.account_info[1]) + 1
        video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%04d.ts" % video_index)
        save_file_return = net.save_net_file_list(video_info["video_url_list"], video_file_path)
        if save_file_return["status"] == 1:
            log.step(self.account_name + " 第%s个视频下载成功" % video_index)
        else:
            log.error(self.account_name + " 第%s个视频 %s 下载失败" % (video_index, video_info["video_url_list"]))
            return

        # 视频下载完毕
        self.total_video_count += 1  # 计数累加
        self.account_info[1] = str(video_index)  # 设置存档记录
        self.account_info[2] = str(video_info["video_time"])  # 设置存档记录

    def run(self):
        try:
            # 图片下载
            if self.main_thread.is_download_image:
                # 获取所有可下载图片
                image_info_list = self.get_crawl_image_list()
                log.step("需要下载的全部图片解析完毕，共%s张" % len(image_info_list))

                # 从最早的图片开始下载
                while len(image_info_list) > 0:
                    image_info = image_info_list.pop()
                    log.step(self.account_name + " 开始下载第%s张图片 %s" % (int(self.account_info[3]) + 1, image_info["image_url"]))
                    self.crawl_image(image_info)
                    self.main_thread_check()  # 检测主线程运行状态

            # 视频下载
            if self.main_thread.is_download_video:
                # 获取所有可下载视频
                video_info_list = self.get_crawl_video_list()
                log.step(self.account_name + " 需要下载的全部视频解析完毕，共%s个" % len(video_info_list))

                # 从最早的视频开始下载
                while len(video_info_list) > 0:
                    video_info = video_info_list.pop()
                    log.step(self.account_name + " 开始下载第%s个视频 %s" % (int(self.account_info[1]) + 1, video_info["video_url_list"]))
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
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (self.total_image_count, self.total_video_count))
        self.notify_main_thread()


if __name__ == "__main__":
    YiZhiBo().main()
