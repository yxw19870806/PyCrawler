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
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_AUTO_FOLLOW = True
IS_LOGIN = True
COOKIE_INFO = {"acw_tc": "", "PHPSESSID": "", "LOGGED_USER": ""}


# 检测登录状态
def check_login():
    if not COOKIE_INFO["LOGGED_USER"]:
        return False
    cookies_list = {"LOGGED_USER": COOKIE_INFO["LOGGED_USER"]}
    index_url = "http://bcy.net/"
    index_response = net.http_request(index_url, cookies_list=cookies_list)
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        set_cookie = net.get_cookies_from_response_header(index_response.headers)
        if "acw_tc" in set_cookie and "PHPSESSID" in set_cookie:
            COOKIE_INFO["acw_tc"] = set_cookie["acw_tc"]
            COOKIE_INFO["PHPSESSID"] = set_cookie["PHPSESSID"]
    if not COOKIE_INFO["acw_tc"] or not COOKIE_INFO["PHPSESSID"]:
        return False
    home_url = "http://bcy.net/home/user/index"
    home_response = net.http_request(home_url, cookies_list=COOKIE_INFO)
    if home_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if home_response.data.find('<a href="/login">登录</a>') == -1:
            return True
    return False


# 从控制台输入获取账号信息
def get_account_info_from_console():
    while True:
        email = tool.console_input(tool.get_time() + " 请输入邮箱: ")
        password = tool.console_input(tool.get_time() + " 请输入密码: ")
        while True:
            input_str = tool.console_input(tool.get_time() + " 是否使用这些信息(Y)es或重新输入(N)o: ")
            input_str = input_str.lower()
            if input_str in ["y", "yes"]:
                return email, password
            elif input_str in ["n", "no"]:
                break
            else:
                pass


# 模拟登录
def login():
    global COOKIE_INFO
    # 访问首页，获取一个随机session id
    home_url = "http://bcy.net/home/user/index"
    home_response = net.http_request(home_url)
    if home_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        set_cookie = net.get_cookies_from_response_header(home_response.headers)
        if "acw_tc" in set_cookie and "PHPSESSID" in set_cookie:
            COOKIE_INFO["acw_tc"] = set_cookie["acw_tc"]
            COOKIE_INFO["PHPSESSID"] = set_cookie["PHPSESSID"]
        else:
            return False
    else:
        return False
    # 从命令行中输入账号密码
    email, password = get_account_info_from_console()
    login_url = "http://bcy.net/public/dologin"
    login_post = {"email": email, "password": password}
    cookies_list = {"acw_tc": COOKIE_INFO["acw_tc"], "PHPSESSID": COOKIE_INFO["PHPSESSID"]}
    login_response = net.http_request(login_url, method="POST", post_data=login_post, cookies_list=cookies_list)
    if login_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if login_response.data.find('<a href="/login">登录</a>') == -1:
            return True
    return False


# 关注指定账号
def follow(account_id):
    follow_api_url = "http://bcy.net/weibo/Operate/follow?"
    follow_post_data = {"uid": account_id, "type": "dofollow"}
    follow_response = net.http_request(follow_api_url, method="POST", post_data=follow_post_data)
    if follow_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 0 未登录，11 关注成功，12 已关注
        if int(follow_response.data) == 12:
            return True
    return False


# 取消关注指定账号
def unfollow(account_id):
    unfollow_api_url = "http://bcy.net/weibo/Operate/follow?"
    unfollow_post_data = {"uid": account_id, "type": "unfollow"}
    unfollow_response = net.http_request(unfollow_api_url, method="POST", post_data=unfollow_post_data)
    if unfollow_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if int(unfollow_response.data) == 1:
            return True
    return False


# 获取指定页数的所有作品
def get_one_page_album(account_id, page_count):
    # http://bcy.net/u/50220/post/cos?&p=1
    album_pagination_url = "http://bcy.net/u/%s/post/cos?&p=%s" % (account_id, page_count)
    album_pagination_response = net.http_request(album_pagination_url)
    result = {
        "coser_id": None,  # coser id
        "album_info_list": [],  # 所有作品信息
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
        extra_album_info = {
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
        extra_album_info['album_id'] = album_id
        # 获取作品标题
        album_title = album_selector.find(".postWorkCard__img footer").text()
        extra_album_info["album_title"] = str(album_title.encode("UTF-8"))
        result["album_info_list"].append(extra_album_info)
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
    album_response = net.http_request(album_url, cookies_list=COOKIE_INFO)
    result = {
        "is_admin_locked": False,  # 是否被管理员锁定
        "is_only_follower": False,  # 是否只显示给粉丝
        "is_only_login": False,  # 是否只显示给登录用户
        "image_url_list": [],  # 页面解析出的所有图片地址列表
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
        result["is_only_login"] = True
    # 获取作品页面内的所有图片地址列表
    image_url_list = re.findall("src='([^']*)'", album_response.data)
    if not result["is_admin_locked"] and not result["is_only_follower"] and len(image_url_list) == 0:
        raise robot.RobotException("页面匹配图片地址失败\n%s" % album_response.data)
    result["image_url_list"] = map(str, image_url_list)
    return result


class Bcy(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global COOKIE_INFO
        global IS_AUTO_FOLLOW

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_GET_COOKIE: {".bcy.net": ("LOGGED_USER",)},
            robot.SYS_APP_CONFIG: (os.path.realpath("config.ini"), ("IS_AUTO_FOLLOW", True, 2)),
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO["LOGGED_USER"] = self.cookie_value["LOGGED_USER"]
        IS_AUTO_FOLLOW = self.app_config["IS_AUTO_FOLLOW"]

    def main(self):
        global ACCOUNTS

        # 检测登录状态
        # 未登录时提示可能无法获取粉丝指定的作品
        if not check_login():
            while True:
                input_str = tool.console_input(tool.get_time() + " 没有检测到您的账号信息，可能无法解析那些只对粉丝开放的隐藏作品，是否手动输入账号密码登录(Y)es？ 或者跳过登录继续程序(C)ontinue？或者退出程序(E)xit？:")
                input_str = input_str.lower()
                if input_str in ["y", "yes"]:
                    if login():
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

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock
        self.temp_path = ""

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]
        total_image_count = 0

        try:
            log.step(account_name + " 开始")

            page_count = 1
            unique_list = []
            album_info_list = []
            is_over = False
            coser_id = None
            # 获取全部还未下载过需要解析的作品
            while not is_over:
                log.step(account_name + " 开始解析第%s页作品" % page_count)

                # 获取一页作品
                try:
                    album_pagination_response = get_one_page_album(account_id, page_count)
                except robot.RobotException, e:
                    log.error(account_name + " 第%s页作品解析失败，原因：%s" % (page_count, e.message))
                    raise

                coser_id = album_pagination_response["coser_id"]

                log.trace(account_name + " 第%s页解析的所有作品：%s" % (page_count, album_pagination_response["album_info_list"]))

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

            log.step(account_name + " 需要下载的全部作品解析完毕，共%s个" % len(album_info_list))

            # 从最早的作品开始下载
            while len(album_info_list) > 0:
                album_info = album_info_list.pop()
                log.step(account_name + " 开始解析作品%s 《%s》" % (album_info["album_id"], album_info["album_title"]))

                # 获取作品
                try:
                    album_response = get_album_page(coser_id, album_info["album_id"])
                except robot.RobotException, e:
                    log.error(account_name + " 作品%s 《%s》解析失败，原因：%s" % (album_info["album_id"], album_info["album_title"], e.message))
                    raise

                # 是不是已被管理员锁定
                if album_response["is_admin_locked"]:
                    log.error(account_name + " 作品%s 《%s》已被管理员锁定，跳过" % (album_info["album_id"], album_info["album_title"]))
                    continue

                # 是不是只对登录账号可见
                if album_response["is_only_login"]:
                    log.error(account_name + " 作品%s 《%s》只对登录账号显示，跳过" % (album_info["album_id"], album_info["album_title"]))
                    if not IS_LOGIN:
                        continue
                    else:
                        tool.process_exit()

                # 是不是只对粉丝可见，并判断是否需要自动关注
                if album_response["is_only_follower"]:
                    if not IS_LOGIN or not IS_AUTO_FOLLOW:
                        continue
                    log.step(account_name + " 作品%s 《%s》是私密作品且账号不是ta的粉丝，自动关注" % (album_info["album_id"], album_info["album_title"]))
                    if follow(account_id):
                        # 重新获取作品页面
                        try:
                            album_response = get_album_page(coser_id, album_info["album_id"])
                        except robot.RobotException, e:
                            log.error(account_name + " 作品%s 《%s》解析失败，原因：%s" % (album_info["album_id"], album_info["album_title"], e.message))
                            raise
                    else:
                        # 关注失败
                        log.error(account_name + " 关注失败，跳过作品%s 《%s》" % (album_info["album_id"], album_info["album_title"]))
                        continue

                image_count = 1
                # 过滤标题中不支持的字符
                album_title = robot.filter_text(album_info["album_title"])
                if album_title:
                    album_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, "%s %s" % (album_info["album_id"], album_title))
                else:
                    album_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name, str(album_info["album_id"]))
                # 正在下载的目录
                self.temp_path = album_path
                for image_url in album_response["image_url_list"]:
                    # 禁用指定分辨率
                    image_url = "/".join(image_url.split("/")[0:-1])
                    log.step(account_name + " 作品%s 《%s》开始下载第%s张图片 %s" % (album_info["album_id"], album_info["album_title"], image_count, image_url))

                    if image_url.rfind("/") < image_url.rfind("."):
                        file_type = image_url.split(".")[-1]
                    else:
                        file_type = "jpg"
                    file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step(account_name + " 作品%s 《%s》第%s张图片下载成功" % (album_info["album_id"], album_info["album_title"], image_count))
                        image_count += 1
                    else:
                        log.error(account_name + " 作品%s 《%s》第%s张图片 %s，下载失败，原因：%s" % (album_info["album_id"], album_info["album_title"], image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                # 作品全部图片下载完毕
                self.temp_path = ""  # 临时目录设置清除
                self.account_info[1] = album_info["album_id"]  # 设置存档记录
                total_image_count += image_count - 1  # 计数累加
        except SystemExit, se:
            if se.code == 0:
                log.step(account_name + " 提前退出")
            else:
                log.error(account_name + " 异常退出")
            # 如果临时目录变量不为空，表示某个图集正在下载中，需要把下载了部分的内容给清理掉
            if self.temp_path:
                tool.remove_dir_or_file(self.temp_path)
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 保存最后的信息
        self.thread_lock.acquire()
        tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
        TOTAL_IMAGE_COUNT += total_image_count
        ACCOUNTS.remove(account_id)
        self.thread_lock.release()
        log.step(account_name + " 下载完毕，总共获得%s张图片" % total_image_count)


if __name__ == "__main__":
    Bcy().main()
