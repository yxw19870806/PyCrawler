# -*- coding:UTF-8  -*-
'''
Created on 2013-4-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common
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


class GooglePlus(common.Robot):

    def __init__(self):
        global GET_IMAGE_URL_COUNT
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_USER_ID_LIST_FILE_PATH
        global IS_SORT
        global IS_TRACE
        global IS_SHOW_ERROR
        global IS_SHOW_STEP
        global TRACE_LOG_PATH
        global ERROR_LOG_PATH
        global STEP_LOG_PATH

        super(GooglePlus, self).__init__()

        # 全局变量
        GET_IMAGE_URL_COUNT = 100  # 单次获取最新的N张照片,G+ 限制最多1000张
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
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
        if self.is_proxy == 1 or self.is_proxy == 2:
            common.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.user_id_list_file_path):
            user_id_list_file = open(self.user_id_list_file_path, "r")
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            for user_info in all_user_list:
                if len(user_info) < 10:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
                user_info_list = user_info.split("\t")

                user_id = user_info_list[0]
                user_id_list[user_id] = user_info_list
                # 如果没有名字，则名字用uid代替
                if len(user_id_list[user_id]) < 2:
                    user_id_list[user_id].append(user_id)
                if user_id_list[user_id][1] == '':
                    user_id_list[user_id][1] = user_id
                # 如果没有数量，则为0
                if len(user_id_list[user_id]) < 3:
                    user_id_list[user_id].append("0")
                if user_id_list[user_id][2] == '':
                    user_id_list[user_id][2] = '0'
                # 处理上一次image URL
                if len(user_id_list[user_id]) < 4:
                    user_id_list[user_id].append("")
                # 处理成员队伍信息
                if len(user_id_list[user_id]) < 5:
                    user_id_list[user_id].append("")
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

        # 删除临时文件夹
        common.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "r")
        all_user_list = new_user_id_list_file.readlines()
        new_user_id_list_file.close()
        user_id_list = {}
        for user_info in all_user_list:
            if len(user_info) < 5:
                continue
            user_info = user_info.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
            user_info_list = user_info.split("\t")
            user_id_list[user_info_list[0]] = user_info_list
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "w")
        for user_id in sorted(user_id_list.keys()):
            new_user_id_list_file.write("\t".join(user_id_list[user_id]) + "\n")
        new_user_id_list_file.close()

        stop_time = time.time()
        print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(TOTAL_IMAGE_COUNT) + "张")


class Download(threading.Thread):

    def __init__(self, user_info):
        threading.Thread.__init__(self)
        self.user_info = user_info

    def run(self):
        global GET_IMAGE_URL_COUNT
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_USER_ID_LIST_FILE_PATH
        global IS_SORT
        global TOTAL_IMAGE_COUNT
        global THREAD_COUNT

        user_id = self.user_info[0]
        user_name = self.user_info[1]

        print_step_msg(user_name + " 开始")

        try:
            # 初始化数据
            last_message_url = self.user_info[3]
            self.user_info[3] = ''  # 置空，存放此次的最后URL
            # 为防止前一次的记录图片被删除，根据历史图片总数给一个单次下载的数量限制
            # 第一次下载，不用限制
            if last_message_url == '':
                limit_download_count = 0
            else:
                [last_message_page_return_code, ] = common.http_request(last_message_url)
                # 上次记录的信息首页还在，那么不要限制
                if last_message_page_return_code == 1:
                    limit_download_count = 0
                else:
                    # 历史总数的10%，下限50、上限1000
                    limit_download_count = min(max(50, int(self.user_info[2]) / 100 * 10), 1000)
            image_count = 1
            message_url_list = []
            image_url_list = []
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if last_message_url.find("picasaweb.google.com/") != -1:
                is_error = True
            else:
                is_error = False

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = IMAGE_TEMP_PATH + "\\" + user_name
            else:
                image_path = IMAGE_DOWNLOAD_PATH + "\\" + self.user_info[4] + "\\" + user_name
            if not common.make_dir(image_path, 1):
                print_error_msg(user_name + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
                common.process_exit()

            # 图片下载
            photo_album_url = 'https://plus.google.com/_/photos/pc/read/'
            key = ''
            trace(user_name + " 信息首页地址：" + photo_album_url)

            while 1:
                post_data = 'f.req=[["posts",null,null,"synthetic:posts:%s",3,"%s",null],[%s,1,null],"%s",null,null,null,null,null,null,null,2]' % (user_id, user_id, GET_IMAGE_URL_COUNT, key)
                [photo_album_page_return_code, photo_album_page] = common.http_request(photo_album_url, post_data)
                # 换一个获取信息页的方法，这个只能获取最近的100张
                # if not photo_album_page and key == '':
                #     photo_album_url = "https://plus.google.com/photos/%s/albums/posts?banner=pwa" % (user_id)
                #     trace(user_name + " 信息首页地址：" + photo_album_url)
                #     photo_album_page = common.http_request(photo_album_url)

                # 无法获取信息首页
                if photo_album_page_return_code != 1:
                    print_error_msg(user_name + " 无法获取相册首页: " + photo_album_url + ', key = ' + key)
                    break

                # 相册也中全部的信息页
                this_page_message_url_list = re.findall('\[\["(https://picasaweb.google.com/[^"]*)"', photo_album_page)
                for message_url in this_page_message_url_list:
                    # 有可能拿到带authkey的，需要去掉
                    # https://picasaweb.google.com/116300481938868290370/2015092603?authkey\u003dGv1sRgCOGLq-jctf-7Ww#6198800191175756402
                    message_url = message_url.replace('\u003d', '=')
                    try:
                        temp = re.findall('(.*)\?.*(#.*)', message_url)
                        real_message_url = temp[0][0] + temp[0][1]
                    except:
                        real_message_url = message_url
                    # 判断是否重复
                    if real_message_url in message_url_list:
                        continue
                    message_url_list.append(real_message_url)
                    trace("message URL:" + message_url)

                    # 将第一张image的URL保存到新id list中
                    if self.user_info[3] == '':
                        self.user_info[3] = real_message_url

                    # 检查是否已下载到前一次的图片
                    if real_message_url == last_message_url:
                        is_error = False
                        break

                    [message_page_return_code, message_page] = common.http_request(message_url)
                    if message_page_return_code != 1:
                        print_error_msg(user_name + " 无法获取信息页")
                        continue

                    flag = message_page.find("<div><a href=")
                    while flag != -1:
                        image_index = message_page.find("<img src=", flag, flag + 200)
                        if image_index == -1:
                            print_error_msg(user_name + " 信息页：" + message_url + " 中没有找到标签'<img src='")
                            break
                        image_start = message_page.find("http", image_index)
                        image_stop = message_page.find('"', image_start)
                        image_url = message_page[image_start:image_stop]
                        if image_url in image_url_list:
                            flag = message_page.find("<div><a href=", flag + 1)
                            continue
                        image_url_list.append(image_url)
                        trace("image URL:" + image_url)

                        # 重组URL并使用最大分辨率
                        # https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/Ic42/s128/16%252520-%2525201.jpg
                        # ->
                        # https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/s0-Ic42/16%252520-%2525201.jpg
                        temp_list = image_url.split("/")
                        temp_list[-2] = "s0"
                        image_url = "/".join(temp_list[:-3]) + '/s0-' + temp_list[-3] + '/' + temp_list[-1]
                        # 文件类型
                        if image_url.rfind('/') < image_url.rfind('.'):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = 'jpg'
                        file_name = image_path + "\\" + str("%04d" % image_count) + "." + file_type

                        # 下载
                        print_step_msg(user_name + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                        if common.save_image(image_url, file_name):
                            print_step_msg(user_name + " 第" + str(image_count) + "张图片下载成功")
                            image_count += 1
                        else:
                            print_error_msg(user_name + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")

                        # 达到下载数量限制，结束
                        if limit_download_count > 0 and image_count > limit_download_count:
                            is_over = True
                            break

                        # 达到配置文件中的下载数量，结束
                        if GET_IMAGE_COUNT > 0 and image_count > GET_IMAGE_COUNT:
                            is_over = True
                            break

                        flag = message_page.find("<div><a href=", flag + 1)

                # 查找下一页的token key
                finds = re.findall('"([a-zA-Z0-9-]*)"', photo_album_page)
                if len(finds[0]) > 80:
                    key = finds[0]

            print_step_msg(user_name + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1:
                image_list = common.get_dir_files_name(image_path, 'desc')
                # 判断排序目标文件夹是否存在
                if len(image_list) >= 1:
                    destination_path = IMAGE_DOWNLOAD_PATH + "\\" + self.user_info[4] + "\\" + user_name
                    if not common.make_dir(destination_path, 1):
                        print_error_msg(user_name + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                        common.process_exit()
                    # 倒叙排列
                    count = int(self.user_info[2])
                    for file_name in image_list:
                        count += 1
                        file_type = file_name.split(".")[1]
                        common.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)
                    print_step_msg(user_name + " 图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                common.remove_dir(image_path)

            self.user_info[2] = str(int(self.user_info[2]) + image_count - 1)

            if is_error:
                print_error_msg(user_name + " 图片数量异常，请手动检查")

            # 保存最后的信息
            threadLock.acquire()
            new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "a")
            new_user_id_list_file.write("\t".join(self.user_info) + "\n")
            new_user_id_list_file.close()
            TOTAL_IMAGE_COUNT += image_count - 1
            THREAD_COUNT -= 1
            threadLock.release()

            print_step_msg(user_name + " 完成")

        except Exception, e:
            print_step_msg(user_name + " 异常")
            print_error_msg(str(e))


if __name__ == "__main__":
    GooglePlus().main()
