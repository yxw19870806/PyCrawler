# -*- coding:UTF-8  -*-
"""
Instagram图片&视频爬虫
https://www.instagram.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
import json
import os
import threading
import time
import traceback
from common import *

IS_LOCAL_SAVE_SESSION = False
IMAGE_COUNT_PER_PAGE = 12
QUERY_ID = "17859156310193001"
COOKIE_INFO = {"csrftoken": "", "mid": "", "sessionid": ""}
SESSION_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "session"))


# 生成session cookies
def init_session():
    # 如果有登录信息（初始化时从浏览器中获得）
    if COOKIE_INFO["sessionid"]:
        return True
    home_url = "https://www.instagram.com/"
    home_response = net.http_request(home_url, method="GET")
    if home_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        set_cookie = net.get_cookies_from_response_header(home_response.headers)
        if "csrftoken" in set_cookie and "mid" in set_cookie:
            COOKIE_INFO["csrftoken"] = set_cookie["csrftoken"]
            COOKIE_INFO["mid"] = set_cookie["mid"]
            return True
    return False


# 检测登录状态
def check_login():
    if not COOKIE_INFO["sessionid"]:
        # 从文件中读取账号密码
        account_data = tool.json_decode(tool.decrypt_string(tool.read_file(SESSION_FILE_PATH)), {})
        if crawler.check_sub_key(("email", "password"), account_data):
            if _do_login(account_data["email"], account_data["password"]):
                return True
    else:
        index_url = "https://www.instagram.com/"
        index_response = net.http_request(index_url, method="GET", cookies_list=COOKIE_INFO)
        if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            return index_response.data.find('"viewer":{') >= 0
    return False


# 登录
def login_from_console():
    # 从命令行中输入账号密码
    while True:
        email = output.console_input(crawler.get_time() + " 请输入邮箱: ")
        password = output.console_input(crawler.get_time() + " 请输入密码: ")
        while True:
            input_str = output.console_input(crawler.get_time() + " 是否使用这些信息(Y)es或重新输入(N)o: ")
            input_str = input_str.lower()
            if input_str in ["y", "yes"]:
                if _do_login(email, password):
                    if IS_LOCAL_SAVE_SESSION:
                        account_info_encrypt_string = tool.encrypt_string(json.dumps({"email": email, "password": password}))
                        tool.write_file(account_info_encrypt_string, SESSION_FILE_PATH, tool.WRITE_FILE_TYPE_REPLACE)
                    return True
                return False
            elif input_str in ["n", "no"]:
                break


# 模拟登录请求
def _do_login(email, password):
    login_url = "https://www.instagram.com/accounts/login/ajax/"
    login_post = {"username": email, "password": password, "next": "/"}
    header_list = {"referer": "https://www.instagram.com/", "x-csrftoken": COOKIE_INFO["csrftoken"]}
    login_response = net.http_request(login_url, method="POST", fields=login_post, cookies_list=COOKIE_INFO, header_list=header_list, json_decode=True)
    if login_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if crawler.check_sub_key(("authenticated",), login_response.json_data) and login_response.json_data["authenticated"] is True:
            set_cookie = net.get_cookies_from_response_header(login_response.headers)
            if "sessionid" in set_cookie:
                COOKIE_INFO["sessionid"] = set_cookie["sessionid"]
                return True
    return False


# 根据账号名字获得账号id（字母账号->数字账号)
def get_account_index_page(account_name):
    account_index_url = "https://www.instagram.com/%s" % account_name
    account_index_response = net.http_request(account_index_url, method="GET")
    result = {
        "account_id": None,  # account id
    }
    if account_index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        account_id = tool.find_sub_string(account_index_response.data, '"profilePage_', '"')
        if not crawler.is_integer(account_id):
            raise crawler.CrawlerException("页面截取账号id失败\n%s" % account_index_response.data)
        result["account_id"] = account_id
    elif account_index_response.status == 404:
        raise crawler.CrawlerException("账号不存在")
    else:
        raise crawler.CrawlerException(crawler.request_failre(account_index_response.status))
    return result


# 获取指定页数的全部媒体
# account_id -> 490060609
def get_one_page_media(account_id, cursor):
    api_url = "https://www.instagram.com/graphql/query/"
    query_data = {
        "query_id": QUERY_ID,
        "id": account_id,
        "first": IMAGE_COUNT_PER_PAGE,
    }
    if cursor:
        query_data["after"] = cursor
    media_pagination_response = net.http_request(api_url, method="GET", fields=query_data, cookies_list=COOKIE_INFO, json_decode=True)
    result = {
        "media_info_list": [],  # 全部媒体信息
        "next_page_cursor": None,  # 下一页媒体信息的指针
    }
    if media_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(media_pagination_response.status))
    json_data = media_pagination_response.json_data
    try:
        media_data = media_pagination_response.json_data["data"]["user"]["edge_owner_to_timeline_media"]
    except KeyError:
        raise crawler.CrawlerException("返回数据格式不正确\n%s" % media_pagination_response.json_data)
    if not crawler.check_sub_key(("page_info", "edges", "count"), media_data):
        raise crawler.CrawlerException("返回数据'page_info', 'edges', 'count'字段不存在\n%s" % json_data)
    if not crawler.check_sub_key(("end_cursor", "has_next_page",), media_data["page_info"]):
        raise crawler.CrawlerException("返回数据'end_cursor', 'has_next_page'字段不存在\n%s" % json_data)
    if not isinstance(media_data["edges"], list):
        raise crawler.CrawlerException("返回数据'edges'字段类型不正确\n%s" % json_data)
    if len(media_data["edges"]) == 0:
        if cursor == "":
            if int(media_data["count"]) > 0:
                raise crawler.CrawlerException("私密账号，需要关注才能访问")
            else: # 没有发布任何帖子
                return result
        else:
            raise crawler.CrawlerException("返回数据'edges'字段长度不正确\n%s" % json_data)
    for media_info in media_data["edges"]:
        result_media_info = {
            "image_url": None,  # 图片地址
            "is_group": False,  # 是不是图片/视频组
            "is_video": False,  # 是不是视频
            "page_id": None,  # 媒体详情界面id
            "time": None,  # 媒体上传时间
        }
        if not crawler.check_sub_key(("node",), media_info):
            raise crawler.CrawlerException("媒体信息'node'字段不存在\n%s" % media_info)
        if not crawler.check_sub_key(("display_url", "taken_at_timestamp", "__typename", "shortcode",), media_info["node"]):
            raise crawler.CrawlerException("媒体信息'display_url', 'taken_at_timestamp', '__typename', 'shortcode'字段不存在\n%s" % media_info)
        # GraphImage 单张图片、GraphSidecar 多张图片、GraphVideo 视频
        if media_info["node"]["__typename"] not in ["GraphImage", "GraphSidecar", "GraphVideo"]:
            raise crawler.CrawlerException("媒体信息'__typename'取值范围不正确\n%s" % media_info)
        # 获取图片地址
        result_media_info["image_url"] = str(media_info["node"]["display_url"])
        # 判断是不是图片/视频组
        result_media_info["is_group"] = media_info["node"]["__typename"] == "GraphSidecar"
        # 判断是否有视频
        result_media_info["is_video"] = media_info["node"]["__typename"] == "GraphVideo"
        # 获取图片上传时间
        result_media_info["media_time"] = int(media_info["node"]["taken_at_timestamp"])
        # 获取媒体详情界面id
        result_media_info["page_id"] = str(media_info["node"]["shortcode"])
        result["media_info_list"].append(result_media_info)
    # 获取下一页的指针
    if media_data["page_info"]["has_next_page"]:
        result["next_page_cursor"] = str(media_data["page_info"]["end_cursor"])
    return result


# 获取媒体详细页
def get_media_page(page_id):
    media_url = "https://www.instagram.com/p/%s" % page_id
    media_response = net.http_request(media_url, method="GET", cookies_list=COOKIE_INFO)
    result = {
        "image_url_list": [],  # 全部图片地址
        "video_url_list": [],  # 全部视频地址
    }
    if media_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise crawler.CrawlerException(crawler.request_failre(media_response.status))
    media_info_html = tool.find_sub_string(media_response.data, "window._sharedData = ", ";</script>")
    if not media_info_html:
        crawler.CrawlerException("页面截取媒体信息失败\n%s" % media_response.data)
    media_info_data = tool.json_decode(media_info_html)
    if media_info_data is None:
        raise crawler.CrawlerException("媒体信息加载失败\n%s" % media_info_html)
    try:
        media_data = media_info_data["entry_data"]["PostPage"][0]["graphql"]["shortcode_media"]
    except KeyError:
        raise crawler.CrawlerException("媒体信息格式不正确\n%s" % media_info_data)
    if len(media_info_data["entry_data"]["PostPage"]) != 1:
        raise crawler.CrawlerException("媒体信息'PostPage'字段长度不正确\n%s" % media_info_data)
    if not crawler.check_sub_key(("__typename",), media_data):
        raise crawler.CrawlerException("媒体信息'__typename'字段不存在\n%s" % media_info_data)
    # 多张图片/视频
    if media_data["__typename"] == "GraphSidecar":
        try:
            media_edge_data = media_data["edge_sidecar_to_children"]["edges"]
        except KeyError:
            raise crawler.CrawlerException("图片信息格式不正确\n%s" % media_data)
        if len(media_edge_data) < 2:
            raise crawler.CrawlerException("媒体信息'edges'长度不正确\n%s" % media_data)
        for edge in media_edge_data:
            if not crawler.check_sub_key(("node",), edge):
                raise crawler.CrawlerException("媒体节点'node'字段不存在\n%s" % edge)
            if not crawler.check_sub_key(("__typename", "display_url"), edge["node"]):
                raise crawler.CrawlerException("媒体节点'__typename'或'display_url'字段不存在\n%s" % edge)
            # 获取图片地址
            result["image_url_list"].append(str(edge["node"]["display_url"]))
            # 获取视频地址
            if edge["node"]["__typename"] == "GraphVideo":
                if not crawler.check_sub_key(("video_url",), edge["node"]):
                    raise crawler.CrawlerException("视频节点'video_url'字段不存在\n%s" % edge)
                result["video_url_list"].append(str(edge["node"]["video_url"]))
    # 视频
    elif media_data["__typename"] == "GraphVideo":
        # 获取视频地址
        if not crawler.check_sub_key(("video_url",), media_data):
            raise crawler.CrawlerException("视频信息'video_url'字段不存在\n%s" % media_data)
        result["video_url_list"].append(str(media_data["video_url"]))
    else:
        raise crawler.CrawlerException("媒体信息'__typename'取值范围不正确\n%s" % media_info_data)
    return result


class Instagram(crawler.Crawler):
    def __init__(self, extra_config=None):
        global COOKIE_INFO
        global IS_LOCAL_SAVE_SESSION

        # 设置APP目录
        tool.PROJECT_APP_PATH = os.path.abspath(os.path.dirname(__file__))

        # 初始化参数
        sys_config = {
            crawler.SYS_DOWNLOAD_IMAGE: True,
            crawler.SYS_DOWNLOAD_VIDEO: True,
            crawler.SYS_SET_PROXY: True,
            crawler.SYS_GET_COOKIE: {".instagram.com": ("csrftoken", "sessionid", "mid")},
            crawler.SYS_APP_CONFIG: (
                ("IS_LOCAL_SAVE_SESSION", False, crawler.CONFIG_ANALYSIS_MODE_BOOLEAN),
            ),
        }
        crawler.Crawler.__init__(self, sys_config, extra_config)

        # 设置全局变量，供子线程调用
        COOKIE_INFO.update(self.cookie_value)
        IS_LOCAL_SAVE_SESSION = self.app_config["IS_LOCAL_SAVE_SESSION"]

        # 解析存档文件
        # account_name  account_id  image_count  video_count  last_created_time
        self.account_list = crawler.read_save_data(self.save_data_path, 0, ["", "", "0", "0", "0"])

        # 生成session信息
        init_session()

        # 检测登录状态
        if not check_login():
            while True:
                input_str = output.console_input(crawler.get_time() + " 没有检测到账号登录状态，手动输入账号密码登录继续(C)ontinue？或者退出程序(E)xit？:")
                input_str = input_str.lower()
                if input_str in ["c", "yes"]:
                    if login_from_console():
                        break
                    else:
                        log.step("登录失败！")
                elif input_str in ["e", "exit"]:
                    tool.process_exit()

    def main(self):
        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_name in sorted(self.account_list.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(self.account_list[account_name], self)
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
        self.account_name = self.account_info[0]
        log.step(self.account_name + " 开始")

    # 获取所有可下载媒体
    def get_crawl_list(self):
        cursor = ""
        media_info_list = []
        is_over = False
        # 获取全部还未下载过需要解析的媒体
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析cursor '%s'的媒体信息" % cursor)

            # 获取指定时间后的一页媒体信息
            try:
                media_pagination_response = get_one_page_media(self.account_info[1], cursor)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " cursor '%s'的一页媒体信息解析失败，原因：%s" % (cursor, e.message))
                raise

            log.trace(self.account_name + " cursor '%s'解析的全部媒体：%s" % (cursor, media_pagination_response["media_info_list"]))

            # 寻找这一页符合条件的媒体
            for media_info in media_pagination_response["media_info_list"]:
                # 检查是否达到存档记录
                if media_info["media_time"] > int(self.account_info[4]):
                    media_info_list.append(media_info)
                else:
                    is_over = True
                    break

            if not is_over:
                if media_pagination_response["next_page_cursor"] is None:
                    is_over = True
                else:
                    # 设置下一页指针
                    cursor = media_pagination_response["next_page_cursor"]

        return media_info_list

    # 解析单个媒体
    def crawl_media(self, media_info):
        media_response = None
        # 图片下载
        image_index = int(self.account_info[2]) + 1
        if self.main_thread.is_download_image:
            # 多张图片
            if media_info["is_group"]:
                # 获取媒体详细页
                try:
                    media_response = get_media_page(media_info["page_id"])
                except crawler.CrawlerException, e:
                    log.error(self.account_name + " 媒体%s解析失败，原因：%s" % (media_info["page_id"], e.message))
                    raise
                image_url_list = media_response["image_url_list"]
            # 单张图片 或者 视频的预览图片
            else:
                image_url_list = [media_info["image_url"]]

            for image_url in image_url_list:
                self.main_thread_check()  # 检测主线程运行状态
                # 去除特效，获取原始路径
                log.step(self.account_name + " 开始下载第%s张图片 %s" % (image_index, image_url))

                file_type = image_url.split("?")[0].split(".")[-1]
                image_file_path = os.path.join(self.main_thread.image_download_path, self.account_name, "%04d.%s" % (image_index, file_type))
                save_file_return = net.save_net_file(image_url, image_file_path)
                if save_file_return["status"] == 1:
                    # 设置临时目录
                    self.temp_path_list.append(image_file_path)
                    log.step(self.account_name + " 第%s张图片下载成功" % image_index)
                    image_index += 1
                else:
                    log.error(self.account_name + " 第%s张图片 %s 下载失败，原因：%s" % (image_index, image_url, crawler.download_failre(save_file_return["code"])))

        # 视频下载
        video_index = int(self.account_info[3]) + 1
        if self.main_thread.is_download_video and (media_info["is_group"] or media_info["is_video"]):
            self.main_thread_check()  # 检测主线程运行状态
            # 如果图片那里没有获取过媒体页面，需要重新获取一下
            if media_response is None:
                # 获取媒体详细页
                try:
                    media_response = get_media_page(media_info["page_id"])
                except crawler.CrawlerException, e:
                    log.error(self.account_name + " 媒体%s解析失败，原因：%s" % (media_info["page_id"], e.message))
                    raise

            for video_url in media_response["video_url_list"]:
                self.main_thread_check()  # 检测主线程运行状态
                log.step(self.account_name + " 开始下载第%s个视频 %s" % (video_index, video_url))

                file_type = video_url.split("?")[0].split(".")[-1]
                video_file_path = os.path.join(self.main_thread.video_download_path, self.account_name, "%04d.%s" % (video_index, file_type))
                save_file_return = net.save_net_file(video_url, video_file_path)
                if save_file_return["status"] == 1:
                    # 设置临时目录
                    self.temp_path_list.append(video_file_path)
                    log.step(self.account_name + " 第%s个视频下载成功" % video_index)
                    video_index += 1
                else:
                    log.error(self.account_name + " 第%s个视频 %s 下载失败，原因：%s" % (video_index, video_url, crawler.download_failre(save_file_return["code"])))

        # 媒体内图片和视频全部下载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += (image_index - 1) - int(self.account_info[2])  # 计数累加
        self.total_video_count += (video_index - 1) - int(self.account_info[3])  # 计数累加
        self.account_info[2] = str(image_index - 1)  # 设置存档记录
        self.account_info[3] = str(video_index - 1)  # 设置存档记录
        self.account_info[4] = str(media_info["media_time"])

    def run(self):
        try:
            # 获取首页
            try:
                account_index_response = get_account_index_page(self.account_name)
            except crawler.CrawlerException, e:
                log.error(self.account_name + " 首页解析失败，原因：%s" % e.message)
                raise

            if self.account_info[1] == "":
                self.account_info[1] = account_index_response["account_id"]
            else:
                if self.account_info[1] != account_index_response["account_id"]:
                    log.error(self.account_name + " account id 不符合，原账号已改名")
                    tool.process_exit()

            # 获取所有可下载媒体
            media_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部媒体解析完毕，共%s个" % len(media_info_list))

            # 从最早的媒体开始下载
            while len(media_info_list) > 0:
                media_info = media_info_list.pop()
                log.step(self.account_name + " 开始解析媒体 %s" % media_info["page_id"])
                self.crawl_media(media_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个媒体正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            tool.write_file("\t".join(self.account_info), self.main_thread.temp_save_data_path)
            self.main_thread.total_image_count += self.total_image_count
            self.main_thread.total_video_count += self.total_video_count
            self.main_thread.account_list.pop(self.account_name)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片和%s个视频" % (self.total_image_count, self.total_video_count))
        self.notify_main_thread()


if __name__ == "__main__":
    Instagram().main()
