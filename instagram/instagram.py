# -*- coding:utf-8  -*-
'''
Created on 2013-4-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool, json
import os
import threading
import time

USER_IDS = []

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


class Instagram(robot.Robot):

    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        super(Instagram, self).__init__()

        # 全局变量
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global TOTAL_IMAGE_COUNT
        global USER_IDS

        start_time = time.time()

        # 图片保存目录
        print_step_msg("创建图片根目录：" + self.image_download_path)
        if not tool.make_dir(self.image_download_path, 0):
            print_error_msg("创建图片根目录：" + self.image_download_path + " 失败，程序结束！")
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.save_data_path):
            user_id_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "", ""])
            USER_IDS = user_id_list.keys()
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
                if tool.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if tool.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(user_id_list[user_account])
            thread.start()

            time.sleep(1)

        # 检查除主线程外的其他所有线程是不是全部结束了
        while threading.activeCount() > main_thread_count:
            time.sleep(10)

        # 未完成的数据保存
        if len(USER_IDS) > 0:
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            for user_id in USER_IDS:
                new_save_data_file.write("\t".join(user_id_list[user_id]) + "\n")
            new_save_data_file.close()

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "r")
        all_user_list = new_save_data_file.readlines()
        new_save_data_file.close()
        user_id_list = {}
        for user_info in all_user_list:
            if len(user_info) < 2:
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
        global IS_SORT
        global TOTAL_IMAGE_COUNT
        global USER_IDS

        user_account = self.user_info[0]

        print_step_msg(user_account + " 开始")

        # 初始化数据
        last_created_time = self.user_info[2]
        self.user_info[2] = ""
        # 为防止前一次的记录图片被删除，根据历史图片总数给一个单次下载的数量限制
        if last_created_time == "0":
            limit_download_count = 0
        else:
            # 历史总数的10%，下线50、上限300
            limit_download_count = min(max(50, int(self.user_info[1]) / 100 * 10), 300)
        image_id = ""
        image_count = 1
        is_over = False
        # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
        if last_created_time != "0":
            is_error = True
        else:
            is_error = False
        need_make_download_dir = True

        # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
        if IS_SORT == 1:
            image_path = IMAGE_TEMP_PATH + "\\" + user_account
        else:
            image_path = IMAGE_DOWNLOAD_PATH + "\\" + user_account

        # 图片下载
        while 1:
            if image_id == "":
                photo_album_url = "https://instagram.com/%s/media" % user_account
            else:
                photo_album_url = "https://instagram.com/%s/media?max_id=%s" % (user_account, image_id)

            [photo_album_return_code, photo_album_data] = tool.http_request(photo_album_url)[:2]
            if photo_album_return_code != 1:
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
            if photo_album_page["items"] == []:
                is_over = True
            else:
                for photo_info in photo_album_page["items"]:
                    if not photo_info.has_key("images"):
                        print_error_msg(user_account + " 在JSON数据：" + str(photo_info) + " 中没有找到'images'字段")
                        break
                    if not photo_info.has_key("created_time"):
                        print_error_msg(user_account + " 在JSON数据：" + str(photo_info) + " 中没有找到'created_time'字段")
                        break
                    if not photo_info.has_key("id"):
                        print_error_msg(user_account + " 在JSON数据：" + str(photo_info) + " 中没有找到'id'字段")
                        break
                    else:
                        image_id = photo_info["id"]

                    # 将第一张image的created_time保存到新id list中
                    if self.user_info[2] == "":
                        self.user_info[2] = photo_info["created_time"]

                    # 检查是否已下载到前一次的图片
                    if int(photo_info["created_time"]) <= last_created_time:
                        is_over = True
                        is_error = False
                        break

                    if not photo_info["images"].has_key("standard_resolution"):
                        print_error_msg(user_account + " 在JSON数据：" + str(photo_info["images"]) + " 中没有找到'standard_resolution'字段, image id: " + image_id)
                        break
                    if not photo_info["images"]["standard_resolution"].has_key("url"):
                        print_error_msg(user_account + " 在JSON数据：" + str(photo_info["images"]["standard_resolution"]) + " 中没有找到'url'字段, image id: " + image_id)
                        break

                    image_url = photo_info["images"]["standard_resolution"]["url"]
                    image_url = image_url.split("?")[0]

                    # 文件类型
                    file_type = image_url.split(".")[-1]
                    file_path = image_path + "\\" + str("%04d" % image_count) + "." + file_type

                    # 下载
                    print_step_msg(user_account + " 开始下载第 " + str(image_count) + "张图片：" + image_url)
                    # 第一张图片，创建目录
                    if need_make_download_dir:
                        if not tool.make_dir(image_path, 0):
                            print_error_msg(user_account + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
                            tool.process_exit()
                    if tool.save_image(image_url, file_path):
                        print_step_msg(user_account + " 第" + str(image_count) + "张图片下载成功")
                        image_count += 1
                    else:
                        print_error_msg(user_account + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")

                    # 达到下载数量限制，结束
                    if limit_download_count > 0 and image_count > limit_download_count:
                        is_over = True
                        break

                    # 达到配置文件中的下载数量，结束
                    if GET_IMAGE_COUNT > 0 and image_count > GET_IMAGE_COUNT:
                        is_over = True
                        is_error = False
                        break

            if is_over:
                break

        print_step_msg(user_account + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

        # 排序
        if IS_SORT == 1 and image_count > 1:
            image_list = sorted(os.listdir(image_path), reverse=True)
            # 判断排序目标文件夹是否存在
            if len(image_list) >= 1:
                destination_path = IMAGE_DOWNLOAD_PATH + "\\" + user_account
                if not tool.make_dir(destination_path, 0):
                    print_error_msg(user_account + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    tool.process_exit()

                # 倒叙排列
                count = int(self.user_info[1])
                for file_name in image_list:
                    count += 1
                    file_type = file_name.split(".")[1]
                    tool.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)

                print_step_msg(user_account + " 图片从下载目录移动到保存目录成功")

            # 删除临时文件夹
            tool.remove_dir(image_path)

        self.user_info[1] = str(int(self.user_info[1]) + image_count - 1)

        if is_error:
            print_error_msg(user_account + " 图片数量异常，请手动检查")

        # 保存最后的信息
        threadLock.acquire()
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
        new_save_data_file.write("\t".join(self.user_info) + "\n")
        new_save_data_file.close()
        TOTAL_IMAGE_COUNT += image_count - 1
        USER_IDS.remove(user_account)
        threadLock.release()

        print_step_msg(user_account + " 完成")


if __name__ == "__main__":
    Instagram().main()
