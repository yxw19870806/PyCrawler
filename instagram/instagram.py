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
import re
import threading
import time
import traceback

USER_IDS = []
INIT_CURSOR = "9999999999999999999"

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
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        super(Instagram, self).__init__()

        # 全局变量
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global TOTAL_IMAGE_COUNT
        global USER_IDS

        start_time = time.time()

        # 图片保存目录
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败，程序结束！")
            tool.process_exit()

        # 视频保存目录
        print_step_msg("创建视频根目录：" + VIDEO_DOWNLOAD_PATH)
        if not tool.make_dir(VIDEO_DOWNLOAD_PATH, 0):
            print_error_msg("创建视频根目录：" + VIDEO_DOWNLOAD_PATH + " 失败，程序结束！")
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.save_data_path):
            user_id_list = robot.read_save_data(self.save_data_path, 0, ["", "", "0", "0", ""])
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
        user_id_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [user_id_list[key] for key in sorted(user_id_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
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
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global TOTAL_IMAGE_COUNT
        global USER_IDS

        user_account = self.user_info[0]
        user_id = self.user_info[1]

        try:
            print_step_msg(user_account + " 开始")

            # 初始化数据
            last_created_time = int(self.user_info[3])
            self.user_info[3] = "0"
            cursor = INIT_CURSOR
            image_count = 1
            is_over = False
            need_make_download_dir = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = IMAGE_TEMP_PATH + "\\" + user_account
            else:
                image_path = IMAGE_DOWNLOAD_PATH + "\\" + user_account

            # 图片下载
            while True:
                media_page_url = "https://www.instagram.com/query/"
                media_page_url += "?q=ig_user(%s){media.after(%s,12){nodes{code,date,display_src,is_video},page_info}}" % (user_id, cursor)

                [photo_page_return_code, media_page_response] = tool.http_request(media_page_url)[:2]
                if photo_page_return_code != 1:
                    print_error_msg(user_account + " 无法获取媒体信息: " + media_page_url)
                    break
                try:
                    media_page = json.read(media_page_response)
                except:
                    print_error_msg(user_account + " 媒体信息：" + str(media_page_response) + " 不是一个JSON")
                    break
                if "media" not in media_page:
                    print_error_msg(user_account + " 在JSON数据：" + str(media_page) + " 中没有找到'media'字段")
                    break

                media_data = media_page["media"]
                if "page_info" not in media_data:
                    print_error_msg(user_account + " 在media中：" + str(media_data) + " 中没有找到'page_info'字段")
                    break
                if "has_next_page" not in media_data["page_info"]:
                    print_error_msg(user_account + " 在page_info中：" + str(media_data["page_info"]) +
                                    " 中没有找到'has_next_page'字段")
                    break
                if "end_cursor" not in media_data["page_info"]:
                    print_error_msg(user_account + " 在page_info中：" + str(media_data["page_info"]) +
                                    " 中没有找到'end_cursor'字段")
                    break
                if "nodes" not in media_data:
                    print_error_msg(user_account + " 在media中：" + str(media_data) + " 中没有找到'nodes'字段")
                    break

                nodes_data = media_data["nodes"]
                for photo_info in nodes_data:
                    if "is_video" not in photo_info:
                        print_error_msg(user_account + " 在node中：" + str(nodes_data) + " 中没有找到'is_video'字段")
                        break
                    if photo_info["is_video"]:
                        if "code" not in photo_info:
                            print_error_msg(user_account + " 在node中：" + str(nodes_data) + " 中没有找到'code'字段")
                            break
                    if "display_src" not in photo_info:
                        print_error_msg(user_account + " 在node中：" + str(nodes_data) + " 中没有找到'display_src'字段")
                        break
                    if "date" not in photo_info:
                        print_error_msg(user_account + " 在node中：" + str(nodes_data) + " 中没有找到'date'字段")
                        break

                    # 将第一张image的created_time保存到新id list中
                    if self.user_info[3] == "0":
                        self.user_info[3] = str(int(photo_info["date"]))

                    # 检查是否已下载到前一次的图片
                    if 0 < last_created_time >= int(photo_info["date"]):
                        is_over = True
                        break

                    image_url = str(photo_info["display_src"].split("?")[0])

                    # 文件类型
                    file_type = image_url.split(".")[-1]
                    file_path = image_path + "\\" + str("%04d" % image_count) + "." + file_type

                    # 下载
                    # 图片
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

                    # 视频
                    if photo_info["is_video"]:
                        post_page_url = "https://www.instagram.com/p/%s/" % photo_info["code"]
                        [post_page_return_code, post_page_response] = tool.http_request(post_page_url)[:2]
                        if post_page_return_code == 1:
                            meta_list = re.findall('<meta property="([^"]*)" content="([^"]*)" />', post_page_response)
                            find_video = False
                            for meta_property, meta_content in meta_list:
                                if meta_property == "og:video:secure_url":
                                    file_type = meta_content.split(".")[-1]
                                    video_path = os.path.join(VIDEO_DOWNLOAD_PATH, user_account)
                                    tool.make_dir(video_path, 0)
                                    video_path = os.path.join(video_path, photo_info["code"] + "." + file_type)
                                    if tool.save_image(meta_content, video_path):
                                        print_step_msg(user_account + " 视频：" + photo_info["code"] + "下载成功")
                                    else:
                                        print_step_msg(user_account + " 视频：" + photo_info["code"] + "下载失败")
                                    find_video = True
                                    break
                            if not find_video:
                                print_error_msg(user_account + " 视频：" + photo_info["code"] + "没有获取到源地址")
                        else:
                            print_error_msg(user_account + " 信息页：" + post_page_url + " 访问失败")

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if is_over:
                    break

                if media_data["page_info"]["has_next_page"]:
                    cursor = str(media_data["page_info"]["end_cursor"])
                else:
                    break

            print_step_msg(user_account + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1 and image_count > 1:
                image_list = sorted(os.listdir(image_path), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(image_list) >= 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_account)
                    if robot.sort_file(image_path, destination_path, int(self.user_info[2]), 4):
                        print_step_msg(user_account + " 图片从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(user_account + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                        tool.process_exit()

                # 删除临时文件夹
                tool.remove_dir(image_path)

            self.user_info[2] = str(int(self.user_info[2]) + image_count - 1)

            # 保存最后的信息
            threadLock.acquire()
            new_save_data_file = open(NEW_SAVE_DATA_PATH, "a")
            new_save_data_file.write("\t".join(self.user_info) + "\n")
            new_save_data_file.close()
            TOTAL_IMAGE_COUNT += image_count - 1
            USER_IDS.remove(user_account)
            threadLock.release()

            print_step_msg(user_account + " 完成")
        except Exception, e:
            print_step_msg(user_account + " 异常")
            print_error_msg(str(e))
            print_error_msg(str(e) + "\n" + str(traceback.print_exc()))


if __name__ == "__main__":
    tool.restore_process_status()
    Instagram().main()
