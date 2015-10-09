# -*- coding:utf-8  -*-
'''
Created on 2013-4-8

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


class Instagram(common.Robot):

    def __init__(self):
        super(Instagram, self).__init__()

        common.print_msg("配置文件读取完成")

    def _trace(self, msg):
        common.trace(msg, self.is_show_error, self.trace_log_path)

    def _print_error_msg(self, msg):
        common.print_error_msg(msg, self.is_show_error, self.error_log_path)

    def _print_step_msg(self, msg):
        common.print_step_msg(msg, self.is_show_error, self.step_log_path)

    def main(self):
        start_time = time.time()

        # 图片保存目录
        self._print_step_msg("创建图片根目录：" + self.image_download_path)
        if not common.make_dir(self.image_download_path, 2):
            self._print_error_msg("创建图片根目录：" + self.image_download_path + " 失败，程序结束！")
            common.process_exit()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            common.set_proxy(self.proxy_ip, self.proxy_port, "https")

        # 寻找idlist，如果没有结束进程
        user_id_list = {}
        if os.path.exists(self.user_id_list_file_path):
            user_id_list_file = open(self.user_id_list_file_path, "r")
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            for user_info in all_user_list:
                if len(user_info) < 2:
                    continue
                user_info = user_info.replace("\xef\xbb\xbf", "").replace(" ", "").replace("\n", "")

                user_info_list = user_info.split("\t")
                user_id_list[user_info_list[0]] = user_info_list
        else:
            self._print_error_msg("用户ID存档文件: " + self.user_id_list_file_path + "不存在，程序结束！")
            common.process_exit()
        # 创建临时存档文件
        new_user_id_list_file_path = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        new_user_id_list_file = open(new_user_id_list_file_path, "w")
        new_user_id_list_file.close()
        # 复制处理存档文件
        new_user_id_list = copy.deepcopy(user_id_list)
        for user_account in new_user_id_list:
            # 如果没有初始image count，则为0
            if len(new_user_id_list[user_account]) < 2:
                new_user_id_list[user_account].append("0")
            if new_user_id_list[user_account][1] == '':
                new_user_id_list[user_account][1] = 0
            # 处理上一次image id
            # 需置空存放本次第一张获取的image URL
            if len(new_user_id_list[user_account]) < 3:
                new_user_id_list[user_account].append("")
            else:
                new_user_id_list[user_account][2] = ""

        total_image_count = 0
        # 循环下载每个id
        for user_account in sorted(user_id_list.keys()):
            self._print_step_msg("Account: " + user_account)
            # 初始化数据
            image_id = ""
            image_count = 1
            is_pass = False
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(user_id_list[user_account]) > 2 and user_id_list[user_account][1] != '' and int(user_id_list[user_account][1]) != 0 and user_id_list[user_account][2] != "":
                is_error = True
            else:
                is_error = False
            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.is_sort == 1:
                image_path = self.image_temp_path
            else:
                image_path = self.image_download_path + "\\" + user_account
            if not common.make_dir(image_path, 1):
                self._print_error_msg("创建图片下载目录： " + image_path + " 失败，程序结束！")
                common.process_exit()

            # 图片下载
            while 1:
                if is_pass:
                    break
                if image_id == "":
                    photo_album_url = "https://instagram.com/%s/media" % user_account
                else:
                    photo_album_url = "https://instagram.com/%s/media?max_id=%s" % (user_account, image_id)
                photo_album_page = common.do_get(photo_album_url)
                if not photo_album_page:
                    self._print_error_msg("无法获取相册信息: " + photo_album_url)
                    break
                photo_album_data = common.do_get(photo_album_url)
                try:
                    photo_album_page = json.read(photo_album_data)
                except:
                    self._print_error_msg("返回信息：" + str(photo_album_data) + " 不是一个JSON数据, user id: " + str(user_account))
                    break
                if not isinstance(photo_album_page, dict):
                    self._print_error_msg("JSON数据：" + str(photo_album_page) + " 不是一个字典, user id: " + str(user_account))
                    break
                if not photo_album_page.has_key("items"):
                    self._print_error_msg("在JSON数据：" + str(photo_album_page) + " 中没有找到'items'字段, user id: " + str(user_account))
                    break
                # 下载到了最后一张图了
                if photo_album_page["items"] is []:
                    break
                for photo_info in photo_album_page["items"]:
                    if not photo_info.has_key("images"):
                        self._print_error_msg("在JSON数据：" + str(photo_info) + " 中没有找到'images'字段, user id: " + str(user_account))
                        break
                    if not photo_info.has_key("id"):
                        self._print_error_msg("在JSON数据：" + str(photo_info) + " 中没有找到'id'字段, user id: " + str(user_account))
                        break
                    else:
                        image_id = photo_info["id"]
                    # 将第一张image的id保存到新id list中
                    if new_user_id_list[user_account][2] == "":
                        new_user_id_list[user_account][2] = image_id
                    # 检查是否已下载到前一次的图片
                    if len(user_id_list[user_account]) >= 3 and user_id_list[user_account][2].find("_") != -1:
                        if image_id == user_id_list[user_account][2]:
                            is_pass = True
                            is_error = False
                            break
                    if not photo_info["images"].has_key("standard_resolution"):
                        self._print_error_msg("在JSON数据：" + str(photo_info["images"]) + " 中没有找到'standard_resolution'字段, user id: " + str(user_account) + ", image id: " + image_id)
                        break
                    if not photo_info["images"]["standard_resolution"].has_key("url"):
                        self._print_error_msg("在JSON数据：" + str(photo_info["images"]["standard_resolution"]) + " 中没有找到'url'字段, user id: " + str(user_account) + ", image id: " + image_id)
                        break
                    image_url = photo_info["images"]["standard_resolution"]["url"]
                    self._print_step_msg("开始下载第 " + str(image_count) + "张图片：" + image_url)
                    imgByte = common.do_get(image_url)
                    if imgByte:
                        # 文件类型
                        file_type = image_url.split(".")[-1]
                        # 保存图片
                        image_file = open(image_path + "\\" + str("%04d" % image_count) + "." + file_type, "wb")
                        image_file.write(imgByte)
                        self._print_step_msg("下载成功")
                        image_file.close()
                        image_count += 1
                    else:
                        self._print_error_msg("获取第" + str(image_count) + "张图片信息失败：" + str(user_account) + "，" + image_url)

                    # 达到配置文件中的下载数量，结束
                    if len(user_id_list[user_account]) >= 3 and user_id_list[user_account][2] != '' and self.get_image_count > 0 and image_count > self.get_image_count:
                        is_pass = True
                        break
            self._print_step_msg(user_account + "下载完毕，总共获得" + str(image_count - 1) + "张图片")
            new_user_id_list[user_account][1] = str(int(new_user_id_list[user_account][1]) + image_count - 1)
            total_image_count += image_count - 1
            
            # 排序
            if self.is_sort == 1:
                image_list = sorted(os.listdir(image_path), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(image_list) >= 1:
                    destination_path = self.image_download_path + "\\" + user_account
                    if not common.make_dir(destination_path, 1):
                        self._print_error_msg("创建图片子目录： " + destination_path + " 失败，程序结束！")
                        common.process_exit()

                    # 倒叙排列
                    if len(user_id_list[user_account]) >= 2 and user_id_list[user_account][1] != '':
                        count = int(user_id_list[user_account][1]) + 1
                    else:
                        count = 1
                    for file_name in image_list:
                        file_type = file_name.split(".")[1]
                        common.copy_files(image_path + "\\" + file_name, destination_path + "\\" + str("%04d" % count) + "." + file_type)
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
    Instagram().main()
