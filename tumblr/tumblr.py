# -*- coding:UTF-8  -*-
"""
tumblr图片和视频爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import os
import re
import threading
import time
import traceback
import urllib2

ACCOUNTS = []
TOTAL_IMAGE_COUNT = 0
TOTAL_VIDEO_COUNT = 0
GET_PAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True
IS_DOWNLOAD_IMAGE = True
IS_DOWNLOAD_VIDEO = True

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


# 获取一页的媒体信息
def get_post_page_data(post_url, postfix_list):
    post_page_return_code, post_page_data = tool.http_request(post_url)[:2]
    # 不带后缀的可以访问，则直接返回页面
    if post_page_return_code == 1:
        return post_page_data
    # 不带后缀的无法范文，则依次访问带有后缀的页面
    for postfix in postfix_list:
        temp_post_url = post_url + "/" + urllib2.quote(postfix)
        post_page_return_code, post_page_data = tool.http_request(temp_post_url)[:2]
        if post_page_return_code == 1:
            return post_page_data
    return None


# 过滤头像以及页面上找到不同分辨率的同一张图，保留分辨率较大的那张
def filter_different_resolution_images(image_url_list):
    new_image_url_list = {}
    for image_url in image_url_list:
        if image_url.find("/avatar_") == -1:
            image_id = image_url[image_url.find("media.tumblr.com/") + len("media.tumblr.com/"):].split("/")[0]

            if image_id in new_image_url_list:
                resolution = int(image_url.split("_")[-1].split(".")[0])
                old_resolution = int(new_image_url_list[image_id].split("_")[-1].split(".")[0])
                if resolution < old_resolution:
                    continue
            new_image_url_list[image_id] = image_url

    return new_image_url_list.values()


# 根据post id将同样的信息页合并
def filter_post_url(post_url_list):
    new_post_url_list = {}
    for post_url in post_url_list:
        # 无效的信息页
        post_url = post_url.replace("/embed", "")
        temp = post_url[post_url.find("tumblr.com/post/") + len("tumblr.com/post/"):].split("/", 1)
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


class Tumblr(robot.Robot):
    def __init__(self):
        global GET_PAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_TEMP_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global IS_DOWNLOAD_IMAGE
        global IS_DOWNLOAD_VIDEO

        super(Tumblr, self).__init__()

        # 设置全局变量，供子线程调用
        GET_PAGE_COUNT = self.get_page_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        VIDEO_TEMP_PATH = self.video_temp_path
        VIDEO_DOWNLOAD_PATH = self.video_download_path
        IS_SORT = self.is_sort
        IS_DOWNLOAD_IMAGE = self.is_download_image
        IS_DOWNLOAD_VIDEO = self.is_download_video
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        if not IS_DOWNLOAD_IMAGE and not IS_DOWNLOAD_VIDEO:
            print_error_msg("下载图片和视频都没有开启，请检查配置！")
            tool.process_exit()

        start_time = time.time()

        # 创建图片保存目录
        if IS_DOWNLOAD_IMAGE:
            print_step_msg("创建图片根目录 %s" % IMAGE_DOWNLOAD_PATH)
            if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
                print_error_msg("创建图片根目录 %s 失败" % IMAGE_DOWNLOAD_PATH)
                tool.process_exit()

        # 创建视频保存目录
        if IS_DOWNLOAD_VIDEO:
            print_step_msg("创建视频根目录 %s" % VIDEO_DOWNLOAD_PATH)
            if not tool.make_dir(VIDEO_DOWNLOAD_PATH, 0):
                print_error_msg("创建视频根目录 %s 失败" % VIDEO_DOWNLOAD_PATH)
                tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 寻找idlist，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  image_count  video_count  last_post_id
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])
            ACCOUNTS = account_list.keys()
        else:
            print_error_msg("存档文件 %s 不存在" % self.save_data_path)
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 启用线程监控是否需要暂停其他下载线程
        process_control_thread = tool.ProcessControl()
        process_control_thread.setDaemon(True)
        process_control_thread.start()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
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

        # 删除临时文件夹
        tool.remove_dir(IMAGE_TEMP_PATH)

        # 重新排序保存存档文件
        account_list = robot.read_save_data(NEW_SAVE_DATA_PATH, 0, [])
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)
        os.remove(NEW_SAVE_DATA_PATH)

        duration_time = int(time.time() - start_time)
        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (duration_time, TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]

        try:
            print_step_msg(account_id + " 开始")

            host_url = "%s.tumblr.com" % account_id
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_id)
                video_path = os.path.join(VIDEO_TEMP_PATH, account_id)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_id)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)

            page_count = 1
            image_count = 1
            video_count = 1
            first_post_id = ""
            unique_list = []
            is_over = False
            need_make_image_dir = True
            need_make_video_dir = True
            while not is_over:
                index_page_url = "http://%s/page/%s" % (host_url, page_count)

                index_page_return_code, index_page_response = tool.http_request(index_page_url)[:2]
                # 无法获取信息首页
                if index_page_return_code != 1:
                    print_error_msg(account_id + " 无法访问相册页 %s" % index_page_url)
                    tool.process_exit()

                # 相册也中全部的信息页
                post_url_list = re.findall('"(http[s]?://' + host_url + '/post/[^"|^#]*)["|#]', index_page_response)
                if len(post_url_list) == 0:
                    # 下载完毕了
                    break

                trace(account_id + " 相册第%s页获取的所有信息页：%s" % (page_count, post_url_list))
                post_url_list = filter_post_url(post_url_list)
                trace(account_id + " 相册第%s页去重排序后的信息页：%s" % (page_count, post_url_list))
                for post_id in sorted(post_url_list.keys(), reverse=True):
                    # 将第一个信息页的id做为新的存档记录
                    if first_post_id == "":
                        first_post_id = post_id
                    # 检查信息页id是否小于上次的记录
                    if post_id <= self.account_info[3]:
                        is_over = True
                        break

                    post_url = "http://%s/post/%s" % (host_url, post_id)
                    # 获取指定一页的媒体信息
                    post_page_data = get_post_page_data(post_url, post_url_list[post_id])
                    if post_page_data is None:
                        print_error_msg(account_id + " 无法访问信息页 %s" % post_url)
                        continue

                    # 截取html中的head标签内的内容
                    post_page_head = tool.find_sub_string(post_page_data, "<head", "</head>", 3)
                    if not post_page_head:
                        print_error_msg(account_id + " 信息页 %s 截取head标签异常" % post_url)
                        continue

                    # 获取og_type（页面类型的是视频还是图片或其他）
                    og_type = tool.find_sub_string(post_page_head, '<meta property="og:type" content="', '" />')
                    if not og_type:
                        print_error_msg(account_id + " 信息页 %s，'og:type'获取异常" % post_url)
                        continue

                    # 新增信息页导致的重复判断
                    if post_id in unique_list:
                        continue
                    else:
                        unique_list.append(post_id)

                    # 空
                    if og_type == "tumblr-feed:entry":
                        continue

                    # 视频下载
                    if IS_DOWNLOAD_VIDEO and og_type == "tumblr-feed:video":
                        video_page_url = "http://www.tumblr.com/video/%s/%s/0" % (account_id, post_id)
                        video_page_return_code, video_page = tool.http_request(video_page_url)[:2]
                        if video_page_return_code == 1:
                            video_list = re.findall('src="(http[s]?://www.tumblr.com/video_file/' + post_id + '/[^"]*)" type="([^"]*)"', video_page)
                            if len(video_list) > 0:
                                for video_url, video_type in video_list:
                                    print_step_msg(account_id + " 开始下载第%s个视频 %s" % (video_count, video_url))

                                    file_type = video_type.split("/")[-1]
                                    video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                                    # 第一个视频，创建目录
                                    if need_make_video_dir:
                                        if not tool.make_dir(video_path, 0):
                                            print_error_msg(account_id + " 创建视频下载目录 %s 失败" % video_path)
                                            tool.process_exit()
                                        need_make_video_dir = False
                                    if tool.save_net_file(video_url, video_file_path):
                                        print_step_msg(account_id + " 第%s个视频下载成功" % video_count)
                                        video_count += 1
                                    else:
                                        print_error_msg(account_id + " 第%s个视频 %s 下载失败" % (video_count, video_url))
                            else:
                                print_error_msg(account_id + " 第%s个视频 视频页 %s 中没有找到视频" % (video_count, video_page_url))
                        else:
                            print_error_msg(account_id + " 第%s个视频 无法访问视频页 %s" % (video_count, video_page_url))

                    # 图片下载
                    if IS_DOWNLOAD_IMAGE:
                        page_image_url_list = re.findall('"(http[s]?://\w*[.]?media.tumblr.com/[^"]*)"', post_page_head)
                        trace(account_id + " 信息页 %s 获取的所有图片：%s" % (post_url, page_image_url_list))
                        # 过滤头像以及页面上找到不同分辨率的同一张图
                        page_image_url_list = filter_different_resolution_images(page_image_url_list)
                        trace(account_id + " 信息页 %s 过滤后的所有图片：%s" % (post_url, page_image_url_list))
                        if len(page_image_url_list) > 0:
                            for image_url in page_image_url_list:
                                print_step_msg(account_id + " 开始下载第%s张图片 %s" % (image_count, image_url))

                                file_type = image_url.split(".")[-1]
                                image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                                # 第一张图片，创建目录
                                if need_make_image_dir:
                                    if not tool.make_dir(image_path, 0):
                                        print_error_msg(account_id + " 创建图片下载目录 %s 失败" % image_path)
                                        tool.process_exit()
                                    need_make_image_dir = False
                                if tool.save_net_file(image_url, image_file_path):
                                    print_step_msg(account_id + " 第%s张图片下载成功" % image_count)
                                    image_count += 1
                                else:
                                    print_error_msg(account_id + " 第%s张图片 %s 下载失败" % (image_count, image_url))
                        else:
                            print_error_msg(account_id + " 第%s张图片 信息页 %s 中没有找到图片" % (image_count, post_url))

                if not is_over:
                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_PAGE_COUNT < page_count:
                        is_over = True
                    else:
                        page_count += 1

            print_step_msg(account_id + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_id)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        print_step_msg(account_id + " 图片从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_id + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                        print_step_msg(account_id + " 视频从下载目录移动到保存目录成功")
                    else:
                        print_error_msg(account_id + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_post_id != "":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_post_id

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_id + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_id + " 提前退出")
            else:
                print_error_msg(account_id + " 异常退出")
        except Exception, e:
            print_step_msg(account_id + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Tumblr().main()
