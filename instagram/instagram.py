# -*- coding:utf-8  -*-
'''
Created on 2013-4-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json
import os
import shutil
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


class Instagram(common.Robot):

    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global IS_SORT
        global IS_TRACE
        global IS_SHOW_ERROR
        global IS_SHOW_STEP
        global NEW_USER_ID_LIST_FILE_PATH
        global TRACE_LOG_PATH
        global ERROR_LOG_PATH
        global STEP_LOG_PATH

        super(Instagram, self).__init__()

        # 全局变量
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
        print_step_msg("创建图片根目录：" + self.image_download_path)
        if not common.make_dir(self.image_download_path, 2):
            print_error_msg("创建图片根目录：" + self.image_download_path + " 失败，程序结束！")
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
                if len(user_info) < 2:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "").replace(" ", "").replace("\n", "")
                user_info_list = user_info.split("\t")

                user_account = user_info_list[0]
                user_id_list[user_account] = user_info_list
                # 如果没有数量，则为0
                if len(user_id_list[user_account]) < 2:
                    user_id_list[user_account].append("0")
                if user_id_list[user_account][1] == '':
                    user_id_list[user_account][1] = '0'
                # 处理上一次image id
                if len(user_id_list[user_account]) < 3:
                    user_id_list[user_account].append("")
        else:
            print_error_msg("用户ID存档文件: " + self.user_id_list_file_path + "不存在，程序结束！")
            common.process_exit()

        # 创建临时存档文件
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "w")
        new_user_id_list_file.close()

        TOTAL_IMAGE_COUNT = 0

        # 循环下载每个id
        for user_account in sorted(user_id_list.keys()):
            # 检查正在运行的线程数
            while THREAD_COUNT >= self.thread_count:
                time.sleep(10)

            # 线程数+1
            threadLock.acquire()
            THREAD_COUNT += 1
            threadLock.release()

            thread = Download(user_id_list[user_account])
            thread.start()

        while THREAD_COUNT != 0:
            time.sleep(10)

        # 删除临时文件夹
        common.remove_dir(IMAGE_TEMP_PATH)

        stop_time = time.time()
        print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(TOTAL_IMAGE_COUNT) + "张")


class Download(threading.Thread):

    def __init__(self, user_info):
        threading.Thread.__init__(self)
        self.user_info = user_info

    def run(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global IS_SORT
        global NEW_USER_ID_LIST_FILE_PATH
        global TOTAL_IMAGE_COUNT
        global THREAD_COUNT

        user_account = self.user_info[0]

        print_step_msg(user_account + " 开始")

        # 初始化数据
        last_image_id = self.user_info[2]
        self.user_info[2] = ''
        image_id = ""
        image_count = 1
        is_pass = False
        # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
        if last_image_id != "":
            is_error = True
        else:
            is_error = False

        # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
        if IS_SORT == 1:
            image_path = IMAGE_TEMP_PATH + "\\" + user_account
        else:
            image_path = IMAGE_DOWNLOAD_PATH + "\\" + user_account
        if not common.make_dir(image_path, 1):
            print_error_msg(user_account + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
            common.process_exit()

        # 图片下载
        while 1:
            if image_id == "":
                photo_album_url = "https://instagram.com/%s/media" % user_account
            else:
                photo_album_url = "https://instagram.com/%s/media?max_id=%s" % (user_account, image_id)
            photo_album_data = common.do_get(photo_album_url)
            if not photo_album_data:
                print_error_msg(user_account + " 无法获取相册信息: " + photo_album_url)
                break
            try:
                photo_album_page = json.read(photo_album_data)
            except:
                print_error_msg(user_account + " 相册信息：" + str(photo_album_data) + " 不是一个JSON")
                break
            if not isinstance(photo_album_page, dict):
                print_error_msg(user_account + " JSON数据：" + str(photo_album_page) + " 不是一个字典")
                break
            if not photo_album_page.has_key("items"):
                print_error_msg(user_account + " 在JSON数据：" + str(photo_album_page) + " 中没有找到'items'字段")
                break

            # 下载到了最后一张图了
            if photo_album_page["items"] is []:
                break
            for photo_info in photo_album_page["items"]:
                if not photo_info.has_key("images"):
                    print_error_msg(user_account + " 在JSON数据：" + str(photo_info) + " 中没有找到'images'字段")
                    break
                if not photo_info.has_key("id"):
                    print_error_msg(user_account + " 在JSON数据：" + str(photo_info) + " 中没有找到'id'字段")
                    break
                else:
                    image_id = photo_info["id"]

                # 将第一张image的id保存到新id list中
                if self.user_info[2] == "":
                    self.user_info[2] = image_id

                # 检查是否已下载到前一次的图片
                if image_id == last_image_id:
                    is_pass = True
                    is_error = False
                    break

                if not photo_info["images"].has_key("standard_resolution"):
                    print_error_msg(user_account + " 在JSON数据：" + str(photo_info["images"]) + " 中没有找到'standard_resolution'字段, image id: " + image_id)
                    break
                if not photo_info["images"]["standard_resolution"].has_key("url"):
                    print_error_msg(user_account + " 在JSON数据：" + str(photo_info["images"]["standard_resolution"]) + " 中没有找到'url'字段, image id: " + image_id)
                    break

                image_url = photo_info["images"]["standard_resolution"]["url"]

                # 文件类型
                file_type = image_url.split(".")[-1]
                file_name = image_path + "\\" + str("%04d" % image_count) + "." + file_type

                # 下载
                print_step_msg(user_account + " 开始下载第 " + str(image_count) + "张图片：" + image_url)
                if common.save_image(image_url, file_name):
                    print_step_msg(user_account + " 第" + str(image_count) + "张图片下载成功")
                    image_count += 1
                else:
                    print_error_msg(user_account + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")

                # 达到配置文件中的下载数量，结束
                if last_image_id != '' and GET_IMAGE_COUNT > 0 and image_count > GET_IMAGE_COUNT:
                    is_pass = True
                    break

            if is_pass:
                break

        print_step_msg(user_account + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

        self.user_info[1] = str(int(self.user_info[1]) + image_count - 1)

        # 排序
        if IS_SORT == 1:
            image_list = sorted(os.listdir(image_path), reverse=True)
            # 判断排序目标文件夹是否存在
            if len(image_list) >= 1:
                destination_path = IMAGE_DOWNLOAD_PATH + "\\" + user_account
                if not common.make_dir(destination_path, 1):
                    print_error_msg(user_account + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    common.process_exit()

                # 倒叙排列
                count = int(self.user_info[1]) + 1
                for file_name in image_list:
                    file_type = file_name.split(".")[1]
                    common.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)
                    count += 1
                print_step_msg(user_account + " 图片从下载目录移动到保存目录成功")
            # 删除临时文件夹
            shutil.rmtree(image_path, True)

        if is_error:
            print_error_msg(user_account + " 图片数量异常，请手动检查")

        # 保存最后的信息
        threadLock.acquire()
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "a")
        new_user_id_list_file.write("\t".join(self.user_info) + "\n")
        new_user_id_list_file.close()
        TOTAL_IMAGE_COUNT += image_count - 1
        THREAD_COUNT -= 1
        threadLock.release()

        print_step_msg(user_account + " 完成")

if __name__ == "__main__":
    Instagram().main()
