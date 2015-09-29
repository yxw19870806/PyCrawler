# -*- coding:UTF-8  -*-
'''
Created on 2014-5-31

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common, json
import copy
import os
import shutil
import time


class Twitter(common.Tool):

    def __init__(self):
        super(Twitter, self).__init__()
        self.print_msg("配置文件读取完成")

    def _trace(self, msg):
        super(Twitter, self).trace(msg, self.is_show_error, self.trace_log_path)

    def _print_error_msg(self, msg):
        super(Twitter, self).print_error_msg(msg, self.is_show_error, self.error_log_path)

    def _print_step_msg(self, msg):
        super(Twitter, self).print_step_msg(msg, self.is_show_error, self.step_log_path)

    def main(self, user_id_list_file_path = '', image_download_path = '', image_temp_path = ''):
        start_time = time.time()

        if user_id_list_file_path != '':
            self.user_id_list_file_path = user_id_list_file_path
        if image_download_path != '':
            self.image_download_path = image_download_path
        if image_temp_path != '':
            self.image_temp_path = image_temp_path

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.image_download_path)
        if not self.make_dir(self.image_download_path, 2):
            self._print_error_msg("创建图片根目录：" + self.image_download_path + " 失败，程序结束！")
            self.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            self.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.user_id_list_file_path):
            user_id_list_file = open(self.user_id_list_file_path, "r")
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            for user_info in all_user_list:
                if len(user_info) < 3:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "")
                user_info = user_info.replace(" ", "")
                user_info = user_info.replace("\n", "")
                user_info_list = user_info.split("\t")
                user_id_list[user_info_list[0]] = user_info_list
        else:
            self._print_error_msg("用户ID存档文件: " + self.user_id_list_file_path + "不存在，程序结束！")
            self.process_exit()

        # 创建临时存档文件
        new_user_id_list_file_path = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        new_user_id_list_file = open(new_user_id_list_file_path, "w")
        new_user_id_list_file.close()
        # 复制处理存档文件
        new_user_id_list = copy.deepcopy(user_id_list)
        for user_account in new_user_id_list:
            # 如果没有数量，则为0
            if len(new_user_id_list[user_account]) < 2:
                new_user_id_list[user_account].append("0")
            if new_user_id_list[user_account][1] == '':
                new_user_id_list[user_account][1] = 0
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(new_user_id_list[user_account]) < 3:
                new_user_id_list[user_account].append("")
            else:
                new_user_id_list[user_account][2] = ""
        
        init_max_id = 999999999999999999
        total_image_count = 0
        # 循环下载每个id
        for user_account in sorted(user_id_list.keys()):
            self._print_step_msg("Account: " + user_account)
            # 初始化数据
            data_tweet_id = init_max_id
            image_count = 1
            image_url_list = []
            is_pass = False
            is_last_page = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(user_id_list[user_account]) > 2 and user_id_list[user_account][1] != '' and int(user_id_list[user_account][1]) != 0:
                is_error = True
            else:
                is_error = False
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.is_sort == 1:
                image_path = self.image_temp_path
            else:
                image_path = self.image_download_path + "\\" + user_account
            if not self.make_dir(image_path, 1):
                self._print_error_msg("创建图片下载目录： " + image_path + " 失败，程序结束！")
                self.process_exit()

            # 图片下载
            while not is_last_page:
                if is_pass:
                    break
                photo_page_url = "https://twitter.com/i/profiles/show/%s/media_timeline?include_available_features=1&include_entities=1&max_position=%s" % (user_account, data_tweet_id)
                photo_page_data = self.do_get(photo_page_url)
                if not photo_page_data:
                    self._print_error_msg("无法获取相册信息: " + photo_page_url)
                    break
                try:
                    page = json.read(photo_page_data)
                except:
                    self._print_error_msg("返回信息：" + str(photo_page_data) + " 不是一个JSON数据, account: " + user_account)
                    break

                if not isinstance(page, dict):
                    self._print_error_msg("JSON数据：" + str(page) + " 不是一个字典, account: " + user_account)
                    break
                if not page.has_key("has_more_items"):
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'has_more_items'字段, account: " + user_account)
                    break
                if not page['has_more_items']:
                    is_last_page = True
                if page.has_key("items_html") is False:
                    self._print_error_msg("在JSON数据：" + str(page) + " 中没有找到'items_html'字段, account: " + user_account)
                    break

                page = page['items_html']

                image_index = page.find("data-url")
                while image_index != -1:
                    image_start = page.find("http", image_index)
                    image_stop = page.find('"', image_start)
                    image_url = page[image_start:image_stop].encode("utf-8")
                    if image_url.find('&quot') != -1:
                        image_url = image_url[:image_url.find('&quot')]
                    self._trace("image URL:" + image_url)
                    # 将第一张image的URL保存到新id list中
                    if new_user_id_list[user_account][2] == "":
                        new_user_id_list[user_account][2] = image_url
                    # 检查是否已下载到前一次的图片
                    if len(user_id_list[user_account]) >= 3:
                        if image_url == user_id_list[user_account][2]:
                            is_pass = True
                            is_error = False
                            break
                    if image_url in image_url_list:
                        image_index = page.find('data-url', image_index + 1)
                        continue
                    image_url_list.append(image_url)
                    self._print_step_msg("开始下载第 " + str(image_count) + "张图片：" + image_url)
                    img_byte = self.do_get(image_url)
                    if img_byte:
                        # 文件类型
                        file_type = image_url.split(".")[-1].split(':')[0]
                        # 保存图片
                        image_file = open(image_path + "\\" + str("%04d" % image_count) + "." + file_type, "wb")
                        image_file.write(img_byte)
                        self._print_step_msg("下载成功")
                        image_file.close()
                        image_count += 1
                    else:
                        self._print_error_msg("获取第" + str(image_count) + "张图片信息失败：" + user_account + "：" + image_url)

                    # 达到配置文件中的下载数量，结束
                    if len(user_id_list[user_account]) >= 3 and user_id_list[user_account][2] != '' and self.get_image_count > 0 and image_count > self.get_image_count:
                        is_pass = True
                        break
                    image_index = page.find('data-url', image_index + 1)

                if not is_last_page:
                    # 设置最后一张的data-tweet-id
                    data_tweet_id_index = page.find('data-tweet-id="')
                    while data_tweet_id_index != -1:
                        data_tweet_id_start = page.find('"', data_tweet_id_index)
                        data_tweet_id_stop = page.find('"', data_tweet_id_start + 1)
                        data_tweet_id = page[data_tweet_id_start + 1:data_tweet_id_stop]
                        data_tweet_id_index = page.find('data-tweet-id="', data_tweet_id_index + 1)

            self._print_step_msg(user_account + "下载完毕，总共获得" + str(image_count - 1) + "张图片")
            new_user_id_list[user_account][1] = str(int(new_user_id_list[user_account][1]) + image_count - 1)
            total_image_count += image_count - 1
            
            # 排序
            if self.is_sort == 1:
                image_list = sorted(os.listdir(image_path), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(image_list) >= 1:
                    destination_path = self.image_download_path + "\\" + user_account
                    if not self.make_dir(destination_path, 1):
                        self._print_error_msg("创建图片子目录： " + destination_path + " 失败，程序结束！")
                        self.process_exit()

                    # 倒叙排列
                    if len(user_id_list[user_account]) >= 2 and user_id_list[user_account][1] != '':
                        count = int(user_id_list[user_account][1]) + 1
                    else:
                        count = 1
                    for file_name in image_list:
                        file_type = file_name.split(".")[1]
                        self.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)
                        count += 1
                    self._print_step_msg("图片从下载目录移动到保存目录成功")
                # 删除临时文件夹
                shutil.rmtree(image_path, True)

            if is_error:
                self._print_error_msg(user_account + "图片数量异常，请手动检查")

            # 保存最后的信息
            new_user_id_list_file = open(new_user_id_list_file_path, "a")
            new_user_id_list_file.write("\t".join(new_user_id_list[user_account]) + "\n")
            new_user_id_list_file.close()

        stop_time = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(total_image_count) + "张")

if __name__ == "__main__":
    Twitter().main(os.getcwd() + "\\info\\idlist_1.txt", os.getcwd() +  "\\photo\\twitter1", os.getcwd() +  "\\photo\\twitter1\\tempImage")
    Twitter().main(os.getcwd() + "\\info\\idlist_2.txt", os.getcwd() +  "\\photo\\twitter2", os.getcwd() +  "\\photo\\twitter2\\tempImage")
    Twitter().main(os.getcwd() + "\\info\\idlist_3.txt", os.getcwd() +  "\\photo\\twitter3", os.getcwd() +  "\\photo\\twitter3\\tempImage")
