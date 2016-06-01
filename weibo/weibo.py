# -*- coding:UTF-8  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool
import hashlib
import json
import os
import random
import re
import threading
import time
import traceback

USER_IDS = []
INIT_SINCE_ID = "9999999999999999"

threadLock = threading.Lock()


def trace(msg):
    threadLock.acquire()
    log.trace(msg)
    threadLock.release()


def print_error_msg(msg):
    threadLock.acquire()
    log.error(msg)
    threadLock.release()


def print_step_msg(msg):
    threadLock.acquire()
    log.step(msg)
    threadLock.release()


def save_image(image_byte, image_path):
    image_path = tool.change_path_encoding(image_path)
    image_file = open(image_path, "wb")
    image_file.write(image_byte)
    image_file.close()


def visit_weibo(url):
    [page_return_code, page_response] = tool.http_request(url)[:2]
    if page_return_code == 1:
        # 有重定向
        redirect_url_index = page_response.find("location.replace")
        if redirect_url_index != -1:
            redirect_url_start = page_response.find("'", redirect_url_index) + 1
            redirect_url_stop = page_response.find("'", redirect_url_start)
            redirect_url = page_response[redirect_url_start:redirect_url_stop]
            return visit_weibo(redirect_url)
        # 没有cookies无法访问的处理
        if page_response.find("用户名或密码错误") != -1:
            print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
            tool.process_exit()
        # else:
        #     try:
        #         temp_page_response = page_response.decode("GBK")
        #         if temp_page_response.find("用户名或密码错误") != -1:
        #             print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
        #             tool.process_exit()
        #     except Exception,e:
        #         print e
        #         pass
        # 返回页面
        return str(page_response)
    return False


class Weibo(robot.Robot):

    def __init__(self, save_data_path="", this_image_download_path="", this_image_temp_path=""):
        global IMAGE_COUNT_PER_PAGE
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global IS_SORT

        robot.Robot.__init__(self)

        if save_data_path != "":
            self.save_data_path = save_data_path

        IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
        GET_IMAGE_COUNT = self.get_image_count
        if this_image_temp_path != "":
            IMAGE_TEMP_PATH = this_image_temp_path
        else:
            IMAGE_TEMP_PATH = self.image_temp_path
        if this_image_download_path != "":
            IMAGE_DOWNLOAD_PATH = this_image_download_path
        else:
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

        # 设置代理
        if self.is_proxy == 1:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not tool.set_cookie(self.cookie_path, self.browser_version):
            print_error_msg("导入浏览器cookies失败，程序结束！")
            tool.process_exit()

        # 寻找存档，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.save_data_path):
            user_id_list = robot.read_save_data(self.save_data_path, 0, ["", "_0", "0", "0"])
            USER_IDS = user_id_list.keys()
        else:
            print_error_msg("存档文件：" + self.save_data_path + "不存在，程序结束！")
            tool.process_exit()

        # 创建临时存档文件
        new_save_data_file = open(NEW_SAVE_DATA_PATH, "w")
        new_save_data_file.close()

        # 先访问下页面，产生个cookies
        visit_weibo("http://photo.weibo.com/photos/get_all?uid=1263970750&count=30&page=1&type=3")
        time.sleep(2)

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
        global IMAGE_COUNT_PER_PAGE
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global VIDEO_DOWNLOAD_PATH
        global NEW_SAVE_DATA_PATH
        global TOTAL_IMAGE_COUNT
        global USER_IDS

        user_id = self.user_info[0]
        user_name = self.user_info[1]

        try:
            print_step_msg(user_name + " 开始")

            # 初始化数据
            last_image_time = int(self.user_info[3])
            self.user_info[3] = "0"  # 置空，存放此次的最后图片上传时间
            page_count = 1
            image_count = 1
            since_id = INIT_SINCE_ID
            is_over = False
            need_make_download_dir = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if IS_SORT == 1:
                image_path = os.path.join(IMAGE_TEMP_PATH, user_name)
                video_path = os.path.join(IMAGE_TEMP_PATH, user_name)
            else:
                image_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_name)
                video_path = os.path.join(VIDEO_DOWNLOAD_PATH, user_name)

            # 视频
            while False:
                index_url = "http://weibo.com/u/%s?is_all=1" % user_id
                index_page = visit_weibo(index_url)

                page_id = re.findall("\$CONFIG\['page_id'\]='(\d*)'", index_page)
                if len(page_id) != 1:
                    print_error_msg(user_name + " 微博主页没有获取到page_id")
                    break

                page_id = page_id[0]
                video_url = "http://weibo.com/p/aj/album/loading"
                video_url += "?type=video&since_id=%s&page_id=%s&page=1&ajax_call=1" % (since_id, page_id)
                video_page = visit_weibo(video_url)
                try:
                    video_page = json.loads(video_page)
                except:
                    print_error_msg(user_name + " 返回的视频列表不是一个JSON数据")
                    break

                if "code" not in video_page:
                    print_error_msg(user_name + " 在视频列表：" + str(video_page) + " 中没有找到'code'字段")
                    break
                if int(video_page["code"]) != 100000:
                    print_error_msg(user_name + " 视频列表返回码异常：" + str(video_page["code"]))
                    break
                if "data" not in video_page:
                    print_error_msg(user_name + " 在视频列表：" + str(video_page) + " 中没有找到'data'字段")
                    break

                video_page_data = video_page[u"data"].encode("utf-8")
                video_page_url_list = re.findall('<a target="_blank" href="([^"]*)">', video_page_data)
                for video_page_url in video_page_url_list:
                    if video_page_url.find("miaopai.com/show/") >= 0:  # 秒拍
                        video_id = video_page_url.split("/")[-1].split(".")[0]
                        video_url = "http://wsqncdn.miaopai.com/stream/%s.mp4" % video_id
                        video_file_path = os.path.join(video_path, str("%04d" % image_count) + ".mp4")
                        tool.save_image(video_url, video_file_path)
                    elif video_page_url.find("video.weibo.com/show?fid=") >= 0:  # 微博视频
                        print_error_msg(user_name + " 不支持的视频类型：" + video_page_url)
                        break
                    else:  # 其他视频，暂时不支持，收集看看有没有
                        print_error_msg(user_name + " 不支持的视频类型：" + video_page_url)
                        break
                        
            # 图片
            while True:
                photo_page_url = "http://photo.weibo.com/photos/get_all"
                photo_page_url += "?uid=%s&count=%s&page=%s&type=3" % (user_id, IMAGE_COUNT_PER_PAGE, page_count)
                trace(user_name + "相册专辑地址：" + photo_page_url)
                photo_page_data = visit_weibo(photo_page_url)
                trace(user_name + "返回JSON数据：" + str(photo_page_data))
                try:
                    page = json.loads(photo_page_data)
                except:
                    print_error_msg(user_name + " 返回的图片列表不是一个JSON数据")
                    break

                # 总的图片数
                try:
                    total_image_count = page["data"]["total"]
                except:
                    print_error_msg(user_name + " 在图片列表：" + str(page) + " 中没有找到'total'字段")
                    break

                try:
                    photo_list = page["data"]["photo_list"]
                except:
                    print_error_msg(user_name + " 在图片列表：" + str(page) + " 中没有找到'total'字段" )
                    break

                for image_info in photo_list:
                    if not isinstance(image_info, dict):
                        print_error_msg(user_name + " 'photo_list'：" + str(image_info) + " 不是一个字典")
                        continue
                    if ("pic_name" and "timestamp") in image_info:
                        # 将第一张image的时间戳保存到新id list中
                        if self.user_info[3] == "0":
                            self.user_info[3] = str(image_info["timestamp"])
                        # 检查是否图片时间小于上次的记录
                        if 0 < last_image_time >= image_info["timestamp"]:
                            is_over = True
                            break

                        if "pic_host" in image_info:
                            image_host = str(image_info["pic_host"])
                        else:
                            image_host = ""
                        for try_count in range(1, 6):
                            if image_host == "":
                                image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                            image_url = image_host + "/large/" + str(image_info["pic_name"])
                            if try_count == 1:
                                print_step_msg(user_name + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                            else:
                                print_step_msg(user_name + " 重试下载第" + str(image_count) + "张图片：" + image_url)
                            [image_return_code, image_response] = tool.http_request(image_url)[:2]
                            if image_return_code == 1:
                                md5 = hashlib.md5()
                                md5.update(image_response)
                                md5_digest = md5.hexdigest()
                                # 处理获取的文件为weibo默认获取失败的图片
                                if md5_digest not in ["d29352f3e0f276baaf97740d170467d7", "7bd88df2b5be33e1a79ac91e7d0376b5"]:
                                    file_type = image_url.split(".")[-1]
                                    if file_type.find("/") != -1:
                                        file_type = "jpg"
                                    file_path = os.path.join(image_path, str("%04d" % image_count) + "." + file_type)
                                    # 第一张图片，创建目录
                                    if need_make_download_dir:
                                        if not tool.make_dir(image_path, 0):
                                            print_error_msg(user_name + " 创建图片下载目录： " + image_path + " 失败，程序结束！")
                                            tool.process_exit()
                                        need_make_download_dir = False
                                    save_image(image_response, file_path)
                                    print_step_msg(user_name + " 第" + str(image_count) + "张图片下载成功")
                                    image_count += 1
                                    break
                            if try_count == 5:
                                print_error_msg(user_name + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")
                            image_host = ""
                    else:
                        print_error_msg(user_name + " 在JSON数据：" + str(image_info) + " 中没有找到'pic_name'或'timestamp'字段")

                    # 达到配置文件中的下载数量，结束
                    if 0 < GET_IMAGE_COUNT < image_count:
                        is_over = True
                        break

                if is_over:
                    break

                if (total_image_count / IMAGE_COUNT_PER_PAGE) > (page_count - 1):
                    page_count += 1
                else:
                    # 全部图片下载完毕
                    break

            # 如果有错误且没有发现新的图片，复原旧数据
            if self.user_info[3] == "0" and last_image_time != 0:
                self.user_info[3] = str(last_image_time)

            print_step_msg(user_name + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

            # 排序
            if IS_SORT == 1 and image_count > 1:
                destination_path = os.path.join(IMAGE_DOWNLOAD_PATH, user_name)
                if robot.sort_file(image_path, destination_path, int(self.user_info[2]), 4):
                    print_step_msg(user_name + " 图片从下载目录移动到保存目录成功")
                else:
                    print_error_msg(user_name + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    tool.process_exit()
            self.user_info[2] = str(int(self.user_info[2]) + image_count - 1)

            # 保存最后的信息
            threadLock.acquire()
            tool.write_file("\t".join(self.user_info), NEW_SAVE_DATA_PATH)
            TOTAL_IMAGE_COUNT += image_count - 1
            USER_IDS.remove(user_id)
            threadLock.release()

            print_step_msg(user_name + " 完成")
        except Exception, e:
            print_step_msg(user_name + " 异常")
            print_error_msg(str(e) + "\n" + str(traceback.print_exc()))


if __name__ == "__main__":
    tool.restore_process_status()
    Weibo().main()
