# -*- coding:UTF-8  -*-
"""
半次元图片爬虫
http://bcy.net
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import base64
import cookielib
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

threadLock = threading.Lock()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


# 从控制台输入获取账号信息
def get_account_info_from_console():
    while True:
        email = raw_input(tool.get_time() + " 请输入邮箱: ")
        password = raw_input(tool.get_time() + " 请输入密码: ")
        while True:
            input_str = raw_input(tool.get_time() + " 是否使用这些信息（Y）或重新输入（N）: ")
            input_str = input_str.lower()
            if input_str in ["y", "yes"]:
                return email, password
            elif input_str in ["n", "no"]:
                break
            else:
                pass


# 从文件中获取账号信息
def get_account_info_from_file():
    if not os.path.exists("account.data"):
        return False
    file_handle = open("account.data", "r")
    account_info = file_handle.read()
    file_handle.close()
    try:
        account_info = json.loads(base64.b64decode(account_info))
    except TypeError:
        account_info = {}
    except ValueError:
        account_info = {}
    if robot.check_sub_key(("email", "password"), account_info):
        return account_info["email"], account_info["password"]
    return None, None


# 模拟登录
def login(from_where):
    if from_where == 1:
        email, password = get_account_info_from_file
    else:
        email, password = get_account_info_from_console()
        account_info = base64.b64encode(json.dumps({"email": email, "password": password}))
        file_handle = open("account.data", "w")
        file_handle.write(account_info)
        file_handle.close()

    cookie = cookielib.CookieJar()
    login_url = "http://bcy.net/public/dologin"
    login_post = {"email": email, "password": password}
    login_return_code = tool.http_request(login_url, login_post, cookie)[0]
    if login_return_code == 1:
        return True
    else:
        return False


# 关注指定账号
def follow(account_id):
    follow_url = "http://bcy.net/weibo/Operate/follow?"
    follow_post_data = {"uid": account_id, "type": "dofollow"}
    follow_return_code, follow_return_data = tool.http_request(follow_url, follow_post_data)[:2]
    if follow_return_code == 1:
        # 0 未登录，11 关注成功，12 已关注
        if int(follow_return_data) == 12:
            return True
    return False


# 取消关注指定账号
def unfollow(account_id):
    unfollow_url = "http://bcy.net/weibo/Operate/follow?"
    unfollow_post_data = {"uid": account_id, "type": "unfollow"}
    unfollow_return_code, unfollow_return_data = tool.http_request(unfollow_url, unfollow_post_data)[:2]
    if unfollow_return_code == 1:
        if int(unfollow_return_data) == 1:
            return True
    return False


# 检测登录状态
def check_login():
    home_page_url = "http://bcy.net/home/user/index"
    home_page_return = tool.http_request(home_page_url)
    if home_page_return[0] == 1:
        real_url = home_page_return[2].geturl()
        if (home_page_url != real_url) or ("http://bcy.net/start" == real_url):
            is_check_ok = False
            while not is_check_ok:
                input_str = raw_input(tool.get_time() + " 没有检测到您的账号信息，可能无法获取那些只对粉丝开放的隐藏作品，是否下一步操作？ (Y)es or (N)o: ")
                input_str = input_str.lower()
                if input_str in ["y", "yes"]:
                    is_check_ok = True
                elif input_str in ["n", "no"]:
                    tool.process_exit()


# 获取一页的作品信息
def get_one_page_post(coser_id, page_count):
    # http://bcy.net/u/50220/post/cos?&p=1
    post_url = "http://bcy.net/u/%s/post/cos?&p=%s" % (coser_id, page_count)
    post_page_return_code, post_page = tool.http_request(post_url)[:2]
    if post_page_return_code == 1:
        return post_page
    return None


# 解析作品信息，获取所有的正片信息
def get_rp_list(post_page):
    cp_and_rp_id_list = re.findall('/coser/detail/(\d+)/(\d+)"', post_page)
    title_list = re.findall('<img src="\S*" alt="([\S ]*)" />', post_page)
    if "${post.title}" in title_list:
        title_list.remove("${post.title}")
    cp_id = None
    rp_list = {}
    if len(cp_and_rp_id_list) == len(title_list):
        for cp_id, rp_id in cp_and_rp_id_list:
            rp_list[rp_id] = title_list.pop(0)
    return cp_id, rp_list


# 获取正片页面内的所有图片地址列表
# cp_id -> 9299
# rp_id -> 36484
def get_image_url_list(cp_id, rp_id):
    # http://bcy.net/coser/detail/9299/36484
    rp_url = "http://bcy.net/coser/detail/%s/%s" % (cp_id, rp_id)
    rp_page_return_code, rp_page_response = tool.http_request(rp_url)[:2]
    if rp_page_return_code == 1:
        return re.findall("src='([^']*)'", rp_page_response)
    return None


# 根据当前作品页面，获取作品页数上限
def get_max_page_count(coser_id, post_page):
    max_page_count = tool.find_sub_string(post_page, '<a href="/u/%s/post/cos?&p=' % coser_id, '">尾页</a>')
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

        sys_config = {
             robot.SYS_DOWNLOAD_IMAGE: True,
             robot.SYS_SET_COOKIE: ("bcy.net",),
        }
        robot.Robot.__init__(self, sys_config)

        # 设置全局变量，供子线程调用
        GET_PAGE_COUNT = self.get_page_count
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

    def main(self):
        global ACCOUNTS

        # 检测登录状态
        # 未登录时提示可能无法获取粉丝指定的作品
        check_login()

        # 解析存档文件
        # account_id  last_rp_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                time.sleep(10)

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id])
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

        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT

        coser_id = self.account_info[0]
        if len(self.account_info) >= 3:
            cn = self.account_info[2]
        else:
            cn = self.account_info[0]

        try:
            print_step_msg(cn + " 开始")

            image_path = os.path.join(IMAGE_DOWNLOAD_PATH, cn)

            # 图片下载
            this_cn_total_image_count = 0
            page_count = 1
            total_rp_count = 1
            first_rp_id = ""
            unique_list = []
            is_over = False
            need_make_download_dir = True  # 是否需要创建cn目录
            while not is_over:
                # 获取一页的作品信息
                post_page = get_one_page_post(coser_id, page_count)
                if post_page is None:
                    print_error_msg(cn + " 无法访问第%s页作品" % page_count)
                    tool.process_exit()

                # 解析作品信息，获取所有的正片信息
                cp_id, rp_list = get_rp_list(post_page)
                if cp_id is None:
                    print_error_msg(cn + " 第%s页作品解析异常" % page_count)
                    tool.process_exit()

                for rp_id, title in rp_list.iteritems():
                    # 检查是否已下载到前一次的图片
                    if int(rp_id) <= int(self.account_info[1]):
                        is_over = True
                        break

                    # 新增正片导致的重复判断
                    if rp_id in unique_list:
                        continue
                    else:
                        unique_list.append(rp_id)
                    # 将第一个作品的id做为新的存档记录
                    if first_rp_id == "":
                        first_rp_id = rp_id

                    print_step_msg("rp: " + rp_id)

                    if need_make_download_dir:
                        if not tool.make_dir(image_path, 0):
                            print_error_msg(cn + " 创建CN目录 %s 失败" % image_path)
                            tool.process_exit()
                        need_make_download_dir = False

                    # 标题处理
                    for filter_char in ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]:
                        title = title.replace(filter_char, " ")  # 过滤一些windows文件名屏蔽的字符
                    title = title.strip()  # 去除前后空格
                    if title:
                        rp_path = os.path.join(image_path, "%s %s" % (rp_id, title))
                    else:
                        rp_path = os.path.join(image_path, rp_id)
                    if not tool.make_dir(rp_path, 0):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        print_error_msg(cn + " 创建作品目录 %s 失败，尝试不使用title" % rp_path)
                        rp_path = os.path.join(image_path, rp_id)
                        if not tool.make_dir(rp_path, 0):
                            print_error_msg(cn + " 创建作品目录 %s 失败" % rp_path)
                            tool.process_exit()

                    # 获取正片页面内的所有图片地址列表
                    image_url_list = get_image_url_list(cp_id, rp_id)
                    if image_url_list is None:
                        print_error_msg(cn + " 无法访问正片：%s，cp_id：%s" % (rp_id, cp_id))
                        continue

                    if len(image_url_list) == 0 and IS_AUTO_FOLLOW:
                        print_step_msg(cn + " 检测到可能有私密作品且账号不是ta的粉丝，自动关注")
                        if follow(coser_id):
                            # 重新获取下正片页面内的所有图片地址列表
                            image_url_list = get_image_url_list(cp_id, rp_id)

                    if len(image_url_list) == 0:
                        print_error_msg(cn + " 正片：%s没有任何图片，可能是你使用的账号没有关注ta，所以无法访问只对粉丝开放的私密作品，cp_id：%s" % (rp_id, cp_id))
                        continue

                    image_count = 1
                    for image_url in image_url_list:
                        # 禁用指定分辨率
                        image_url = "/".join(image_url.split("/")[0:-1])
                        print_step_msg(cn + " %s 开始下载第%s张图片 %s" % (rp_id, image_count, image_url))

                        if image_url.rfind("/") < image_url.rfind("."):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = "jpg"
                        file_path = os.path.join(rp_path, "%03d.%s" % (image_count, file_type))
                        if tool.save_net_file(image_url, file_path):
                            image_count += 1
                            print_step_msg(cn + " %s 第%s张图片下载成功" % (rp_id, image_count))
                        else:
                            print_error_msg(cn + " %s 第%s张图片 %s 下载失败" % (rp_id, image_count, image_url))

                    this_cn_total_image_count += image_count - 1

                    if 0 < GET_PAGE_COUNT < total_rp_count:
                        is_over = True
                        break
                    else:
                        total_rp_count += 1

                if not is_over:
                    if page_count >= get_max_page_count(coser_id, post_page):
                        is_over = True
                    else:
                        page_count += 1

            print_step_msg(cn + " 下载完毕，总共获得%s张图片" % this_cn_total_image_count)

            # 新的存档记录
            if first_rp_id != "":
                self.account_info[1] = first_rp_id

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += this_cn_total_image_count
            ACCOUNTS.remove(coser_id)
            threadLock.release()

            print_step_msg(cn + " 完成")
        except SystemExit:
            print_error_msg(cn + " 异常退出")
        except Exception, e:
            print_step_msg(cn + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Bcy().main()
