# -*- coding:UTF-8  -*-
'''
Created on 2015-6-23

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool
import cookielib
import os
import re
import threading
import time
import traceback

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
IMAGE_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_DOWNLOAD_IMAGE = 1

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


def login(email, password):
    cookie = cookielib.CookieJar()
    login_url = "http://bcy.net/public/dologin"
    login_post = {"email": email, "password": password}
    login_return_code = tool.http_request(login_url, login_post, cookie)[0]
    if login_return_code == 1:
        return True
    else:
        return False


def follow(account_id):
    follow_url = "http://bcy.net/weibo/Operate/follow?"
    follow_post_data = {"uid": account_id, "type": "dofollow"}
    follow_return_code, follow_return_data = tool.http_request(follow_url, follow_post_data)[:2]
    if follow_return_code == 1:
        # 0 未登录，11 关注成功，12 已关注
        if int(follow_return_data) == 12:
            return True
    return False


def unfollow(account_id):
    unfollow_url = "http://bcy.net/weibo/Operate/follow?"
    unfollow_post_data = {"uid": account_id, "type": "unfollow"}
    unfollow_return_code, unfollow_return_data = tool.http_request(unfollow_url, unfollow_post_data)[:2]
    print unfollow_return_code
    if unfollow_return_code == 1:
        if int(unfollow_return_data) == 1:
            return True
    return False


class Bcy(robot.Robot):
    def __init__(self):
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_DOWNLOAD_IMAGE

        super(Bcy, self).__init__()

        # 全局变量
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        IS_DOWNLOAD_IMAGE = self.is_download_image

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        if IS_DOWNLOAD_IMAGE == 0:
            print_error_msg("下载图片没开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 图片保存目录
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败，程序结束！")
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not tool.set_cookie(self.cookie_path, self.browser_version, "bcy.net"):
            print_error_msg("导入浏览器cookies失败，程序结束！")
            tool.process_exit()

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

        # 寻找idlist，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  last_rp_id
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0"])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("用户ID存档文件: " + self.save_data_path + "不存在，程序结束！")
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

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
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时" + str(duration_time) + "秒，共计图片" + str(TOTAL_IMAGE_COUNT) + "张")


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

            last_rp_id = self.account_info[1]
            self.account_info[1] = ""  # 置空，存放此次的最后rp id
            this_cn_total_image_count = 0
            page_count = 1
            max_page_count = -1
            need_make_download_dir = True  # 是否需要创建cn目录
            rp_id_list = []
            is_over = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if last_rp_id != "0":
                is_error = True
            else:
                is_error = False

            while True:
                post_url = "http://bcy.net/u/%s/post/cos?&p=%s" % (coser_id, page_count)
                [post_page_return_code, post_page_response] = tool.http_request(post_url)[:2]
                if post_page_return_code != 1:
                    print_error_msg(cn + " 无法获取数据: " + post_url)
                    break

                page_rp_id_list = re.findall('/coser/detail/(\d+)/(\d+)"', post_page_response)
                page_title_list = re.findall('<img src="\S*" alt="([\S ]*)" />', post_page_response)
                if "${post.title}" in page_title_list:
                    page_title_list.remove("${post.title}")
                if len(page_rp_id_list) != len(page_title_list):
                    print_error_msg(cn + " 第" + str(page_count) + "页获取的rp_id和title数量不符")
                    break

                title_index = 0
                for data in page_rp_id_list:
                    cp_id = data[0]
                    rp_id = data[1]
                    rp_id_list.append(rp_id)

                    if self.account_info[1] == "":
                        self.account_info[1] = rp_id
                    # 检查是否已下载到前一次的图片
                    if int(rp_id) <= int(last_rp_id):
                        is_over = True
                        is_error = False
                        break

                    print_step_msg("rp: " + rp_id)

                    # CN目录
                    image_path = os.path.join(IMAGE_DOWNLOAD_PATH, cn)

                    if need_make_download_dir:
                        if not tool.make_dir(image_path, 0):
                            print_error_msg(cn + " 创建CN目录： " + image_path + " 失败，程序结束！")
                            tool.process_exit()
                        need_make_download_dir = False

                    # 正片目录
                    title = page_title_list[title_index]
                    # 过滤一些windows文件名屏蔽的字符
                    for filter_char in ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]:
                        title = title.replace(filter_char, " ")
                    # 去除前后空格
                    title = title.strip()
                    if title != "":
                        rp_path = os.path.join(image_path, rp_id + " " + title)
                    else:
                        rp_path = os.path.join(image_path, rp_id)
                    if not tool.make_dir(rp_path, 0):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        print_error_msg(cn + " 创建正片目录： " + rp_path + " 失败，尝试不使用title！")
                        rp_path = os.path.join(image_path, rp_id)
                        if not tool.make_dir(rp_path, 0):
                            print_error_msg(cn + " 创建正片目录： " + rp_path + " 失败，程序结束！")
                            tool.process_exit()

                    rp_url = "http://bcy.net/coser/detail/%s/%s" % (cp_id, rp_id)
                    [rp_page_return_code, rp_page_response] = tool.http_request(rp_url)[:2]
                    if rp_page_return_code != 1:
                        print_error_msg(cn + " 无法获取正片页面： " + rp_url)
                        continue

                    image_url_list = re.findall("src='([^']*)'", rp_page_response)
                    if len(image_url_list) == 0:
                        print_step_msg(cn + " 检测到可能有私密作品且账号不是ta的粉丝，自动关注")
                        if follow(coser_id):
                            # 重新获取下详细页面
                            rp_url = "http://bcy.net/coser/detail/%s/%s" % (cp_id, rp_id)
                            [rp_page_return_code, rp_page_response] = tool.http_request(rp_url)[:2]
                            if rp_page_return_code == 1:
                                image_url_list = re.findall("src='([^']*)'", rp_page_response)

                    if len(image_url_list) == 0:
                        print_error_msg(cn + " " + rp_id + " 没有任何图片，可能是你使用的账号没有关注ta，所以无法访问只对粉丝开放的私密作品")
                        continue

                    image_count = 1
                    for image_url in image_url_list:
                        # 禁用指定分辨率
                        image_url = "/".join(image_url.split("/")[0:-1])

                        if image_url.rfind("/") < image_url.rfind("."):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = "jpg"
                        file_path = os.path.join(rp_path, str("%03d" % image_count) + "." + file_type)

                        print_step_msg(cn + ":" + rp_id + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                        if tool.save_image(image_url, file_path):
                            image_count += 1
                            print_step_msg(cn + " " + rp_id + " 第" + str(image_count) + "张图片下载成功")
                        else:
                            print_error_msg(cn + " " + rp_id + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")

                    this_cn_total_image_count += image_count - 1

                    title_index += 1

                if is_over:
                    break

                # 看看总共有几页
                if max_page_count == -1:
                    max_page_count_result = re.findall(r'<a href="/u/' + coser_id + '/post/cos\?&p=(\d*)">尾页</a>', post_page_response)
                    if len(max_page_count_result) > 0:
                        max_page_count = int(max_page_count_result[0])
                    else:
                        max_page_count = 1

                if page_count >= max_page_count:
                    break

                page_count += 1

            # 如果有错误且没有发现新的图片，复原旧数据
            if self.account_info[1] == "" and last_rp_id != "0":
                self.account_info[1] = str(last_rp_id)

            print_step_msg(cn + " 下载完毕，总共获得" + str(this_cn_total_image_count) + "张图片")

            if is_error:
                print_error_msg(cn + " 图片数量异常，请手动检查")

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += this_cn_total_image_count
            ACCOUNTS.remove(coser_id)
            threadLock.release()

            print_step_msg(cn + " 完成")
        except Exception, e:
            print_step_msg(cn + " 异常")
            print_error_msg(str(e) + "\n" + str(traceback.print_exc()))


if __name__ == "__main__":
    tool.restore_process_status()
    Bcy().main()
