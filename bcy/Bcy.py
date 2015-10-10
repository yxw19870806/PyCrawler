# -*- coding:UTF-8  -*-
'''
Created on 2015-6-23

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json
import os
import re
import threading
import time

IS_TRACE = False
IS_SHOW_ERROR = False
IS_SHOW_STEP = False
TRACE_LOG_PATH = ''
ERROR_LOG_PATH = ''
STEP_LOG_PATH = ''
THREAD_COUNT = 0

threadLock = threading.Lock()


def trace(msg):
    threadLock.acquire()
    common.trace(msg, IS_TRACE, TRACE_LOG_PATH)
    threadLock.release()


def print_error_msg(msg):
    threadLock.acquire()
    common.print_error_msg(msg, IS_SHOW_ERROR, ERROR_LOG_PATH)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    common.print_step_msg(msg, IS_SHOW_STEP, STEP_LOG_PATH)
    threadLock.release()


class Bcy(common.Robot):

    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_DOWNLOAD_PATH
        global IS_SORT
        global IS_TRACE
        global IS_SHOW_ERROR
        global IS_SHOW_STEP
        global NEW_USER_ID_LIST_FILE_PATH
        global TRACE_LOG_PATH
        global ERROR_LOG_PATH
        global STEP_LOG_PATH

        super(Bcy, self).__init__()

        # 全局变量
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_TRACE = self.is_trace
        IS_SHOW_ERROR = self.is_show_error
        IS_SHOW_STEP = self.is_show_step
        NEW_USER_ID_LIST_FILE_PATH = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        TRACE_LOG_PATH = self.trace_log_path
        ERROR_LOG_PATH = self.error_log_path
        STEP_LOG_PATH = self.step_log_path

        common.print_msg("配置文件读取完成")

    def main(self):
        global TOTAL_IMAGE_COUNT
        global THREAD_COUNT

        start_time = time.time()

        # 图片保存目录
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not common.make_dir(IMAGE_DOWNLOAD_PATH, 2):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败，程序结束！")
            common.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            common.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not common.set_cookie(self.cookie_path, self.browser_version):
            print_error_msg("导入浏览器cookies失败，程序结束！")
            common.process_exit()

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.user_id_list_file_path):
            user_id_list_file = open(self.user_id_list_file_path, "r")
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            for user_info in all_user_list:
                if len(user_info) < 3:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "").replace(" ", "").replace("\n", "").replace("\r", "")
                user_info_list = user_info.split("\t")

                user_id = user_info_list[0]
                user_id_list[user_id] = user_info_list
                # 如果没有数量，则为0
                if len(user_id_list[user_id]) < 2:
                    user_id_list[user_id].append("0")
                if user_id_list[user_id][1] == '':
                    user_id_list[user_id][1] = '0'
                # 处理上一次rp id
                if len(user_id_list[user_id]) < 3:
                    user_id_list[user_id].append("")
                if user_id_list[user_id][2] == '':
                    user_id_list[user_id][2] = '0'
        else:
            print_error_msg("用户ID存档文件: " + self.user_id_list_file_path + "不存在，程序结束！")
            common.process_exit()

        # 创建临时存档文件
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "w")
        new_user_id_list_file.close()

        TOTAL_IMAGE_COUNT = 0
        # 循环下载每个id
        for user_id in sorted(user_id_list.keys()):
            # 检查正在运行的线程数
            while THREAD_COUNT >= self.thread_count:
                time.sleep(10)

            # 线程数+1
            threadLock.acquire()
            THREAD_COUNT += 1
            threadLock.release()

            # 开始下载
            thread = Download(user_id_list[user_id])
            thread.start()

        # 检查所有线程是不是全部结束了
        while THREAD_COUNT != 0:
            time.sleep(10)

        stop_time = time.time()
        print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(total_image_count) + "张")


class Download(threading.Thread):

    def __init__(self, user_info):
        threading.Thread.__init__(self)
        self.user_info = user_info

    def run(self):
        global GET_IMAGE_COUNT
        global IMAGE_DOWNLOAD_PATH
        global IS_SORT
        global NEW_USER_ID_LIST_FILE_PATH
        global TOTAL_IMAGE_COUNT
        global THREAD_COUNT

        cn = self.user_info[1]

        print_step_msg(cn + " 开始")

        last_rp_id = self.user_info[2]
        self.user_info[2] = ''  # 置空，存放此次的最后rp id
        cp_id = int(self.user_info[0]) - 100876  # 网页规则，没有为什么
        page_count = 1
        max_page_count = -1
        need_make_download_dir = True  # 是否需要创建cn目录
        # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
        if last_rp_id != '0':
            is_error = True
        else:
            is_error = False
        is_pass = False

        this_cn_total_image_count = 0

        while 1:
            photo_album_url = 'http://bcy.net/coser/ajaxShowMore?type=all&cp_id=%s&p=%s' % (cp_id, page_count)
            photo_album_page = common.do_get(photo_album_url)
            if not photo_album_page:
                print_error_msg(cn + " 无法获取数据: " + photo_album_url)
                break
            try:
                photo_album_page = json.read(photo_album_page)
            except:
                print_error_msg(cn + " 返回信息不是一个JSON数据")
                break

            # 总共多少页
            if max_page_count == -1:
                try:
                    max_page_data = photo_album_page['data']['page']
                except:
                    print_error_msg(cn + " 在JSON数据：" + str(photo_album_page) + " 中没有找到'page'字段")
                    break
                if not max_page_data:
                    max_page_count = 1
                else:
                    page_list = re.findall(u'<a href=\\"\\/coser\\/ajaxShowMore\?type=all&cp_id=' + str(cp_id) + '&p=(\d)', max_page_data)
                    max_page_count = int(max(page_list))

            try:
                photo_album_page_data = photo_album_page['data']['data']
            except:
                print_error_msg(cn + " 在JSON数据：" + str(photo_album_page) + " 中没有找到'data'字段")
                break

            for data in photo_album_page_data:
                try:
                    rp_id = data['rp_id']
                    title = data['title'].encode('utf-8').strip()
                    # 过滤一些无法作为文件夹路径的符号
                    filter_list = [':', '\\', '/', '.', '*', '?', '"', '<', '>', '|']
                    for filter_char in filter_list:
                        title = title.replace(filter_char, '')
                except:
                    print_error_msg(cn + " 在JSON数据：" + str(data) + " 中没有找到'ur_id'或'title'字段")
                    break

                if self.user_info[2] == '':
                    self.user_info[2] = rp_id
                # 检查是否已下载到前一次的图片
                if int(rp_id) <= int(last_rp_id):
                    is_error = False
                    is_pass = True
                    break

                print_step_msg("rp: " + rp_id)

                # CN目录
                image_path = IMAGE_DOWNLOAD_PATH + "\\" + cn

                if need_make_download_dir:
                    if not common.make_dir(image_path, 1):
                        print_error_msg(cn + " 创建CN目录： " + image_path + " 失败，程序结束！")
                        common.process_exit()
                    need_make_download_dir = False

                # 正片目录
                if title != '':
                    rp_path = image_path + "\\" + rp_id + ' ' + title
                else:
                    rp_path = image_path + "\\" + rp_id
                if not common.make_dir(rp_path, 1):
                    # 目录出错，把title去掉后再试一次，如果还不行退出
                    print_error_msg(cn + " 创建正片目录： " + rp_path + " 失败，尝试不使用title！")
                    rp_path = image_path + "\\" + rp_id
                    if not common.make_dir(rp_path, 1):
                        print_error_msg(cn + " 创建正片目录： " + rp_path + " 失败，程序结束！")
                        common.process_exit()

                rp_url = 'http://bcy.net/coser/detail/%s/%s' % (cp_id, rp_id)
                rp_page = common.do_get(rp_url)
                if rp_page:
                    image_count = 0
                    image_index = rp_page.find("src='")
                    while image_index != -1:
                        image_start = rp_page.find("http", image_index)
                        image_stop = rp_page.find("'", image_start)
                        image_url = rp_page[image_start:image_stop]
                        # 禁用指定分辨率
                        image_url = "/".join(image_url.split("/")[0:-1])
                        image_count += 1
                        print_step_msg(cn + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                        if image_url.rfind('/') < image_url.rfind('.'):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = 'jpg'
                        if common.save_image(image_url, rp_path + "\\" + str("%03d" % image_count) + "." + file_type):
                            print_step_msg(cn + " 第" + str(image_count) + "张图片下载成功")
                        else:
                            print_error_msg(cn + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")
                        image_index = rp_page.find("src='", image_index + 1)
                    if image_count == 0:
                        print_error_msg(cn + " " + rp_id + " 没有任何图片")
                    this_cn_total_image_count += image_count - 1
            if is_pass:
                break
            if page_count >= max_page_count:
                break
            page_count += 1

        print_step_msg(cn + " 下载完毕")

        if is_error:
            print_error_msg(cn + " 图片数量异常，请手动检查")

        # 保存最后的信息
        threadLock.acquire()
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "a")
        new_user_id_list_file.write("\t".join(self.user_info) + "\n")
        new_user_id_list_file.close()
        TOTAL_IMAGE_COUNT += this_cn_total_image_count
        THREAD_COUNT -= 1
        threadLock.release()

if __name__ == "__main__":
    Bcy().main()
