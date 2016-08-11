# -*- coding:UTF-8  -*-
"""
Google Plus图片爬虫
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

ACCOUNTS = []
GET_IMAGE_URL_COUNT = 100  # 单次获取最新的N张照片,G+ 限制最多1000张
TOTAL_IMAGE_COUNT = 0
GET_IMAGE_COUNT = 0
IMAGE_TEMP_PATH = ""
IMAGE_DOWNLOAD_PATH = ""
VIDEO_TEMP_PATH = ""
VIDEO_DOWNLOAD_PATH = ""
NEW_SAVE_DATA_PATH = ""
IS_SORT = True

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


# 重组URL并使用最大分辨率
# https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/Ic42/s128/16%252520-%2525201.jpg
# ->
# https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/s0-Ic42/16%252520-%2525201.jpg

# https://lh3.googleusercontent.com/-hHhAtsQ9m5g/Vxy_HVck36I/AAAAAAACqV0/O0H3OnEWa1wqVFMnidRySNJvF6v-P23UQCCo/s128/24%2B-%2B1
# ->
# https://lh3.googleusercontent.com/-hHhAtsQ9m5g/Vxy_HVck36I/AAAAAAACqV0/O0H3OnEWa1wqVFMnidRySNJvF6v-P23UQCCo/s0/24%2B-%2B1
def generate_max_resolution_image_url(image_url):
    temp_list = image_url.split("/")
    temp_list[-2] = "s0"
    return "/".join(temp_list)


class GooglePlus(robot.Robot):
    def __init__(self):
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        super(GooglePlus, self).__init__(True)

        # 设置全局变量，供子线程调用
        GET_IMAGE_COUNT = self.get_image_count
        IMAGE_TEMP_PATH = self.image_temp_path
        IMAGE_DOWNLOAD_PATH = self.image_download_path
        IS_SORT = self.is_sort
        NEW_SAVE_DATA_PATH = robot.get_new_save_file_path(self.save_data_path)

        tool.print_msg("配置文件读取完成")

    def main(self):
        global ACCOUNTS

        start_time = time.time()

        if not self.is_download_image:
            print_error_msg("下载图片没有开启，请检查配置！")
            tool.process_exit()

        # 图片保存目录
        print_step_msg("创建图片根目录 %s" % IMAGE_DOWNLOAD_PATH)
        if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
            print_error_msg("创建图片根目录 %s 失败" % IMAGE_DOWNLOAD_PATH)
            tool.process_exit()

        # 寻找idlist，如果没有结束进程
        account_list = {}
        if os.path.exists(self.save_data_path):
            # account_id  image_count  album_id  (account_name)  (file_path)
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "0", "0"])
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
        print_step_msg("全部下载完毕，耗时%s秒，共计图片%s张" % (duration_time, TOTAL_IMAGE_COUNT))


class Download(threading.Thread):
    def __init__(self, account_info):
        threading.Thread.__init__(self)
        self.account_info = account_info

    def run(self):
        global TOTAL_IMAGE_COUNT

        account_id = self.account_info[0]
        if len(self.account_info) >= 4 and self.account_info[3]:
            account_name = self.account_info[3]
        else:
            account_name = self.account_info[0]
        if len(self.account_info) >= 5 and self.account_info[4]:
            account_file_path = self.account_info[4]
        else:
            account_file_path = ""

        try:
            print_step_msg(account_name + " 开始")

            photo_album_url = "https://plus.google.com/_/photos/pc/read/"
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT:
                image_path = os.path.join(IMAGE_TEMP_PATH, account_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_file_path, account_name)

            # 图片下载
            image_count = 1
            key = ""
            first_album_id = "0"
            unique_list = []
            is_over = False
            need_make_download_dir = True
            while not is_over:
                post_data = 'f.req=[["posts",null,null,"synthetic:posts:%s",3,"%s",null],[%s,1,null],"%s",null,null,null,null,null,null,null,2]' % (account_id, account_id, GET_IMAGE_URL_COUNT, key)
                index_page_return_code, index_page_response = tool.http_request(photo_album_url, post_data)[:2]
                # 无法获取信息首页
                if index_page_return_code != 1:
                    print_error_msg(account_name + " 无法访问相册首页 %s，key：%s" % (photo_album_url, key))
                    tool.process_exit()

                # 相册也中全部的信息页
                page_message_url_list = re.findall('\[\["(https://picasaweb.google.com/[^"]*)"', index_page_response)
                trace(account_name + " 相册获取的所有信息页：%s" % page_message_url_list)
                for message_url in page_message_url_list:
                    # 有可能拿到带authkey的，需要去掉
                    # https://picasaweb.google.com/116300481938868290370/2015092603?authkey\u003dGv1sRgCOGLq-jctf-7Ww#6198800191175756402
                    message_url = message_url.replace("\u003d", "=")
                    message_page_return_code, message_page_data = tool.http_request(message_url)[:2]
                    if message_page_return_code != 1:
                        print_error_msg(account_name + " 第%s张图片，无法访问信息页 %s" % (image_count, message_url))
                        continue

                    # 查找信息页的album id
                    album_id = tool.find_sub_string(message_page_data, "var _album = {id:'", "'")
                    if not album_id:
                        print_error_msg(account_name + " 第%s张图片，信息页 %s 中没有找到album id" % (image_count, message_url))
                        continue

                    print_step_msg(account_name + " 信息页 %s 的album id：%s" % (message_url, album_id))
                    # 相同的album_id判断
                    if album_id in unique_list:
                        continue
                    else:
                        unique_list.append(album_id)
                    # 将第一个album_id做为新的存档记录
                    if first_album_id == "0":
                        first_album_id = album_id
                    # 检查是否已下载到前一次的图片
                    if int(album_id) <= int(self.account_info[2]):
                        is_over = True
                        break

                    # 截取图片信息部分
                    message_page_data = tool.find_sub_string(message_page_data, 'id="lhid_feedview">', '<div id="lhid_content">')
                    if not message_page_data:
                        print_error_msg(account_name + " 第%s张图片，信息页 %s 中没有找到相关图片信息" % (image_count, message_url))
                        continue

                    # 匹配查找所有的图片
                    page_image_url_list = re.findall('<img src="(\S*)">', message_page_data)
                    trace(account_name + " 信息页 %s 获取的所有图片：%s" % (message_url, page_image_url_list))
                    if len(page_image_url_list) == 0:
                        print_error_msg(account_name + " 第%s张图片，信息页 %s 中没有找到标签'<img src='" % (image_count, message_url))
                        continue

                    for image_url in page_image_url_list:
                        image_url = generate_max_resolution_image_url(image_url)
                        # 文件类型
                        if image_url.rfind("/") < image_url.rfind("."):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = "jpg"
                        file_path = os.path.join(image_path, "%04d.%s" % (image_count, file_type))

                        # 下载
                        print_step_msg(account_name + " 开始下载第%s张图片 %s" % (image_count, image_url))
                        # 第一张图片，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(image_path, 0):
                                print_error_msg(account_name + " 创建图片下载目录 %s 失败" % image_path)
                                tool.process_exit()
                            need_make_download_dir = False
                        if tool.save_net_file(image_url, file_path):
                            print_step_msg(account_name + " 第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            print_error_msg(account_name + " 第%s张图片 %s 下载失败" % (image_count, image_url))

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_IMAGE_COUNT < image_count:
                            is_over = True
                            break
                    if is_over:
                        break

                if not is_over:
                    # 查找下一页的token key
                    key_find = re.findall('"([.]?[a-zA-Z0-9-_]*)"', index_page_response)
                    if len(key_find) > 0 and len(key_find[0]) > 80:
                        key = key_find[0]
                    else:
                        # 不是第一次下载
                        if self.account_info[2] != "":
                            print_error_msg(account_name + " 没有找到下一页的token，将该页保存：")
                            print_error_msg(index_page_response)
                        is_over = True

            print_step_msg(account_name + " 下载完毕，总共获得%s张图片" % (image_count - 1))

            # 排序
            if IS_SORT and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, account_file_path, account_name)
                if robot.sort_file(image_path, destination_path, int(self.account_info[1]), 4):
                    print_step_msg(account_name + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(account_name + " 创建图片子目录 %s 失败" % destination_path)
                    tool.process_exit()

            # 新的存档记录
            if first_album_id != "":
                self.account_info[1] = str(int(self.account_info[1]) + image_count - 1)
                self.account_info[2] = first_album_id

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.account_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            ACCOUNTS.remove(account_id)
            threadLock.release()

            print_step_msg(account_name + " 完成")
        except SystemExit, se:
            if se.code == 0:
                print_step_msg(account_id + " 提前退出")
            else:
                print_error_msg(account_id + " 异常退出")
        except Exception, e:
            print_step_msg(account_name + " 未知异常")
            print_error_msg(str(e) + "\n" + str(traceback.format_exc()))


if __name__ == "__main__":
    GooglePlus().main()
