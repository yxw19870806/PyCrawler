# -*- coding:UTF-8  -*-
"""
tumblr图片和视频爬虫
http://www.tumblr.com/
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


# 获取一页的日志地址列表
def get_one_page_post_url_list(account_id, page_count):
    index_page_url = "http://%s.tumblr.com/page/%s" % (account_id, page_count)
    index_page_return_code, index_page_response = tool.http_request(index_page_url)[:2]
    if index_page_return_code == 1:
        return re.findall('"(http[s]?://' + account_id + '.tumblr.com/post/[^"|^#]*)["|#]', index_page_response)
    return None


# 根据post id将同样的信息页合并
def filter_post_url(post_url_list):
    new_post_url_list = {}
    for post_url in post_url_list:
        # 无效的信息页
        post_url = post_url.replace("/embed", "")
        temp = post_url[post_url.find("tumblr.com/post/") + len("tumblr.com/post/"):].split("/", 1)
        post_id = temp[0]
        if post_id not in new_post_url_list:
            new_post_url_list[post_id] = []
        if len(temp) == 2:
            new_post_url_list[post_id].append(temp[1])

    # 去重排序
    for post_id in new_post_url_list:
        new_post_url_list[post_id] = sorted(list(set(new_post_url_list[post_id])), reverse=True)

    return new_post_url_list


# 根据日志地址以及可能的后缀，获取日志页面的head标签下的内容
def get_post_page_head(post_url, postfix_list):
    post_page_return_code, post_page_data = tool.http_request(post_url)[:2]
    # 不带后缀的可以访问，则直接返回页面
    # 如果无法访问，则依次访问带有后缀的页面
    if post_page_return_code != 1:
        for postfix in postfix_list:
            temp_post_url = post_url + "/" + urllib2.quote(postfix)
            post_page_return_code, post_page_data = tool.http_request(temp_post_url)[:2]
            if post_page_return_code == 1:
                break
    if post_page_data is not None:
        return tool.find_sub_string(post_page_data, "<head", "</head>", 3)
    else:
        return None


# 根据日志id获取页面中的全部视频信息（视频地址、视频）
def get_video_list(account_id, post_id):
    video_play_url = "http://www.tumblr.com/video/%s/%s/0" % (account_id, post_id)
    video_page_return_code, video_page = tool.http_request(video_play_url)[:2]
    if video_page_return_code == 1:
        return re.findall('src="(http[s]?://www.tumblr.com/video_file/[^"]*)" type="([^"]*)"', video_page)
    return None


# 过滤头像以及页面上找到不同分辨率的同一张图，保留分辨率较大的那张
def filter_different_resolution_images(image_url_list):
    new_image_url_list = {}
    for image_url in image_url_list:
        # 头像，跳过
        if image_url.find("/avatar_") != -1:
            continue

        image_id = image_url[image_url.find("media.tumblr.com/") + len("media.tumblr.com/"):].split("/")[0]
        # 判断是否有分辨率更小的相同图片
        if image_id in new_image_url_list:
            resolution = int(image_url.split("_")[-1].split(".")[0])
            old_resolution = int(new_image_url_list[image_id].split("_")[-1].split(".")[0])
            if resolution < old_resolution:
                continue
        new_image_url_list[image_id] = image_url

    return new_image_url_list.values()


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

        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_DOWNLOAD_VIDEO: True,
            robot.SYS_SET_PROXY: True,
        }
        robot.Robot.__init__(self, sys_config)

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

    def main(self):
        global ACCOUNTS

        # 解析存档文件
        # account_id  image_count  video_count  last_post_id
        account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0", "0"])
        ACCOUNTS = account_list.keys()

        # 循环下载每个id
        main_thread_count = threading.activeCount()
        for account_id in sorted(account_list.keys()):
            # 检查正在运行的线程数
            while threading.activeCount() >= self.thread_count + main_thread_count:
                if robot.is_process_end() == 0:
                    time.sleep(10)
                else:
                    break

            # 提前结束
            if robot.is_process_end() > 0:
                break

            # 开始下载
            thread = Download(account_list[account_id], self.thread_lock)
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
        self.finish_task()

        # 重新排序保存存档文件
        robot.rewrite_save_file(NEW_SAVE_DATA_PATH, self.save_data_path)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张，视频%s个" % (self.get_run_time(), TOTAL_IMAGE_COUNT, TOTAL_VIDEO_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info, thread_lock):
        threading.Thread.__init__(self)
        self.account_info = account_info
        self.thread_lock = thread_lock

    def run(self):
        global TOTAL_IMAGE_COUNT
        global TOTAL_VIDEO_COUNT

        account_id = self.account_info[0]

        try:
            log.step(account_id + " 开始")

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
                post_url_list = get_one_page_post_url_list(account_id, page_count)
                if post_url_list is None:
                    log.error(account_id + " 无法访问第%s页相册页" % page_count)
                    tool.process_exit()

                if len(post_url_list) == 0:
                    # 下载完毕了
                    break

                log.trace(account_id + " 相册第%s页获取的所有信息页：%s" % (page_count, post_url_list))
                post_url_list_group_by_post_id = filter_post_url(post_url_list)
                log.trace(account_id + " 相册第%s页去重排序后的信息页：%s" % (page_count, post_url_list_group_by_post_id))
                log.step(account_id + " 相册第%s页获取到%s页信息页" % (page_count, len(post_url_list_group_by_post_id)))
                for post_id in sorted(post_url_list_group_by_post_id.keys(), reverse=True):
                    # 检查信息页id是否小于上次的记录
                    if post_id <= self.account_info[3]:
                        is_over = True
                        break

                    # 将第一个信息页的id做为新的存档记录
                    if first_post_id == "":
                        first_post_id = post_id

                    # 获取信息页并截取head标签内的内容
                    post_url = "http://%s.tumblr.com/post/%s" % (account_id, post_id)
                    post_page_head = get_post_page_head(post_url, post_url_list_group_by_post_id[post_id])
                    if post_page_head is None:
                        log.error(account_id + " 无法访问信息页 %s" % post_url)
                        continue
                    if not post_page_head:
                        log.error(account_id + " 信息页 %s 截取head标签异常" % post_url)
                        continue

                    # 获取og_type（页面类型的是视频还是图片或其他）
                    og_type = tool.find_sub_string(post_page_head, '<meta property="og:type" content="', '" />')
                    if not og_type:
                        log.error(account_id + " 信息页 %s，'og:type'获取异常" % post_url)
                        continue

                    # 空、音频、引用，跳过
                    if og_type in ["tumblr-feed:entry", "tumblr-feed:audio", "tumblr-feed:quote", "tumblr-feed:link"]:
                        continue

                    # 新增信息页导致的重复判断
                    if post_id in unique_list:
                        continue
                    else:
                        unique_list.append(post_id)

                    # 视频下载
                    if IS_DOWNLOAD_VIDEO and og_type == "tumblr-feed:video":
                        video_list = get_video_list(account_id, post_id)
                        if video_list is None:
                            log.error(account_id + " 第%s个视频 日志id：%s无法访问播放页" % (video_count, post_id))
                        else:
                            if len(video_list) > 0:
                                for video_url, video_type in list(video_list):
                                    log.step(account_id + " 开始下载第%s个视频 %s" % (video_count, video_url))

                                    # 第一个视频，创建目录
                                    if need_make_video_dir:
                                        if not tool.make_dir(video_path, 0):
                                            log.error(account_id + " 创建视频下载目录 %s 失败" % video_path)
                                            tool.process_exit()
                                        need_make_video_dir = False

                                    file_type = video_type.split("/")[-1]
                                    video_file_path = os.path.join(video_path, "%04d.%s" % (video_count, file_type))
                                    if tool.save_net_file(video_url, video_file_path):
                                        log.step(account_id + " 第%s个视频下载成功" % video_count)
                                        video_count += 1
                                    else:
                                        log.error(account_id + " 第%s个视频 %s 下载失败" % (video_count, video_url))
                            else:
                                log.error(account_id + " 第%s个视频 日志id：%s 中没有找到视频" % (video_count, post_id))

                    # 图片下载
                    if IS_DOWNLOAD_IMAGE:
                        if og_type == "tumblr-feed:video":
                            page_image_url_list = []
                            video_image_url = tool.find_sub_string(post_page_head, '<meta property="og:image" content="', '" />')
                            if video_image_url:
                                page_image_url_list.append(video_image_url)
                        else:
                            page_image_url_list = re.findall('"(http[s]?://\w*[.]?media.tumblr.com/[^"]*)"', post_page_head)
                            log.trace(account_id + " 信息页 %s 过滤前的所有图片：%s" % (post_url, page_image_url_list))
                            # 过滤头像以及页面上找到不同分辨率的同一张图
                            page_image_url_list = filter_different_resolution_images(page_image_url_list)
                        log.trace(account_id + " 信息页 %s 获取的的所有图片：%s" % (post_url, page_image_url_list))
                        if len(page_image_url_list) > 0:
                            for image_url in page_image_url_list:
                                log.step(account_id + " 开始下载第%s张图片 %s" % (image_count, image_url))

                                # 第一张图片，创建目录
                                if need_make_image_dir:
                                    if not tool.make_dir(image_path, 0):
                                        log.error(account_id + " 创建图片下载目录 %s 失败" % image_path)
                                        tool.process_exit()
                                    need_make_image_dir = False

                                file_type = image_url.split(".")[-1]
                                image_file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))
                                if tool.save_net_file(image_url, image_file_path):
                                    log.step(account_id + " 第%s张图片下载成功" % image_count)
                                    image_count += 1
                                else:
                                    log.error(account_id + " 第%s张图片 %s 下载失败" % (image_count, image_url))
                        else:
                            log.error(account_id + " 第%s张图片 信息页 %s 中没有找到图片" % (image_count, post_url))

                if not is_over:
                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_PAGE_COUNT <= page_count:
                        is_over = True
                    else:
                        page_count += 1

            log.step(account_id + " 下载完毕，总共获得%s张图片和%s个视频" % (image_count - 1, video_count - 1))

            # 排序
            if IS_SORT:
                if image_count > 1:
                    destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_id)
                    if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                        log.step(account_id + " 图片从下载目录移动到保存目录成功")
                    else:
                        log.error(account_id + " 创建图片保存目录 %s 失败" % destination_path)
                        tool.process_exit()
                if video_count > 1:
                    destination_path = os.path.join(VIDEO_DOWNLOAD_PATH, account_id)
                    if robot.sort_file(video_path, destination_path, int(self.account_info[2]), 4):
                        log.step(account_id + " 视频从下载目录移动到保存目录成功")
                    else:
                        log.error(account_id + " 创建视频保存目录 %s 失败" % destination_path)
                        tool.process_exit()

            # 新的存档记录
            if first_post_id != "":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = str(int(self.account_info[2]) + video_count - 1)
                self.account_info[3] = first_post_id

            # 保存最后的信息
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            self.thread_lock.acquire()
            TOTAL_IMAGE_COUNT += image_count - 1
            TOTAL_VIDEO_COUNT += video_count - 1
            ACCOUNTS.remove(account_id)
            self.thread_lock.release()

            log.step(account_id + " 完成")
        except SystemExit, se:
            if se.code == 0:
                log.step(account_id + " 提前退出")
            else:
                log.error(account_id + " 异常退出")
        except Exception, e:
            log.error(account_id + " 未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    Tumblr().main()
