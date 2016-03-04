# -*- coding:UTF-8  -*-
'''
Created on 2014-5-31

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import robot, tool, json
import os
import re
import threading
import time

IS_TRACE = False
IS_SHOW_ERROR = False
IS_SHOW_STEP = False
TRACE_LOG_PATH = ""
ERROR_LOG_PATH = ""
STEP_LOG_PATH = ""
INIT_MAX_ID = 999999999999999999

threadLock = threading.Lock()


def trace(msg):
    threadLock.acquire()
    tool.trace(msg, IS_TRACE, TRACE_LOG_PATH)
    threadLock.release()


def print_error_msg(msg):
    threadLock.acquire()
    tool.print_error_msg(msg, IS_SHOW_ERROR, ERROR_LOG_PATH)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    tool.print_step_msg(msg, IS_SHOW_STEP, STEP_LOG_PATH)
    threadLock.release()


# 返回的是当前时区对应的时间
def get_image_last_modified(info):
    last_modified_time = tool.get_response_info(info, "last-modified")
    last_modified_time = time.strptime(last_modified_time, "%a, %d %b %Y %H:%M:%S %Z")
    return int(time.mktime(last_modified_time)) - time.timezone


def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


class Twitter(robot.Robot):

    def __init__(self, save_data_path="", this_image_download_path="", this_image_temp_path=""):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_TRACE
        global IS_SHOW_ERROR
        global IS_SHOW_STEP
        global TRACE_LOG_PATH
        global ERROR_LOG_PATH
        global STEP_LOG_PATH

        # multiprocessing.Process.__init__(self)
        robot.Robot.__init__(self)

        if save_data_path != "":
            self.save_data_path = save_data_path

        GET_IMAGE_COUNT = self.get_image_count
        if this_image_temp_path != "":
            IMAGE_TEMP_PATH = this_image_temp_path
        else:
            IMAGE_TEMP_PATH = self.image_temp_path
        if this_image_download_path != "":
            IMAGE_DOWNLOAD_PATH = this_image_download_path
        else:
            IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        IS_TRACE = self.is_trace
        IS_SHOW_ERROR = self.is_show_error
        IS_SHOW_STEP = self.is_show_step
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)
        TRACE_LOG_PATH = self.trace_log_path
        ERROR_LOG_PATH = self.error_log_path
        STEP_LOG_PATH = self.step_log_path

        tool.print_msg("配置文件读取完成")

    def main(self):
        global TOTAL_IMAGE_COUNT

        start_time = time.time()

        # 图片保存目录
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 2):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败，程序结束！")
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.save_data_path):
            save_data_file = open(self.save_data_path, "r")
            all_user_list = save_data_file.readlines()
            save_data_file.close()
            for user_info in all_user_list:
                if len(user_info) < 3:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "").replace(" ", "").replace("\n", "").replace("\r", "")
                user_info_list = user_info.split("\t")

                user_account = user_info_list[0]
                user_id_list[user_account] = user_info_list
                # 如果没有数量，则为0
                if len(user_id_list[user_account]) < 2:
                    user_id_list[user_account].append("0")
                if user_id_list[user_account][1] == "":
                    user_id_list[user_account][1] = "0"
                # 处理上一次图片的上传时间
                if len(user_id_list[user_account]) < 3:
                    user_id_list[user_account].append("")
                if user_id_list[user_account][2] == "":
                    user_id_list[user_account][2] = "0"

        else:
            print_error_msg("用户ID存档文件: " + self.save_data_path + "不存在，程序结束！")
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        TOTAL_IMAGE_COUNT = 0

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for user_account in sorted(user_id_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                time.sleep(10)

            # 开始下载
            thread = Download(user_id_list[user_account])
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "r")
        all_user_list = new_save_data_file.readlines()
        new_save_data_file.close()
        user_id_list = {}
        for user_info in all_user_list:
            if len(user_info) < 5:
                continue
            user_info = user_info.replace("\xef\xbb\xbf", "").replace("\n", "").replace("\r", "")
            user_info_list = user_info.split("\t")
            user_id_list[user_info_list[0]] = user_info_list
        new_save_data_file = open(self.save_data_path, "w")
        for user_id in sorted(user_id_list.keys()):
            new_save_data_file.write("\t".join(user_id_list[user_id]) + "\n")
        new_save_data_file.close()
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时" + str(duration_time) + "秒，共计图片" + str(TOTAL_IMAGE_COUNT) + "张")


class Download(threading.Thread):

    def __init__(self, user_info):
        threading.Thread.__init__(self)
        self.user_info = user_info

    def run(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global TOTAL_IMAGE_COUNT

        user_account = self.user_info[0]

        try:
            print_step_msg(user_account + " 开始")

            # 初始化数据
            last_image_time = self.user_info[2]
            self.user_info[2] = "0"  # 置空，存放此次的最后图片上传时间
            data_tweet_id = INIT_MAX_ID
            image_count = 1
            image_url_list = []
            is_over = False
            # 如果有存档记录，则直到找到在记录之前的图片，否则都算错误
            if last_image_time == "0":
                is_error = False
            else:
                is_error = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = os.path.join(IMAGE_TEMP_PATH, user_account)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_account)
            if not tool.make_dir(image_path, 1):
                print_error_msg(user_account + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
                tool.process_exit()

            # 图片下载
            while 1:
                photo_page_url = "https://twitter.com/i/profiles/show/%s/media_timeline?include_available_features=1&include_entities=1&max_position=%s" % (user_account, data_tweet_id)
                [photo_page_return_code, photo_page_data] = tool.http_request(photo_page_url)[:2]
                if photo_page_return_code != 1:
                    print_error_msg(user_account + " 无法获取相册信息: " + photo_page_url)
                    break
                try:
                    page = json.read(photo_page_data)
                except:
                    print_error_msg(user_account + " 返回信息：" + str(photo_page_data) + " 不是一个JSON数据")
                    break

                if not isinstance(page, dict):
                    print_error_msg(user_account + " JSON数据：" + str(page) + " 不是一个字典")
                    break
                if "has_more_items" not in page:
                    print_error_msg(user_account + " 在JSON数据：" + str(page) + " 中没有找到'has_more_items'字段")
                    break
                if "items_html" not in page:
                    print_error_msg(user_account + " 在JSON数据：" + str(page) + " 中没有找到'items_html'字段")
                    break
                if "min_position" not in page:
                    print_error_msg(user_account + " 在JSON数据：" + str(page) + " 中没有找到'min_position'字段")
                    break

                # 正则表达，匹配data-image-url="XXX"
                urls = re.findall('data-image-url="([^"]*)"', page["items_html"])
                for image_url in urls:
                    image_url = str(image_url)
                    image_url_list.append(image_url)
                    trace(user_account + " image URL:" + image_url)

                    [image_response_return_code, image_response_data, image_response_info] = tool.http_request(image_url)
                    # 404，不算做错误，图片已经被删掉了
                    if image_response_return_code == -1:
                        pass
                    elif image_response_return_code == 1:
                        image_time = get_image_last_modified(image_response_info)
                        # 将第一张image的URL保存到新id list中
                        if self.user_info[2] == "0":
                            self.user_info[2] = str(image_time)

                        # 检查是否已下载到前一次的图片
                        if 0 < int(last_image_time) >= image_time:
                            is_over = True
                            is_error = False
                            break

                        # 文件类型
                        file_type = image_url.split(".")[-1].split(":")[0]
                        file_path = os.path.join(image_path, str("%04d" % image_count) + "." + file_type)

                        print_step_msg(user_account + " 开始下载第 " + str(image_count) + "张图片：" + image_url)
                        save_image(image_response_data, file_path)
                        print_step_msg(user_account + " 第" + str(image_count) + "张图片下载成功")
                        image_count += 1
                    else:
                        print_error_msg(user_account + " 第" + str(image_count) + "张图片 " + image_url + " 获取失败")

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        is_error = False
                        break

                if is_over:
                    break

                if page["has_more_items"] and "min_position" in page:
                    # 设置最后一张的data-tweet-id
                    data_tweet_id = page["min_position"]
                else:
                    break

            # 如果有错误且没有发现新的图片，复原旧数据
            if self.user_info[2] == "0" and last_image_time != "0":
                self.user_info[2] = last_image_time

            print_step_msg(user_account + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_account)
                if robot.sort_file(image_path, destination_path, int(self.user_info[1]), 4):
                    print_step_msg(user_account + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(user_account + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    tool.process_exit()

            self.user_info[1] = str(int(self.user_info[1]) + image_count - 1)

            if is_error:
                print_error_msg(user_account + " 图片数量异常，请手动检查")

            # 保存最后的信息
            threadLock.acquire()
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            new_save_data_file.write("\t".join(self.user_info) + "\n")
            new_save_data_file.close()
            TOTAL_IMAGE_COUNT += image_count - 1
            threadLock.release()

            print_step_msg(user_account + " 完成")
        except Exception, e:
            print_step_msg(user_account + " 异常")
            print_error_msg(str(e))


if __name__ == "__main__":
    Twitter().main()
