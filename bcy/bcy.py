# -*- coding:UTF-8  -*-
"""
半次元图片爬虫
http://bcy.net
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import base64
import json
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
GET_PAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_AUTO_FOLLOW = True
NOT_LOGIN_CAN_RUN = False
SAVE_ACCOUNT_INFO = True
COOKIE_INFO = {"acw_tc": "", "PHPSESSID": ""}


# 检测登录状态
def check_login():
    if not COOKIE_INFO["acw_tc"] or not COOKIE_INFO["PHPSESSID"]:
        return False
    home_page_url = "http://bcy.net/home/user/index"
    header_list = {"Cookie": "acw_tc=%s; PHPSESSID=%s; mobile_set=no" % (COOKIE_INFO["acw_tc"], COOKIE_INFO["PHPSESSID"])}
    home_page_response = net.http_request(home_page_url, header_list=header_list)
    if home_page_response.status == 200:
        if home_page_response.data.find('<a href="/login">登录</a>') == -1:
            return True
        else:
            return False
    return False


# 从文件中获取账号信息
def read_cookie_info_from_file():
    if not os.path.exists("account.data"):
        return False
    file_handle = open("account.data", "r")
    cookie_info = file_handle.read()
    file_handle.close()
    try:
        cookie_info = json.loads(base64.b64decode(cookie_info[1:]))
    except TypeError:
        pass
    except ValueError:
        pass
    else:
        if robot.check_sub_key(("acw_tc", "PHPSESSID"), cookie_info):
            global COOKIE_INFO
            COOKIE_INFO["acw_tc"] = cookie_info["acw_tc"]
            COOKIE_INFO["PHPSESSID"] = cookie_info["PHPSESSID"]
            return True
    return False


# 保存账号信息到到文件中
def save_cookie_info_to_file(cookie_info):
    account_info = tool.generate_random_string(1) + base64.b64encode(json.dumps(cookie_info))
    file_handle = open("account.data", "w")
    file_handle.write(account_info)
    file_handle.close()


# 从控制台输入获取账号信息
def get_account_info_from_console():
    while True:
        email = raw_input(tool.get_time() + " 请输入邮箱: ")
        password = raw_input(tool.get_time() + " 请输入密码: ")
        while True:
            input_str = raw_input(tool.get_time() + " 是否使用这些信息(Y)es或重新输入(N)o: ")
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
    home_page_url = "http://bcy.net/home/user/index"
    home_page_response = net.http_request(home_page_url)
    if home_page_response.status == 200 and "Set-Cookie" in home_page_response.headers:
        COOKIE_INFO["acw_tc"] = tool.find_sub_string(home_page_response.headers["Set-Cookie"], "acw_tc=", ";")
        COOKIE_INFO["PHPSESSID"] = tool.find_sub_string(home_page_response.headers["Set-Cookie"], "PHPSESSID=", ";")
    else:
        return False
    # 从命令行中输入账号密码
    email, password = get_account_info_from_console()
    login_url = "http://bcy.net/public/dologin"
    login_post = {"email": email, "password": password}
    header_list = {"Cookie": "acw_tc=%s; PHPSESSID=%s; mobile_set=no" % (COOKIE_INFO["acw_tc"], COOKIE_INFO["PHPSESSID"])}
    login_response = net.http_request(login_url, login_post, header_list=header_list)
    if login_response.status == 200:
        if login_response.data.find('<a href="/login">登录</a>') == -1:
            if SAVE_ACCOUNT_INFO:
                save_cookie_info_to_file(COOKIE_INFO)
            return True
    return False


# 关注指定账号
def follow(account_id):
    follow_url = "http://bcy.net/weibo/Operate/follow?"
    follow_post_data = {"uid": account_id, "type": "dofollow"}
    follow_response = net.http_request(follow_url, follow_post_data)
    if follow_response.status == 200:
        # 0 未登录，11 关注成功，12 已关注
        if int(follow_response.data) == 12:
            return True
    return False


# 取消关注指定账号
def unfollow(account_id):
    unfollow_url = "http://bcy.net/weibo/Operate/follow?"
    unfollow_post_data = {"uid": account_id, "type": "unfollow"}
    unfollow_response = net.http_request(unfollow_url, unfollow_post_data)
    if unfollow_response.status == 200:
        if int(unfollow_response.data) == 1:
            return True
    return False


# 获取一页的作品信息
def get_one_page_post(account_id, page_count):
    # http://bcy.net/u/50220/post/cos?&p=1
    post_url = "http://bcy.net/u/%s/post/cos?&p=%s" % (account_id, page_count)
    return net.http_request(post_url)


# 解析作品信息，获取所有的作品信息
def get_album_list(post_page):
    cp_and_album_id_list = re.findall('/coser/detail/(\d+)/(\d+)"', post_page)
    title_list = re.findall('<img src="\S*" alt="([\S ]*)" />', post_page)
    if "${post.title}" in title_list:
        title_list.remove("${post.title}")
    coser_id = None
    album_list = {}
    if len(cp_and_album_id_list) == len(title_list):
        for coser_id, album_id in cp_and_album_id_list:
            album_list[album_id] = title_list.pop(0)
    return coser_id, album_list


# 获取作品页面
# coser_id -> 9299
# album_id -> 36484
def get_album_page(coser_id, album_id):
    # http://bcy.net/coser/detail/9299/36484
    album_page_url = "http://bcy.net/coser/detail/%s/%s" % (coser_id, album_id)
    return net.http_request(album_page_url)


# 检测作品是否被管理员锁定
def is_invalid_album(album_page):
    return album_page.find("该作品属于下属违规情况，已被管理员锁定：") >= 0


# 获取作品页面内的所有图片地址列表
def get_image_url_list(album_page):
    return re.findall("src='([^']*)'", album_page)


# 根据当前作品页面，获取作品页数上限
def get_max_page_count(account_id, post_page):
    max_page_count = tool.find_sub_string(post_page, '<a href="/u/%s/post/cos?&p=' % account_id, '">')
    if max_page_count:
        max_page_count = int(max_page_count)
    else:
        max_page_count = 1
    return max_page_count


class Bcy(robot.Robot):
    def __init__(self):
        global GET_PAGE_COUNT
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global COOKIE_INFO

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_GET_COOKIE: {"bcy.net": ("acw_tc", "PHPSESSID")},
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_PAGE_COUNT = self.get_page_count
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        COOKIE_INFO["acw_tc"] = self.cookie_value["acw_tc"]
        # COOKIE_INFO["PHPSESSID"] = self.cookie_value["PHPSESSID"]

    def main(self):
        global ACCOUNTS

        # 检测登录状态
        # 未登录时提示可能无法获取粉丝指定的作品
        if not check_login():
            # 尝试从文件中获取账号信息
            if read_cookie_info_from_file() and check_login():
                pass
            else:
                while True:
                    input_str = raw_input(tool.get_time() + " 没有检测到您的账号信息，可能无法获取那些只对粉丝开放的隐藏作品，是否手动输入账号密码登录(Y)es？ 或者跳过登录继续程序(C)ontinue？或者退出程序(E)xit？:")
                    input_str = input_str.lower()
                    if input_str in ["y", "yes"]:
                        if login():
                            break
                        else:
                            log.step("登录失败！")
                    elif input_str in ["e", "exit"]:
                        tool.process_exit()
                    elif input_str in ["c", "continue"]:
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

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 3:
            account_name = self.account_info[2]
        else:
            account_name = self.account_info[0]

        try:
            log.step(account_name + " 开始")

            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_name)

            # 图片下载
            this_account_total_image_count = 0
            page_count = 1
            total_album_count = 1
            first_album_id = ""
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                log.step(account_name + " 开始解析第%s页作品" % page_count)

                # 获取一页的作品信息
                post_page_response = get_one_page_post(account_id, page_count)
                if post_page_response.status != 200:
                    log.error(account_name + " 第%s页作品访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(post_page_response.status)))
                    tool.process_exit()

                # 解析作品信息，获取所有的作品信息
                coser_id, album_list = get_album_list(post_page_response.data)
                if coser_id is None:
                    log.error(account_name + " 第%s页作品解析异常" % page_count)
                    tool.process_exit()
                log.trace(account_name + " coser id：%s" % coser_id)
                log.trace(account_name + " 第%s页获取的所有作品：%s" % (page_count, album_list))

                for album_id, title in album_list.iteritems():
                    # 检查是否已下载到前一次的图片
                    if int(album_id) <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 将第一个作品的id做为新的存档记录
                    if first_album_id == "":
                        first_album_id = album_id

                    # 新增作品导致的重复判断
                    if album_id in unique_list:
                        continue
                    else:
                        unique_list.append(album_id)

                    log.step(account_name + " 开始解析作品%s 《%s》" % (album_id, title))

                    if need_make_download_dir:
                        if not tool.make_dir(image_path, 0):
                            log.error(account_name + " 创建下载目录 %s 失败" % image_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    # 过滤标题中不支持的字符
                    filtered_title = robot.filter_text(title)
                    if filtered_title:
                        album_path = os.path.join(image_path, "%s %s" % (album_id, filtered_title))
                    else:
                        album_path = os.path.join(image_path, album_id)
                    if not tool.make_dir(album_path, 0):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        log.error(account_name + " 创建作品目录 %s 失败，尝试不使用title" % album_path)
                        album_path = os.path.join(image_path, album_id)
                        if not tool.make_dir(album_path, 0):
                            log.error(account_name + " 创建作品目录 %s 失败" % album_path)
                            tool.process_exit()

                    # 获取作品页面
                    album_page_response = get_album_page(coser_id, album_id)
                    if album_page_response.status != 200:
                        log.error(account_name + " 作品%s 《%s》（coser_id：%s）访问失败，原因：%s" % (album_id, coser_id, title, robot.get_http_request_failed_reason(album_page_response.status)))
                        tool.process_exit()

                    if is_invalid_album(album_page_response.data):
                        log.error(account_name + " 作品%s 《%s》（coser_id：%s）已被管理员锁定，跳过" % (album_id, title, coser_id))
                        continue

                    # 获取作品中的全部图片地址
                    image_url_list = get_image_url_list(album_page_response.data)

                    if len(image_url_list) == 0 and IS_AUTO_FOLLOW:
                        log.step(account_name + " 检测到可能有私密作品且账号不是ta的粉丝，自动关注")
                        if follow(account_id):
                            # 重新获取作品页面
                            album_page_response = get_album_page(coser_id, album_id)
                            if album_page_response.status != 200:
                                log.error(account_name + " 作品%s 《%s》（coser_id：%s）访问失败，原因：%s" % (album_id, title, coser_id, robot.get_http_request_failed_reason(album_page_response.status)))
                                tool.process_exit()
                            # 重新获取作品中的全部图片地址
                            image_url_list = get_image_url_list(album_page_response.data)

                    if len(image_url_list) == 0:
                        log.error(account_name + " 作品%s 《%s》（coser_id：%s）没有任何图片，可能是你使用的账号没有关注ta，所以无法访问只对粉丝开放的私密作品" % (album_id, title, coser_id))
                        continue

                    image_count = 1
                    for image_url in list(image_url_list):
                        # 禁用指定分辨率
                        image_url = "/".join(image_url.split("/")[0:-1])
                        log.step(account_name + " %s 《%s》开始下载第%s张图片 %s" % (album_id, title, image_count, image_url))

                        if image_url.rfind("/") < image_url.rfind("."):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = "jpg"
                        file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                        save_file_return = net.save_net_file(image_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step(account_name + " %s 《%s》第%s张图片下载成功" % (album_id, title, image_count))
                            image_count += 1
                        else:
                            log.error(" %s 《%s》第%s张图片 %s，下载失败，原因：%s" % (album_id, title, image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

                    this_account_total_image_count += image_count - 1

                    if 0 < GET_PAGE_COUNT < total_album_count:
                        is_over = True
                        break
                    else:
                        total_album_count += 1

                if not is_over:
                    if page_count >= get_max_page_count(account_id, post_page_response.data):
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_name + " 下载完毕，总共获得%s张图片" % this_account_total_image_count)

            # 新的存档记录
            if first_album_id != "":
                self.account_info[1] = first_album_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += this_account_total_image_count
            ACCOUNTS.remove(account_id)
            self.thread_lock.release()

            log.step(account_name + " 完成")
        except SystemExit:
            log.error(account_name + " 异常退出")
        except Exception, e:
            log.error(account_name + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Bcy().main()
