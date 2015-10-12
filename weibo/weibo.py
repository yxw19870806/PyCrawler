# -*- coding:UTF-8  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json
import hashlib
# import multiprocessing
import os
import random
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


class Weibo(common.Robot):

    def __init__(self, user_id_list_file_path='', image_download_path='', image_temp_path=''):
        global IMAGE_COUNT_PER_PAGE
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_USER_ID_LIST_FILE_PATH
        global IS_SORT
        global IS_TRACE
        global IS_SHOW_ERROR
        global IS_SHOW_STEP
        global TRACE_LOG_PATH
        global ERROR_LOG_PATH
        global STEP_LOG_PATH

        # multiprocessing.Process.__init__(self)
        common.Robot.__init__(self)

        if user_id_list_file_path != '':
            self.user_id_list_file_path = user_id_list_file_path

        IMAGE_COUNT_PER_PAGE = 20  # 每次请求获取的图片数量
        GET_IMAGE_COUNT = self.get_image_count
        if image_temp_path != '':
            IMAGE_TEMP_PATH = image_temp_path
        else:
            IMAGE_TEMP_PATH = self.image_temp_path
        if image_download_path != '':
            IMAGE_DOWNLOAD_PATH = image_download_path
        else:
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
        print_step_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH)
        if not common.make_dir(IMAGE_DOWNLOAD_PATH, 2):
            print_error_msg("创建图片根目录：" + IMAGE_DOWNLOAD_PATH + " 失败，程序结束！")
            common.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            common.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not common.set_cookie(self.cookie_path, self.browser_version):
            print_error_msg("导入浏览器cookies失败，程序结束！")
            common.process_exit()

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.user_id_list_file_path):
            user_id_list_file = open(self.user_id_list_file_path, 'r')
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            for user_info in all_user_list:
                if len(user_info) < 5:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "").replace(" ", "").replace("\n", "").replace("\r", "")
                user_info_list = user_info.split("\t")

                user_id = user_info_list[0]
                user_id_list[user_id] = user_info_list
                # 如果没有名字，则名字用uid代替
                if len(user_id_list[user_id]) < 2:
                    user_id_list[user_id].append(user_id)
                if user_id_list[user_id][1] == '':
                    user_id_list[user_id][1] = user_id
                # 如果没有数量，则为0
                if len(user_id_list[user_id]) < 3:
                    user_id_list[user_id].append("0")
                if user_id_list[user_id][2] == '':
                    user_id_list[user_id][2] = '0'
                # 处理上一次image URL
                if len(user_id_list[user_id]) < 4:
                    user_id_list[user_id].append("")
        else:
            print_error_msg("用户ID存档文件：" + self.user_id_list_file_path + "不存在，程序结束！")
            common.process_exit()

        # 创建临时存档文件
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, 'w')
        new_user_id_list_file.close()

        TOTAL_IMAGE_COUNT = 0
        for user_id in sorted(user_id_list.keys()):
            # 检查正在运行的线程数
            while THREAD_COUNT >= self.thread_count:
                time.sleep(10)

            # 线程数+1
            threadLock.acquire()
            THREAD_COUNT += 1
            threadLock.release()

            # 开始下载
            thread = Download(user_id_list[user_id])
            thread.start()

        # 检查所有线程是不是全部结束了
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

    def _visit(self, url):
        temp_page = common.do_get(url)
        if temp_page:
            redirect_url_index = temp_page.find("location.replace")
            if redirect_url_index != -1:
                redirect_url_start = temp_page.find("'", redirect_url_index) + 1
                redirect_url_stop = temp_page.find("'", redirect_url_start)
                redirect_url = temp_page[redirect_url_start:redirect_url_stop]
                return str(common.do_get(redirect_url))
            elif temp_page.find("用户名或密码错误") != -1:
                print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                common.process_exit()
            else:
                try:
                    temp_page = temp_page.decode("utf-8")
                    if temp_page.find("用户名或密码错误") != -1:
                        print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                        common.process_exit()
                except Exception, e:
                    pass
                return str(temp_page)
        return False

    def run(self):
        global IMAGE_COUNT_PER_PAGE
        global GET_IMAGE_COUNT
        global IMAGE_TEMP_PATH
        global IMAGE_DOWNLOAD_PATH
        global NEW_USER_ID_LIST_FILE_PATH
        global TOTAL_IMAGE_COUNT
        global THREAD_COUNT

        user_id = self.user_info[0]
        user_name = self.user_info[1]

        print_step_msg(user_name + " 开始")

        # 初始化数据
        last_image_url = self.user_info[3]
        self.user_info[3] = ''  # 置空，存放此次的最后URL
        # 为防止前一次的记录图片被删除，根据历史图片总数给一个单次下载的数量限制
        if last_image_url == '':
            limit_download_count = 0
        else:
            # 历史总数的10%，下线50、上限300
            limit_download_count = min(max(50, int(self.user_info[2]) / 100 * 10), 300)
        page_count = 1
        image_count = 1
        is_over = False
        # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
        if last_image_url == '':
            is_error = False
        else:
            is_error = True

        # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
        if IS_SORT == 1:
            image_path = IMAGE_TEMP_PATH + "\\" + user_name
        else:
            image_path = IMAGE_DOWNLOAD_PATH + "\\" + user_name
        if not common.make_dir(image_path, 1):
            print_error_msg(user_name + " 创建图片下载目录：" + image_path + " 失败，程序结束！")
            common.process_exit()

        # 日志文件插入信息
        while 1:
            photo_album_url = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (user_id, IMAGE_COUNT_PER_PAGE, page_count)
            trace("相册专辑地址：" + photo_album_url)
            photo_page_data = self._visit(photo_album_url)
            trace("返回JSON数据：" + photo_page_data)
            try:
                page = json.read(photo_page_data)
            except:
                print_error_msg(user_name + " 返回信息不是一个JSON数据")
                break

            # 总的图片数
            try:
                total_image_count = page["data"]["total"]
            except:
                print_error_msg(user_name + " 在JSON数据：" + str(page) + " 中没有找到'total'字段")
                break

            try:
                photo_list = page["data"]["photo_list"]
            except:
                print_error_msg(user_name + " 在JSON数据：" + str(page) + " 中没有找到'total'字段" )
                break

            for image_info in photo_list:
                if not isinstance(image_info, dict):
                    print_error_msg(user_name + " JSON数据['photo_list']：" + str(image_info) + " 不是一个字典")
                    continue
                if image_info.has_key("pic_name"):
                    # 将第一张image的URL保存到新id list中
                    if self.user_info[3] == "":
                        self.user_info[3] = image_info["pic_name"]
                    # 检查是否已下载到前一次的图片
                    if image_info["pic_name"] == last_image_url:
                        is_over = True
                        is_error = False
                        break

                    if image_info.has_key("pic_host"):
                        image_host = image_info["pic_host"]
                    else:
                        image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                    try_count = 0
                    while True:
                        # 如果是第二次获取图片的话，试试换个域名
                        if try_count > 1:
                            image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                        image_url = image_host + "/large/" + image_info["pic_name"]

                        if try_count == 0:
                            print_step_msg(user_name + " 开始下载第" + str(image_count) + "张图片：" + image_url)
                        else:
                            print_step_msg(user_name + " 重试下载第" + str(image_count) + "张图片：" + image_url)

                        img_byte = common.do_get(image_url)
                        if img_byte:
                            md5_digest = hashlib.md5()
                            md5_digest.update(img_byte)
                            md5_digest.hexdigest()
                            # 处理获取的文件为weibo默认获取失败的图片
                            if md5_digest in ['d29352f3e0f276baaf97740d170467d7', '7bd88df2b5be33e1a79ac91e7d0376b5']:
                                print_step_msg(user_name + " 源文件获取失败，重试")
                            else:
                                file_type = image_url.split(".")[-1]
                                if file_type.find('/') != -1:
                                    file_type = 'jpg'
                                file_path = common.change_path_encoding(image_path + "\\" + str("%04d" % image_count) + "." + file_type)
                                image_file = open(file_path, "wb")
                                image_file.write(img_byte)
                                image_file.close()
                                print_step_msg(user_name + " 第" + str(image_count) + "张图片下载成功")
                                image_count += 1
                            break
                        else:
                            try_count += 1

                        if try_count >= 5:
                            print_error_msg(user_name + " 第" + str(image_count) + "张图片 " + image_url + " 下载失败")
                            break

                else:
                    print_error_msg(user_name + " 在JSON数据：" + str(image_info) + " 中没有找到'pic_name'字段")

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

            if total_image_count / IMAGE_COUNT_PER_PAGE > page_count - 1:
                page_count += 1
            else:
                # 全部图片下载完毕
                break

        print_step_msg(user_name + " 下载完毕，总共获得" + str(image_count - 1) + "张图片")

        # 排序
        if IS_SORT == 1:
            image_list = common.get_dir_files_name(image_path, 'desc')
            # 判断排序目标文件夹是否存在
            if len(image_list) >= 1:
                destination_path = IMAGE_DOWNLOAD_PATH + "\\" + user_name
                if not common.make_dir(destination_path, 1):
                    print_error_msg(user_name + " 创建图片子目录： " + destination_path + " 失败，程序结束！")
                    common.process_exit()

                # 倒叙排列
                count = int(self.user_info[2])

                for file_name in image_list:
                    count += 1
                    file_type = file_name.split(".")[1]
                    common.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)

                print_step_msg(user_name + " 图片从下载目录移动到保存目录成功")
            # 删除临时文件夹
            common.remove_dir(image_path)

        self.user_info[2] = str(int(self.user_info[2]) + image_count - 1)

        if is_error:
            print_error_msg(user_name + " 图片数量异常，请手动检查")

        # 保存最后的信息
        threadLock.acquire()
        new_user_id_list_file = open(NEW_USER_ID_LIST_FILE_PATH, "a")
        new_user_id_list_file.write("\t".join(self.user_info) + "\n")
        new_user_id_list_file.close()
        TOTAL_IMAGE_COUNT += image_count - 1
        THREAD_COUNT -= 1
        threadLock.release()

        print_step_msg(user_name + " 完成")


if __name__ == '__main__':
    Weibo(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\weibo1", os.getcwd() +  "\\photo\\weibo1\\tempImage").main()
    Weibo(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\weibo2", os.getcwd() +  "\\photo\\weibo2\\tempImage").main()
    Weibo(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\weibo3", os.getcwd() +  "\\photo\\weibo3\\tempImage").main()
    Weibo(os.getcwd() + "\\info\\idlist_4.txt", os.getcwd() +  "\\photo\\weibo4", os.getcwd() +  "\\photo\\weibo4\\tempImage").main()
