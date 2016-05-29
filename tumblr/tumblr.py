# -*- coding:UTF-8  -*-
'''
Created on 2016-5-24

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool
import os
import re
import threading
import time
import urllib2

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


class Tumblr(robot.Robot):

    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        super(Tumblr, self).__init__()

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
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.save_data_path):
            user_id_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
            USER_IDS = user_id_list.keys()
        else:
            print_error_msg("存档文件: " + self.save_data_path + "不存在，程序结束！")
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
        for user_id in sorted(user_id_list.keys()):
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
            thread = Download(user_id_list[user_id])
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

        print_step_msg(user_account + " 开始")

        try:
            # 初始化数据
            last_post_id = self.user_info[2]
            self.user_info[2] = ""  # 置空，存放此次的最后URL
            page_count = 1
            image_count = 1
            post_id_list = []
            video_post_id_list = []
            is_over = False
            need_make_download_dir = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = os.path.join(IMAGE_TEMP_PATH, user_account)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_account)

            host_url = '%s.tumblr.com' % user_account
            # 图片下载
            while 1:
                page_url = "http://%s/page/%s" % (host_url, page_count)

                [photo_album_page_return_code, photo_album_page] = tool.http_request(page_url)[:2]

                # 无法获取信息首页
                if photo_album_page_return_code != 1:
                    print_error_msg(user_account + " 无法获取相册页: " + page_url)
                    break

                # 相册也中全部的信息页
                this_page_post_url_list = re.findall('"(http[s]?://' + host_url + '/post/[^"|^#]*)["|#]', photo_album_page)

                if len(this_page_post_url_list) == 0:
                    # 下载完毕了
                    break
                else:
                    trace(user_account + " 相册第" + str(page_count) + "页获取的所有信息页: " + str(this_page_post_url_list))
                    this_page_post_url_list = filter_post_url(this_page_post_url_list)
                    trace(user_account + " 相册第" + str(page_count) + "页去重排序后的信息页: " + str(this_page_post_url_list))

                    for post_id in sorted(this_page_post_url_list.keys(), reverse=True):
                        # 已经下载过了
                        if post_id in post_id_list:
                            continue

                        # 将第一张image的URL保存到新id list中
                        if self.user_info[2] == "":
                            self.user_info[2] = post_id

                        # 检查是否已下载到前一次的图片
                        if post_id <= last_post_id:
                            is_over = True
                            break

                        post_url = 'http://%s/post/%s' % (host_url, post_id)
                        trace(user_account + " 信息页URL:" + post_url)
                        [post_page_return_code, post_page] = tool.http_request(post_url)[:2]
                        if post_page_return_code != 1:
                            for postfix in this_page_post_url_list[post_id]:
                                temp_post_url = post_url + '/' + urllib2.quote(postfix)
                                [post_page_return_code, post_page] = tool.http_request(temp_post_url)[:2]
                                if post_page_return_code == 1:
                                    break
                            if not post_page:
                                print_error_msg(user_account + " 无法获取信息页：" + post_url)
                                continue

                        # 截取html中的head标签内的内容
                        post_page = re.findall('(<head[\S|\s]*</head>)', post_page)
                        if len(post_page) == 1:
                            post_page = post_page[0]
                        else:
                            print_error_msg(user_account + " 信息页：" + post_url + " 截取head标签异常")
                            continue

                        # 视频
                        if post_id not in video_post_id_list:
                            og_type = re.findall('<meta property="og:type" content="([^"]*)" />', post_page)
                            if len(og_type) != 1:
                                print_error_msg(user_account + " 信息页：" + post_url + " '，og:type'获取异常")
                            else:
                                og_type = og_type[0]
                                if og_type == "tumblr-feed:video":
                                    video_page_url = "http://www.tumblr.com/video/%s/%s/0" % (user_account, post_id)
                                    [video_page_return_code, video_page] =  tool.http_request(video_page_url)[:2]
                                    if video_page_return_code == 1:
                                        video_list = re.findall('src="(http[s]?://www.tumblr.com/video_file/' + post_id +'/[^"]*)" type="([^"]*)"', video_page)
                                        for video_url, video_type in video_list:
                                            file_type = video_type.split("/")[-1]
                                            video_path = os.path.join(VIDEO_DOWNLOAD_PATH, user_account)
                                            tool.make_dir(video_path, 0)
                                            video_path = os.path.join(video_path, post_id + '.' + file_type)
                                            if tool.save_image(video_url, video_path):
                                                video_post_id_list.append(post_id)
                                                print_error_msg(user_account + " 视频：" + video_url + "下载成功")
                                            else:
                                                print_error_msg(user_account + " 视频：" + video_url + "下载失败")
                                    else:
                                        print_error_msg(user_account + " 无法获取视频页：" + video_page_url)
                                else:
                                    tool.write_test_file(post_url + '\t' + og_type)

                        post_page_image_list = re.findall('"(http[s]?://\w*[.]?media.tumblr.com/[^"]*)"', post_page)
                        post_page_image_list = filter_different_resolution_images(post_page_image_list)
                        # post_page_video_list = re.findall('"(http[s]?://vt.tumblr.com/[^"]*)"', post_page)
                        trace(user_account + " 信息页" + post_url + "获取的所有图片和视频: " + str(post_page_image_list))
                        if len(post_page_image_list) == 0:
                            print_error_msg(user_account + " 信息页：" + post_url + " 中没有找到图片")
                            continue

                        post_id_list.append(post_id)

                        for image_url in post_page_image_list:
                            # 文件类型
                            file_type = image_url.split(".")[-1]
                            file_path = os.path.join(image_path, str("%04d" % image_count) + "." + file_type)

                            # 下载
                            print_step_msg(user_account + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                            # 第一张图片，创建目录
                            if need_make_download_dir:
                                if not tool.make_dir(image_path, 0):
                                    print_error_msg(user_account + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
                                    tool.process_exit()
                                need_make_download_dir = False
                            if tool.save_image(image_url, file_path):
                                print_step_msg(user_account + " 第" + str(image_count) + "张图片下载成功")
                                image_count += 1
                            else:
                                print_error_msg(user_account + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")

                            # 达到配置文件中的下载数量，结束
                            if 0 < GET_IMAGE_COUNT < image_count:
                                is_over = True
                                break

                        if is_over:
                            break

                    if is_over:
                        break

                page_count += 1

            # 如果有错误且没有发现新的图片，复原旧数据
            if self.user_info[2] == "" and last_post_id != "":
                self.user_info[2] = last_post_id

            print_step_msg(user_account + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1 and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_account)
                if robot.sort_file(image_path, destination_path, int(self.user_info[1]), 4):
                    print_step_msg(user_account + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(user_account + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    tool.process_exit()

            self.user_info[1] = str(int(self.user_info[1]) + image_count - 1)

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.user_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            USER_IDS.remove(user_account)
            threadLock.release()

            print_step_msg(user_account + " 完成")

        except Exception, e:
            print_step_msg(user_account + " 异常")
            print_error_msg(str(e))


# 过滤页面上找到不同分辨率的同一张图，保留分辨率较大的那张
def filter_different_resolution_images(post_page_image_list):
    new_post_page_image_list = {}
    for image_url in post_page_image_list:
        if image_url.find('/avatar_') == -1:
            image_id = image_url[image_url.find('media.tumblr.com/') + len('media.tumblr.com/'):].split('/')[0]

            if image_id in new_post_page_image_list:
                resolution = int(image_url.split('_')[-1].split('.')[0])
                old_resolution = int(new_post_page_image_list[image_id].split('_')[-1].split('.')[0])
                if resolution < old_resolution:
                    continue
            new_post_page_image_list[image_id] = image_url

    return new_post_page_image_list.values()


def filter_post_url(this_page_post_url_list):
    new_post_url_list = {}
    for post_url in this_page_post_url_list:
        # 无效的信息页
        post_url = post_url.replace('/embed', '')
        temp = post_url[post_url.find('tumblr.com/post/') + len('tumblr.com/post/'):].split("/", 1)
        post_id = temp[0]
        if post_id in new_post_url_list:
            if len(temp) == 2:
                new_post_url_list[post_id].append(temp[1])
        else:
            new_post_url_list[post_id] = []
    # 去重排序
    for post_id in new_post_url_list:
        new_post_url_list[post_id] = sorted(list(set(new_post_url_list[post_id])), reverse=True)

    return new_post_url_list


if __name__ == "__main__":
    tool.restore_process_status()
    Tumblr().main()
