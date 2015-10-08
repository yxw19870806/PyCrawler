# -*- coding:UTF-8  -*-
'''
Created on 2013-8-28

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json

import copy
import hashlib
import os
import random
import threading
import time


class Weibo(common.Robot, threading.Thread):

    def __init__(self, user_id_list_file_path='', image_download_path='', image_temp_path=''):
        threading.Thread.__init__(self)
        common.Robot.__init__(self)

        if user_id_list_file_path != '':
            self.user_id_list_file_path = user_id_list_file_path
        if image_download_path != '':
            self.image_download_path = image_download_path
        if image_temp_path != '':
            self.image_temp_path = image_temp_path

        # 每次请求获取的图片数量
        self.IMAGE_COUNT_PER_PAGE = 20

        common.print_msg("配置文件读取完成")

    def _trace(self, msg):
        common.trace(msg, self.is_trace, self.trace_log_path)

    def _print_error_msg(self, msg):
        common.print_error_msg(msg, self.is_show_error, self.error_log_path)

    def _print_step_msg(self, msg):
        common.print_step_msg(msg, self.is_show_step, self.step_log_path)
        
    def _visit(self, url):
        temp_page = common.do_get(url)
        if temp_page:
            redirect_url_index = temp_page.find("location.replace")
            if redirect_url_index != -1:
                redirect_url_start = temp_page.find("'", redirect_url_index) + 1
                redirect_url_stop = temp_page.find("'", redirect_url_start)
#                 redirectUrlStart = temp_page.find('"', redirect_url_index) + 1
#                 redirectUrlStop = temp_page.find('"', redirectUrlStart)
                redirect_url = temp_page[redirect_url_start:redirect_url_stop]
                return str(common.do_get(redirect_url))
            elif temp_page.find("用户名或密码错误") != -1:
                self._print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                common.process_exit()
            else:
                try:
                    temp_page = temp_page.decode("utf-8")
                    if temp_page.find("用户名或密码错误") != -1:
                        self._print_error_msg("登陆状态异常，请在浏览器中重新登陆微博账号")
                        common.process_exit()
                except Exception, e:
                    pass
                return str(temp_page)
        return False

    def run(self):
        start_time = time.time()

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.image_download_path)
        if not common.make_dir(self.image_download_path, 2):
            self._print_error_msg("创建图片根目录：" + self.image_download_path + " 失败，程序结束！")
            common.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            common.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not common.set_cookie(self.cookie_path, self.browser_version):
            self._print_error_msg("导入浏览器cookies失败，程序结束！")
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
                user_info = user_info.replace("\xef\xbb\xbf", "")
                user_info = user_info.replace(" ", "")
                user_info = user_info.replace("\n", "")
                user_info = user_info.replace("\r", "")
                user_info_list = user_info.split("\t")
                user_id_list[user_info_list[0]] = user_info_list
        else:
            self._print_error_msg("用户ID存档文件：" + self.user_id_list_file_path + "不存在，程序结束！")
            common.process_exit()

        # 创建临时存档文件
        new_user_id_list_file_path = os.getcwd() + "\\info\\" + time.strftime('%Y-%m-%d_%H_%M_%S_', time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        new_user_id_list_file = open(new_user_id_list_file_path, 'w')
        new_user_id_list_file.close()
        # 复制处理存档文件
        new_user_id_list = copy.deepcopy(user_id_list)
        for user_id in new_user_id_list:
            # 如果没有名字，则名字用uid代替
            if len(new_user_id_list[user_id]) < 2:
                new_user_id_list[user_id].append(new_user_id_list[user_id][0])
            # 如果没有初始image count，则为0
            if len(new_user_id_list[user_id]) < 3:
                new_user_id_list[user_id].append("0")
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(new_user_id_list[user_id]) < 4:
                new_user_id_list[user_id].append("")
            else:
                new_user_id_list[user_id][3] = ""
            # 处理成员队伍信息
            if len(new_user_id_list[user_id]) < 5:
                new_user_id_list[user_id].append("")

        total_image_count = 0
        for user_id in sorted(user_id_list.keys()):
            user_name = new_user_id_list[user_id][1]
            self._print_step_msg("UID: " + str(user_id) + "，Name: " + user_name)
            # 初始化数据
            page_count = 1
            image_count = 1
            is_pass = False
            if len(user_id_list[user_id]) <= 3 or user_id_list[user_id][3] == '':
                is_error = False
            else:
                is_error = True

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.is_sort == 1:
                image_path = self.image_temp_path
            else:
                image_path = self.image_download_path + "\\" + user_name
            if not common.make_dir(image_path, 1):
                self._print_error_msg("创建图片下载目录：" + image_path + " 失败，程序结束！")
                common.process_exit()

            # 日志文件插入信息
            while 1:
                photo_album_url = "http://photo.weibo.com/photos/get_all?uid=%s&count=%s&page=%s&type=3" % (user_id, self.IMAGE_COUNT_PER_PAGE, page_count)
                self._trace("相册专辑地址：" + photo_album_url)
                photo_page_data = self._visit(photo_album_url)
                self._trace("返回JSON数据：" + photo_page_data)
                try:
                    page = json.read(photo_page_data)
                except:
                    self._print_error_msg("返回信息不是一个JSON数据, user id: " + str(user_id))
                    break

                # 总的图片数
                try:
                    total_image_count = page["data"]["total"]
                except:
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(user_id))
                    break

                try:
                    photo_list = page["data"]["photo_list"]
                except:
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'total'字段, user id: " + str(user_id))
                    break

                for image_info in photo_list:
                    if not isinstance(image_info, dict):
                        self._print_error_msg("JSON数据['photo_list']：" + str(image_info) + " 不是一个字典, user id: " + str(user_id))
                        continue
                    if image_info.has_key("pic_name"):
                        # 将第一张image的URL保存到新id list中
                        if new_user_id_list[user_id][3] == "":
                            new_user_id_list[user_id][3] = image_info["pic_name"]
                        # 检查是否已下载到前一次的图片
                        if len(user_id_list[user_id]) >= 4:
                            if image_info["pic_name"] == user_id_list[user_id][3]:
                                is_pass = True
                                is_error = False
                                break
                        if image_info.has_key("pic_host"):
                            image_host = image_info["pic_host"]
                        else:
                            image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                        try_count = 0
                        while True:
                            if try_count > 1:
                                image_host = "http://ww%s.sinaimg.cn" % str(random.randint(1, 4))
                            image_url = image_host + "/large/" + image_info["pic_name"]
                            if try_count == 0:
                                self._print_step_msg("开始下载第" + str(image_count) + "张图片：" + image_url)
                            else:
                                self._print_step_msg("重试下载第" + str(image_count) + "张图片：" + image_url)
                            imgByte = common.do_get(image_url)
                            if imgByte:
                                md5Digest = hashlib.md5().update(imgByte).hexdigest()
                                # 处理获取的文件为weibo默认获取失败的图片
                                if md5Digest in ['d29352f3e0f276baaf97740d170467d7', '7bd88df2b5be33e1a79ac91e7d0376b5']:
                                    self._print_step_msg("源文件获取失败，重试")
                                else:
                                    file_type = image_url.split(".")[-1]
                                    if file_type.find('/') != -1:
                                        file_type = 'jpg'
                                    imageFile = open(image_path + "\\" + str("%04d" % image_count) + "." + file_type, "wb")
                                    imageFile.write(imgByte)
                                    self._print_step_msg("下载成功")
                                    imageFile.close()
                                    image_count += 1
                                break
                            else:
                                try_count += 1
                            if try_count >= 5:
                                self._print_error_msg("下载图片失败，用户ID：" + str(user_id) + ", 第" + str(image_count) +  "张，图片地址：" + image_url)
                                break
                            
                    else:
                        self._print_error_msg("在JSON数据：" + str(image_info) + " 中没有找到'pic_name'字段, user id: " + str(user_id))
                           
                    # 达到配置文件中的下载数量，结束
                    if len(user_id_list[user_id]) >= 4 and user_id_list[user_id][3] != '' and self.get_image_count > 0 and image_count > self.get_image_count:
                        is_pass = True
                        break
                if is_pass:
                    break
                if total_image_count / self.IMAGE_COUNT_PER_PAGE > page_count - 1:
                    page_count += 1
                else:
                    # 全部图片下载完毕
                    break
            
            self._print_step_msg(user_name + "下载完毕，总共获得" + str(image_count - 1) + "张图片")
            new_user_id_list[user_id][2] = str(int(new_user_id_list[user_id][2]) + image_count - 1)
            total_image_count += image_count - 1
            
            # 排序
            if self.is_sort == 1:
                image_list = sorted(os.listdir(image_path), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(image_list) >= 1:
                    destination_path = self.image_download_path + "\\" + user_name
                    if not common.make_dir(destination_path, 1):
                        self._print_error_msg("创建图片子目录： " + destination_path + " 失败，程序结束！")
                        common.process_exit()

                    # 倒叙排列
                    if len(user_id_list[user_id]) >= 3:
                        count = int(user_id_list[user_id][2]) + 1
                    else:
                        count = 1
                    for file_name in image_list:
                        file_type = file_name.split(".")[1]
                        common.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)
                        count += 1
                    self._print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                common.remove_dir(image_path)

            if is_error:
                self._print_error_msg(user_name + "图片数量异常，请手动检查")
                
            # 保存最后的信息
            new_user_id_list_file = open(new_user_id_list_file_path, 'a')
            new_user_id_list_file.write("\t".join(new_user_id_list[user_id]) + "\n")
            new_user_id_list_file.close()

        stop_time = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(total_image_count) + "张")

if __name__ == '__main__':
    thread1 = Weibo(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\weibo1", os.getcwd() +  "\\photo\\weibo1\\tempImage")
    thread2 = Weibo(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\weibo2", os.getcwd() +  "\\photo\\weibo2\\tempImage")
    thread3 = Weibo(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\weibo3", os.getcwd() +  "\\photo\\weibo3\\tempImage")
    thread4 = Weibo(os.getcwd() + "\\info\\idlist_4.txt", os.getcwd() +  "\\photo\\weibo4", os.getcwd() +  "\\photo\\weibo4\\tempImage")
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
