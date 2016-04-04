# -*- coding:UTF-8  -*-
'''
Created on 2013-4-8

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


class GooglePlus(robot.Robot):

    def __init__(self):
        global GET_IMAGE_URL_COUNT
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        super(GooglePlus, self).__init__()

        # 全局变量
        GET_IMAGE_URL_COUNT = 100  # 单次获取最新的N张照片,G+ 限制最多1000张
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
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not tool.make_dir(IMAGE_DOWNLOAD_PATH, 0):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败，程序结束！")
            tool.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.save_data_path):
            user_id_list = robot.read_save_data(self.save_data_path, 0, ["", "_0", "0", "", "", ""])
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
        global GET_IMAGE_URL_COUNT
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT
        global TOTAL_IMAGE_COUNT
        global USER_IDS

        user_id = self.user_info[0]
        user_name = self.user_info[1]

        print_step_msg(user_name + " 开始")

        try:
            # 初始化数据
            last_message_url = self.user_info[3]
            self.user_info[3] = ""  # 置空，存放此次的最后URL
            # 为防止前一次的记录图片被删除，根据历史图片总数给一个单次下载的数量限制
            # 第一次下载，不用限制
            if last_message_url == "":
                limit_download_count = 0
            else:
                last_message_page_return_code = tool.http_request(last_message_url)[0]
                # 上次记录的信息首页还在，那么不要限制
                if last_message_page_return_code == 1:
                    limit_download_count = 0
                else:
                    # 历史总数的10%，下限50、上限1000
                    limit_download_count = min(max(50, int(self.user_info[2]) / 100 * 10), 1000)
            image_count = 1
            message_url_list = []
            image_url_list = []
            is_over = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if last_message_url.find("picasaweb.google.com/") != -1:
                is_error = True
            else:
                is_error = False
            need_make_download_dir = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = os.path.join(IMAGE_TEMP_PATH, user_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, self.user_info[4], user_name)

            # 图片下载
            photo_album_url = "https://plus.google.com/_/photos/pc/read/"
            key = ""

            while 1:
                post_data = 'f.req=[["posts",null,null,"synthetic:posts:%s",3,"%s",null],[%s,1,null],"%s",null,null,null,null,null,null,null,2]' % (user_id, user_id, GET_IMAGE_URL_COUNT, key)
                [photo_album_page_return_code, photo_album_page] = tool.http_request(photo_album_url, post_data)[:2]

                # 无法获取信息首页
                if photo_album_page_return_code != 1:
                    print_error_msg(user_name + " 无法获取相册首页: " + photo_album_url + ', key = ' + key)
                    break

                # 相册也中全部的信息页
                this_page_message_url_list = re.findall('\[\["(https://picasaweb.google.com/[^"]*)"', photo_album_page)
                for message_url in this_page_message_url_list:
                    # 有可能拿到带authkey的，需要去掉
                    # https://picasaweb.google.com/116300481938868290370/2015092603?authkey\u003dGv1sRgCOGLq-jctf-7Ww#6198800191175756402
                    message_url = message_url.replace("\u003d", "=")
                    try:
                        temp = re.findall("(.*)\?.*(#.*)", message_url)
                        real_message_url = temp[0][0] + temp[0][1]
                    except:
                        real_message_url = message_url
                    # 判断是否重复
                    if real_message_url in message_url_list:
                        continue
                    message_url_list.append(real_message_url)
                    trace("message URL:" + message_url)

                    # 将第一张image的URL保存到新id list中
                    if self.user_info[3] == "":
                        self.user_info[3] = real_message_url

                    # 检查是否已下载到前一次的图片
                    if real_message_url == last_message_url:
                        is_error = False
                        is_over = True
                        break

                    [message_page_return_code, message_page] = tool.http_request(message_url)[:2]
                    if message_page_return_code != 1:
                        print_error_msg(user_name + " 无法获取信息页")
                        continue

                    message_page_image_data = re.findall('id="lhid_feedview">([\s|\S]*)<div id="lhid_content">', message_page)
                    if len(message_page_image_data) != 1:
                        print_error_msg(user_name + " 信息页：" + message_url + " 中没有找到相关图片信息，第" + str(image_count) + "张图片")
                        image_count += 1
                        continue
                    message_page_image_data = message_page_image_data[0]

                    urls = re.findall('<img src="(\S*)">', message_page_image_data)
                    if len(urls) == 0:
                        print_error_msg(user_name + " 信息页：" + message_url + " 中没有找到标签'<img src='")
                        continue

                    for image_url in urls:
                        if image_url in image_url_list:
                            continue
                        image_url_list.append(image_url)
                        trace("image URL:" + image_url)

                        image_url = generate_max_resolution_image_url(image_url)
                        # 文件类型
                        if image_url.rfind("/") < image_url.rfind("."):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = "jpg"
                        file_path = os.path.join(image_path, str("%04d" % image_count) + "." + file_type)

                        # 下载
                        print_step_msg(user_name + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                        # 第一张图片，创建目录
                        if need_make_download_dir:
                            if not tool.make_dir(image_path, 0):
                                print_error_msg(user_name + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
                                tool.process_exit()
                            need_make_download_dir = False
                        if tool.save_image(image_url, file_path):
                            print_step_msg(user_name + " 第" + str(image_count) + "张图片下载成功")
                            image_count += 1
                        else:
                            print_error_msg(user_name + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")

                        # 达到下载数量限制，结束
                        if 0 < limit_download_count < image_count:
                            is_over = True
                            break

                        # 达到配置文件中的下载数量，结束
                        if 0 < GET_IMAGE_COUNT < image_count:
                            is_over = True
                            break

                if is_over:
                    break

                # 查找下一页的token key
                finds = re.findall('"([.]?[a-zA-Z0-9-_]*)"', photo_album_page)
                if len(finds[0]) > 80:
                    key = finds[0]
                    trace(user_name + " 下一个信息首页token:" + key)
                else:
                    # 不是第一次下载
                    if last_message_url != "":
                        print_error_msg(user_name + " 没有找到下一页的token，将该页保存：")
                        print_error_msg(photo_album_page)
                    break

            # 如果有错误且没有发现新的图片，复原旧数据
            if self.user_info[3] == "" and last_message_url != "":
                self.user_info[3] = last_message_url

            print_step_msg(user_name + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1 and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, self.user_info[4], user_name)
                if robot.sort_file(image_path, destination_path, int(self.user_info[2]), 4):
                    print_step_msg(user_name + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(user_name + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    tool.process_exit()

            self.user_info[2] = str(int(self.user_info[2]) + image_count - 1)

            if is_error:
                print_error_msg(user_name + " 图片数量异常，请手动检查")

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.user_info) + "\n", NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            USER_IDS.remove(user_id)
            threadLock.release()

            print_step_msg(user_name + " 完成")

        except Exception, e:
            print_step_msg(user_name + " 异常")
            print_error_msg(str(e))


# 重组URL并使用最大分辨率
# https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/Ic42/s128/16%252520-%2525201.jpg
# ->
# https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/s0-Ic42/16%252520-%2525201.jpg
def generate_max_resolution_image_url(image_url):
    temp_list = image_url.split("/")
    temp_list[-2] = "s0"
    return "/".join(temp_list[:-3]) + "/s0-" + temp_list[-3] + "/" + temp_list[-1]


if __name__ == "__main__":
    GooglePlus().main()
