# -*- coding:UTF-8  -*-
"""
PR社APP图片&视频爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import threading
import time
import traceback

POST_COUNT_PER_PAGE = 10  # 每次获取的作品数量（貌似无效）
IS_SKIP_BLUR = False
IS_STEP_INVALID_RESOURCE = False


# 获取指定时间后的一页作品
def get_one_page_post(account_id, timestamp):
    post_pagination_url = "https://api.prpr.tinydust.cn/v3/posts/old"
    query_data = {
        "timestamp": timestamp,
        "userId": account_id,
        "limit": POST_COUNT_PER_PAGE,
    }
    index_response = net.http_request(post_pagination_url, method="GET", fields=query_data, json_decode=True)
    result = {
        "post_info_list": [],  # 全部作品信息
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(index_response.status))
    if not crawler.check_sub_key(("code",), index_response.json_data):
        raise crawler.CrawlerException("返回信息'code'字段不存在\n%s" % index_response.json_data)
    if not crawler.is_integer(index_response.json_data["code"]):
        raise crawler.CrawlerException("返回信息'code'字段类型不正确\n%s" % index_response.json_data)
    if int(index_response.json_data["code"]) != 200:
        raise crawler.CrawlerException("返回信息'code'字段取值不正确\n%s" % index_response.json_data)
    if not crawler.check_sub_key(("result",), index_response.json_data):
        raise crawler.CrawlerException("返回信息'result'字段不存在\n%s" % index_response.json_data)
    for post_info in index_response.json_data["result"]:
        result_post_info = {
            "post_id": None,  # 作品id
            "post_time": None,  # 作品时间
        }
        if not crawler.check_sub_key(("_id",), post_info):
            raise crawler.CrawlerException("作品信息'_id'字段不存在\n%s" % post_info)
        result_post_info["post_id"] = str(post_info["_id"])
        if not crawler.check_sub_key(("createdAt",), post_info):
            raise crawler.CrawlerException("作品信息'createdAt'字段不存在\n%s" % post_info)
        if not crawler.is_integer(post_info["createdAt"]):
            raise crawler.CrawlerException("作品信息'createdAt'字段类型不正确\n%s" % post_info)
        result_post_info["post_time"] = int(post_info["createdAt"])
        result["post_info_list"].append(result_post_info)
    return result


# 获取指定作品
def get_post_page(post_id):
    index_url = "https://api.prpr.tinydust.cn/v3/posts/%s" % post_id
    index_response = net.http_request(index_url, method="GET", json_decode=True)
    result = {
        "image_url_list": [],  # 全部图片地址
        "video_url_list": [],  # 全部视频地址
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(index_response.status))
    if not crawler.check_sub_key(("code",), index_response.json_data):
        raise crawler.CrawlerException("返回信息'code'字段不存在\n%s" % index_response.json_data)
    if not crawler.is_integer(index_response.json_data["code"]):
        raise crawler.CrawlerException("返回信息'code'字段类型不正确\n%s" % index_response.json_data)
    if int(index_response.json_data["code"]) != 200:
        raise crawler.CrawlerException("返回信息'code'字段取值不正确\n%s" % index_response.json_data)
    if not crawler.check_sub_key(("result",), index_response.json_data):
        raise crawler.CrawlerException("返回信息'result'字段不存在\n%s" % index_response.json_data)
    if not crawler.check_sub_key(("pictures", "imageCount", "videoCount"), index_response.json_data["result"]):
        raise crawler.CrawlerException("返回信息'pictures'、'imageCount'或'videoCount'字段不存在\n%s" % index_response.json_data)
    for media_info in index_response.json_data["result"]["pictures"]:
        if not crawler.check_sub_key(("url",), media_info):
            raise crawler.CrawlerException("返回信息'url'字段不存在\n%s" % media_info)
        if not crawler.check_sub_key(("type",), media_info):
            raise crawler.CrawlerException("返回信息'type'字段不存在\n%s" % media_info)
        if not crawler.is_integer(media_info["type"]):
            raise crawler.CrawlerException("返回信息'type'字段类型不正确\n%s" % media_info)
        media_type = int(media_info["type"])
        if media_type == 0:
            result["image_url_list"].append(str(media_info["url"]))
        elif media_type == 1:
            if media_info["url"][0] != "?":
                result["video_url_list"].append(str(media_info["url"]))
            else:
                if not crawler.check_sub_key(("thum",), media_info):
                    raise crawler.CrawlerException("返回信息'thum'字段不存在\n%s" % media_info)
                result["image_url_list"].append(str(media_info["thum"]))
        else:
            raise crawler.CrawlerException("返回信息'type'字段取值不正确\n%s" % media_info)
    return result


# 检测下载得文件是否有效
def check_invalid(file_path):
    if file_path.split(".")[-1] == "png" and os.path.getsize(file_path) < 102400:
        if tool.get_file_md5(file_path) in ["0764beb3d521b9b420d365f6ee6d453b", "0d527d84f1150d002998cb67ec271de5", "11f81047704ca9a522f54ced9ef82a85",
                                            "1ba2863db2ac7296d73818be890ef378", "23e0a284d4fa44c222bf41d3cb58b241", "2423c99718385d789cec3e6c1c1020db",
                                            "483ec66794f1dfa02d634c4745fd4ded", "6a9e28c562a9187ad262f027b0ed9cf2", "76d8988358e84e123a126d736be4bc44",
                                            "7a9abea08bc47d3a64f87eebdd533dcd", "7c6b17080d95d2e7847f6c00b1228182", "c0de7824049435be9209b8f39fbcb1ba",
                                            "cbccd65c36ff32fe877bf56b7e70a8ba", "dd77da050fc0bcf79d22d35deb1019bd", "f932db2213fee316359b1267f972899e",
                                            ]:
            return True
    return False


class PrPr(crawler.Crawler):
    def __init__(self):
        global IS_SKIP_BLUR, IS_STEP_INVALID_RESOURCE

        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_APP_CONFIG: (
                os.path.realpath("config.ini"),
                ("IS_STEP_INVALID_RESOURCE", False, crawler.CONFIG_ANALYSIS_MODE_BOOLEAN),
                ("IS_SKIP_BLUR", False, crawler.CONFIG_ANALYSIS_MODE_BOOLEAN),
            ),
        }
        crawler.Crawler.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IS_SKIP_BLUR = self.app_config["IS_SKIP_BLUR"]
        IS_STEP_INVALID_RESOURCE = self.app_config["IS_STEP_INVALID_RESOURCE"]

        # 解析存档文件
        # account_id last_post_time
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "0"])

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
        if len(self.account_info) > 2 and self.account_info[2]:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_id
        log.step(self.account_name + " 开始")

    # 获取所有可下载作品
    def get_crawl_list(self):
        page_count = 1
        post_id_list = []
        is_over = False
        timestamp = int(time.time() * 1000)
        # 获取全部还未下载过需要解析的作品
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析%s后一页的作品" % timestamp)

            # 获取一页作品
            try:
                post_pagination_response = get_one_page_post(self.account_id, timestamp)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 首页解析失败，原因：%s" % e.message)
                raise

            log.trace(self.account_name + " 第%s页解析的全部作品：%s" % (page_count, post_pagination_response["post_info_list"]))

            # 寻找这一页符合条件的媒体
            for post_info in post_pagination_response["post_info_list"]:
                # 检查是否达到存档记录
                if post_info["post_time"] > int(self.account_info[1]):
                    post_id_list.append(post_info)
                    # 设置下一页指针
                    timestamp = post_info["post_time"]
                else:
                    is_over = True
                    break

            if not is_over:
                if len(post_pagination_response["post_info_list"]) < POST_COUNT_PER_PAGE:
                    is_over = True

        return post_id_list

    # 解析单个作品
    def crawl_post(self, post_info):
        # 获取指定作品
        try:
            blog_response = get_post_page(post_info["post_id"])
        except crawler.CrawlerException, e:
            log.error(self.account_name + " 作品%s解析失败，原因：%s" % (post_info["post_id"], e.message))
            raise

        # 图片下载
        image_index = 1
        if self.main_thread.is_download_image:
            for image_url in blog_response["image_url_list"]:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(self.account_name + " 作品%s 开始下载第%s张图片 %s" % (post_info["post_id"], image_index, image_url))

                origin_image_url, file_param = image_url.split("?", 1)
                file_name_and_type = origin_image_url.split("/")[-1]
                if file_param.find("/blur/") >= 0:
                    # 跳过
                    if IS_SKIP_BLUR:
                        log.step(self.account_name + " 作品%s 第%s张图片 %s 跳过" % (post_info["post_id"], image_index, image_url))
                        continue
                    image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "blur", file_name_and_type)
                else:
                    image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, file_name_and_type)
                save_file_return = net.save_net_file(image_url, image_file_path, need_content_type=True)
                if save_file_return["status"] == 1:
                    if check_invalid(save_file_return["file_path"]):
                        path.delete_dir_or_file(save_file_return["file_path"])
                        error_message = self.account_name + " 作品%s 第%s张图片 %s 无效，已删除" % (post_info["post_id"], image_index, image_url)
                        if IS_STEP_INVALID_RESOURCE:
                            log.step(error_message)
                        else:
                            log.error(error_message)
                    else:
                        # 设置临时目录
                        self.temp_path_list.append(image_file_path)
                        log.step(self.account_name + " 作品%s 第%s张图片 下载成功" % (post_info["post_id"], image_index))
                        image_index += 1
                else:
                    log.error(self.account_name + " 作品%s 第%s张图片 %s 下载失败，原因：%s" % (post_info["post_id"], image_index, image_url, crawler.download_failre(save_file_return["code"])))

        # 视频下载
        video_index = 1
        if self.main_thread.is_download_video:
            for video_url in blog_response["video_url_list"]:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(self.account_name + " 作品%s 开始下载第%s个视频 %s" % (post_info["post_id"], video_index, video_url))

                video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%s_%02d.mp4" % (post_info["post_id"], video_index))
                save_file_return = net.save_net_file(video_url, video_file_path, need_content_type=True)
                if save_file_return["status"] == 1:
                    if check_invalid(save_file_return["file_path"]):
                        path.delete_dir_or_file(save_file_return["file_path"])
                        error_message = self.account_name + " 作品%s 第%s个视频 %s 无效，已删除" % (post_info["post_id"], video_index, video_url)
                        if IS_STEP_INVALID_RESOURCE:
                            log.step(error_message)
                        else:
                            log.error(error_message)
                    else:
                        # 设置临时目录
                        self.temp_path_list.append(video_file_path)
                        log.step(self.account_name + " 作品%s 第%s个视频下载成功" % (post_info["post_id"], video_index))
                        video_index += 1
                else:
                    log.error(self.account_name + " 作品%s 第%s个视频 %s 下载失败，原因：%s" % (post_info["post_id"], video_index, video_url, crawler.download_failre(save_file_return["code"])))

        # 媒体内图片和视频全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1)  # 计数累加
        self.total_video_count += (video_index - 1)  # 计数累加
        self.account_info[1] = str(post_info["post_time"])  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载作品
            post_id_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部作品解析完毕，共%s个" % len(post_id_list))

            while len(post_id_list) > 0:
                post_info = post_id_list.pop()
                log.step(self.account_name + " 开始解析作品%s" % post_info["post_id"])
                self.crawl_post(post_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个作品正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
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
    PrPr().main()
