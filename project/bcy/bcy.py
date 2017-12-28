# -*- coding:UTF-8  -*-
"""
半次元图片爬虫
http://bcy.net
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as pq
import json
import os
import re
import sys
import threading
import time
import traceback

ACCOUNT_LIST = {}
TOTAL_IMAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_AUTO_FOLLOW = True
IS_LOCAL_SAVE_SESSION = False
IS_LOGIN = True
COOKIE_INFO = {"acw_tc": "", "PHPSESSID": "", "LOGGED_USER": ""}
account_file_path = os.path.realpath(os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "session.data"))


# 生成session cookies
def init_session():
    # 如果有登录信息（初始化时从浏览器中获得）
    if COOKIE_INFO["LOGGED_USER"]:
        cookies_list = {"LOGGED_USER": COOKIE_INFO["LOGGED_USER"]}
    else:
        cookies_list = None
    home_url = "http://bcy.net/home/user/index"
    home_response = net.http_request(home_url, method="GET", cookies_list=cookies_list)
    if home_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        set_cookie = net.get_cookies_from_response_header(home_response.headers)
        if "acw_tc" in set_cookie and "PHPSESSID" in set_cookie:
            COOKIE_INFO["acw_tc"] = set_cookie["acw_tc"]
            COOKIE_INFO["PHPSESSID"] = set_cookie["PHPSESSID"]
            return True
    return False


# 检测登录状态
def check_login():
    # 没有浏览器cookies，尝试读取文件
    if not COOKIE_INFO["LOGGED_USER"]:
        # 从文件中读取账号密码
        email, password = get_account_info_from_file()
        if email is not None and password is not None:
            # 模拟登录
            if _do_login(email, password):
                return True
    else:
        home_url = "http://bcy.net/home/user/index"
        home_response = net.http_request(home_url, method="GET", cookies_list=COOKIE_INFO)
        if home_response.status == net.HTTP_RETURN_CODE_SUCCEED:
            if home_response.data.find('<a href="/login">登录</a>') == -1:
                return True
    return False


# 登录
def login_from_console():
    # 从命令行中输入账号密码
    email, password = get_account_info_from_console()
    if _do_login(email, password):
        if IS_LOCAL_SAVE_SESSION:
            save_account_info_to_file(email, password)
        return True
    return False


# 模拟登录请求
def _do_login(email, password):
    login_url = "http://bcy.net/public/dologin"
    login_post = {"email": email, "password": password}
    cookies_list = {"acw_tc": COOKIE_INFO["acw_tc"], "PHPSESSID": COOKIE_INFO["PHPSESSID"]}
    login_response = net.http_request(login_url, method="POST", fields=login_post, cookies_list=cookies_list)
    if login_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if login_response.data.find('<a href="/login">登录</a>') == -1:
            return True
    return False


# 从文件中读取账号信息
def get_account_info_from_file():
    account_data = tool.decrypt_string(tool.read_file(account_file_path))
    if account_data is not None:
        try:
            account_data = json.loads(account_data)
        except ValueError:
            pass
        else:
            if robot.check_sub_key(("email", "password"), account_data):
                return account_data["email"], account_data["password"]
    return None, None


# 保存账号信息到文件中
def save_account_info_to_file(email, password):
    account_info_encrypt_string = tool.encrypt_string(json.dumps({"email": email, "password": password}))
    tool.write_file(account_info_encrypt_string, account_file_path, tool.WRITE_FILE_TYPE_REPLACE)


# 从控制台输入获取账号信息
def get_account_info_from_console():
    while True:
        email = output.console_input(robot.get_time() + " 请输入邮箱: ")
        password = output.console_input(robot.get_time() + " 请输入密码: ")
        while True:
            input_str = output.console_input(robot.get_time() + " 是否使用这些信息(Y)es或重新输入(N)o: ")
            input_str = input_str.lower()
            if input_str in ["y", "yes"]:
                return email, password
            elif input_str in ["n", "no"]:
                break
            else:
                pass


# 关注指定账号
def follow(account_id):
    follow_api_url = "http://bcy.net/weibo/Operate/follow?"
    follow_post_data = {"uid": account_id, "type": "dofollow"}
    follow_response = net.http_request(follow_api_url, method="POST", fields=follow_post_data)
    if follow_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 0 未登录，11 关注成功，12 已关注
        if int(follow_response.data) == 12:
            return True
    return False


# 取消关注指定账号
def unfollow(account_id):
    unfollow_api_url = "http://bcy.net/weibo/Operate/follow?"
    unfollow_post_data = {"uid": account_id, "type": "unfollow"}
    unfollow_response = net.http_request(unfollow_api_url, method="POST", fields=unfollow_post_data)
    if unfollow_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if int(unfollow_response.data) == 1:
            return True
    return False


# 获取指定页数的全部作品
def get_one_page_album(account_id, page_count):
    # http://bcy.net/u/50220/post/cos?&p=1
    album_pagination_url = "http://bcy.net/u/%s/post/cos" % account_id
    query_data = {"p": page_count}
    album_pagination_response = net.http_request(album_pagination_url, method="GET", fields=query_data)
    result = {
        "album_info_list": [],  # 全部作品信息
        "coser_id": None,  # coser id
        "is_over": False,  # 是不是最后一页作品
    }
    if album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(album_pagination_response.status))
    if page_count == 1 and album_pagination_response.data.find("<h2>用户不存在</h2>") >= 0:
        raise robot.RobotException("账号不存在")
    # 获取coser id
    coser_id_find = re.findall('<a href="/coser/detail/([\d]+)/\$\{post.rp_id\}', album_pagination_response.data)
    if len(coser_id_find) != 1:
        raise robot.RobotException("页面截取coser id失败\n%s" % album_pagination_response.data)
    if not robot.is_integer(coser_id_find[0]):
        raise robot.RobotException("页面截取coser id类型不正确\n%s" % album_pagination_response.data)
    result["coser_id"] = coser_id_find[0]
    # 获取作品信息
    album_list_selector = pq(album_pagination_response.data.decode("UTF-8")).find("ul.l-grid__inner li.l-grid__item")
    for album_index in range(0, album_list_selector.size()):
        album_selector = album_list_selector.eq(album_index)
        result_album_info = {
            "album_id": None,  # 作品id
            "album_title": None,  # 作品标题
        }
        # 获取作品id
        album_url = album_selector.find(".postWorkCard__img a.postWorkCard__link").attr("href")
        if not album_url:
            raise robot.RobotException("作品信息截取作品地址失败\n%s" % album_selector.html().encode("UTF-8"))
        album_id = str(album_url).split("/")[-1]
        if not robot.is_integer(album_id):
            raise robot.RobotException("作品地址 %s 截取作品id失败\n%s" % (album_url, album_selector.html().encode("UTF-8")))
        result_album_info['album_id'] = album_id
        # 获取作品标题
        album_title = album_selector.find(".postWorkCard__img img").attr("alt")
        result_album_info["album_title"] = str(album_title.encode("UTF-8"))
        result["album_info_list"].append(result_album_info)
    # 判断是不是最后一页
    last_pagination_selector = pq(album_pagination_response.data).find("#js-showPagination ul.pager li:last a")
    if last_pagination_selector.size() == 1:
        max_page_count = int(last_pagination_selector.attr("href").strip().split("&p=")[-1])
        result["is_over"] = page_count >= max_page_count
    else:
        result["is_over"] = True
    return result


# 获取指定id的作品
# coser_id -> 9299
# album_id -> 36484
def get_album_page(coser_id, album_id):
    # http://bcy.net/coser/detail/9299/36484
    album_url = "http://bcy.net/coser/detail/%s/%s" % (coser_id, album_id)
    album_response = net.http_request(album_url, method="GET", cookies_list=COOKIE_INFO)
    result = {
        "image_url_list": [],  # 全部图片地址
        "is_admin_locked": False,  # 是否被管理员锁定
        "is_only_follower": False,  # 是否只显示给粉丝
        "is_only_login": False,  # 是否只显示给登录用户
    }
    if album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(album_response.status))
    # 检测作品是否被管理员锁定
    if album_response.data.find("该作品属于下属违规情况，已被管理员锁定：") >= 0:
        result["is_admin_locked"] = True
    # 检测作品是否只对粉丝可见
    if album_response.data.find("该作品已被作者设置为只有粉丝可见") >= 0:
        result["is_only_follower"] = True
    # 检测作品是否只对登录可见
    if album_response.data.find("该作品已被作者设置为登录后可见") >= 0:
        if not IS_LOGIN:
            result["is_only_login"] = True
        else:
            raise robot.RobotException("登录状态丢失")
    # 获取作品页面内的全部图片地址列表
    image_url_list = re.findall("src='([^']*)'", album_response.data)
    if not result["is_admin_locked"] and not result["is_only_follower"] and len(image_url_list) == 0:
        raise robot.RobotException("页面匹配图片地址失败\n%s" % album_response.data)
    result["image_url_list"] = map(str, image_url_list)
    return result


# 禁用指定分辨率
def get_image_url(image_url):
    return "/".join(image_url.split("/")[0:-1])


class Bcy(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global COOKIE_INFO
        global IS_AUTO_FOLLOW
        global IS_LOCAL_SAVE_SESSION

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_GET_COOKIE: {".bcy.net": ("LOGGED_USER",)},
            robot.SYS_APP_CONFIG: (
                os.path.realpath("config.ini"),
                ("IS_AUTO_FOLLOW", True, robot.CONFIG_ANALYSIS_MODE_BOOLEAN),
                ("IS_LOCAL_SAVE_SESSION", False, robot.CONFIG_ANALYSIS_MODE_BOOLEAN)
            ),
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO["LOGGED_USER"] = self.cookie_value["LOGGED_USER"]
        IS_AUTO_FOLLOW = self.app_config["IS_AUTO_FOLLOW"]
        IS_LOCAL_SAVE_SESSION = self.app_config["IS_LOCAL_SAVE_SESSION"]

    def main(self):
        global ACCOUNT_LIST

        # 生成session信息
        init_session()

        # 检测登录状态
        # 未登录时提示可能无法获取粉丝指定的作品
        if not check_login():
            while True:
                input_str = output.console_input(robot.get_time() + " 没有检测到账号登录状态，可能无法解析那些只对粉丝开放的作品，手动输入账号密码登录(Y)es？或者跳过登录继续程序(C)ontinue？或者退出程序(E)xit？:")
                input_str = input_str.lower()
                if input_str in ["y", "yes"]:
                    if login_from_console():
                        break
                    else:
                        log.step("登录失败！")
                elif input_str in ["e", "exit"]:
                    tool.process_exit()
                elif input_str in ["c", "continue"]:
                    global IS_LOGIN
                    IS_LOGIN = False
                    break

        # 解析存档文件
        # account_id  last_album_id
        ACCOUNT_LIST = robot.read_save_data(self.save_data_path, 0, ["", "0"])

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(ACCOUNT_LIST.keys()):
            # 检查正在运行的线程数
            if threading.activeCount() >= self.thread_count + main_thread_count:
                self.wait_sub_thread()

            # 提前结束
            if not self.is_running():
                break

            # 开始下载
            thread = Download(ACCOUNT_LIST[account_id], self)
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            self.wait_sub_thread()

        # 未完成的数据保存
        if len(ACCOUNT_LIST) > 0:
            tool.write_file(tool.list_to_string(ACCOUNT_LIST.values()), NEW_SAVE_DATA_PATH)

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(robot.DownloadThread):
    def __init__(self, account_info, main_thread):
        robot.DownloadThread.__init__(self, account_info, main_thread)
        self.account_id = self.account_info[0]
        if len(self.account_info) >= 3:
            self.account_name = self.account_info[2]
        else:
            self.account_name = self.account_info[0]
        self.coser_id = None
        log.step(self.account_name + " 开始")

    # 获取所有可下载作品
    def get_crawl_list(self):
        page_count = 1
        unique_list = []
        album_info_list = []
        is_over = False
        while not is_over:
            self.main_thread_check()  # 检测主线程运行状态
            log.step(self.account_name + " 开始解析第%s页作品" % page_count)

            # 获取一页作品
            try:
                album_pagination_response = get_one_page_album(self.account_id, page_count)
            except robot.RobotException, e:
                log.error(self.account_name + " 第%s页作品解析失败，原因：%s" % (page_count, e.message))
                raise

            if self.coser_id is None:
                self.coser_id = album_pagination_response["coser_id"]

            log.trace(self.account_name + " 第%s页解析的全部作品：%s" % (page_count, album_pagination_response["album_info_list"]))

            # 寻找这一页符合条件的作品
            for album_info in album_pagination_response["album_info_list"]:
                # 新增作品导致的重复判断
                if album_info["album_id"] in unique_list:
                    continue
                else:
                    unique_list.append(album_info["album_id"])

                # 检查是否达到存档记录
                if int(album_info["album_id"]) > int(self.account_info[1]):
                    album_info_list.append(album_info)
                else:
                    is_over = True
                    break

            if not is_over:
                if album_pagination_response["is_over"]:
                    is_over = True
                else:
                    page_count += 1

        return album_info_list

    # 解析单个作品
    def crawl_album(self, album_info):
        self.main_thread_check()  # 检测主线程运行状态
        # 获取作品
        try:
            album_response = get_album_page(self.coser_id, album_info["album_id"])
        except robot.RobotException, e:
            log.error(self.account_name + " 作品%s 《%s》解析失败，原因：%s" % (album_info["album_id"], album_info["album_title"], e.message))
            raise

        # 是不是已被管理员锁定
        if album_response["is_admin_locked"]:
            log.error(self.account_name + " 作品%s 《%s》已被管理员锁定，跳过" % (album_info["album_id"], album_info["album_title"]))
            return

        # 是不是只对登录账号可见
        if album_response["is_only_login"]:
            log.error(self.account_name + " 作品%s 《%s》只对登录账号显示，跳过" % (album_info["album_id"], album_info["album_title"]))
            return

        # 是不是只对粉丝可见，并判断是否需要自动关注
        if album_response["is_only_follower"]:
            if not IS_LOGIN or not IS_AUTO_FOLLOW:
                return
            log.step(self.account_name + " 作品%s 《%s》是私密作品且账号不是ta的粉丝，自动关注" % (album_info["album_id"], album_info["album_title"]))
            if follow(self.account_id):
                self.main_thread_check()  # 检测主线程运行状态
                # 重新获取作品页面
                try:
                    album_response = get_album_page(self.coser_id, album_info["album_id"])
                except robot.RobotException, e:
                    log.error(self.account_name + " 作品%s 《%s》解析失败，原因：%s" % (album_info["album_id"], album_info["album_title"], e.message))
                    raise
            else:
                # 关注失败
                log.error(self.account_name + " 关注失败，跳过作品%s 《%s》" % (album_info["album_id"], album_info["album_title"]))
                return

        image_index = 1
        # 过滤标题中不支持的字符
        album_title = path.filter_text(album_info["album_title"])
        if album_title:
            album_path = os.path.join(IMAGE_DOWNLOAD_PATH, self.account_name, "%s %s" % (album_info["album_id"], album_title))
        else:
            album_path = os.path.join(IMAGE_DOWNLOAD_PATH, self.account_name, str(album_info["album_id"]))
        # 设置临时目录
        self.temp_path_list.append(album_path)
        for image_url in album_response["image_url_list"]:
            self.main_thread_check()  # 检测主线程运行状态
            # 禁用指定分辨率
            image_url = get_image_url(image_url)
            log.step(self.account_name + " 作品%s 《%s》开始下载第%s张图片 %s" % (album_info["album_id"], album_info["album_title"], image_index, image_url))

            if image_url.rfind("/") < image_url.rfind("."):
                file_type = image_url.split(".")[-1]
            else:
                file_type = "jpg"
            file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
            save_file_return = net.save_net_file(image_url, file_path)
            if save_file_return["status"] == 1:
                log.step(self.account_name + " 作品%s 《%s》第%s张图片下载成功" % (album_info["album_id"], album_info["album_title"], image_index))
                image_index += 1
            else:
                log.error(self.account_name + " 作品%s 《%s》第%s张图片 %s，下载失败，原因：%s" % (album_info["album_id"], album_info["album_title"], image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

        # 作品内图片下全部载完毕
        self.temp_path_list = []  # 临时目录设置清除
        self.total_image_count += image_index - 1  # 计数累加
        self.account_info[1] = album_info["album_id"]  # 设置存档记录

    def run(self):
        try:
            # 获取所有可下载作品
            album_info_list = self.get_crawl_list()
            log.step(self.account_name + " 需要下载的全部作品解析完毕，共%s个" % len(album_info_list))

            # 从最早的作品开始下载
            while len(album_info_list) > 0:
                album_info = album_info_list.pop()
                log.step(self.account_name + " 开始解析作品%s 《%s》" % (album_info["album_id"], album_info["album_title"]))
                self.crawl_album(album_info)
                self.main_thread_check()  # 检测主线程运行状态
        except SystemExit, se:
            if se.code == 0:
                log.step(self.account_name + " 提前退出")
            else:
                log.error(self.account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个图集正在下载中，需要把下载了部分的内容给清理掉
            self.clean_temp_path()
        except Exception, e:
            log.error(self.account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        with self.thread_lock:
            global TOTAL_IMAGE_COUNT
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += self.total_image_count
            ACCOUNT_LIST.pop(self.account_id)
        log.step(self.account_name + " 下载完毕，总共获得%s张图片" % self.total_image_count)
        self.notify_main_thread()


if __name__ == "__main__":
    Bcy().main()
