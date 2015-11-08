# -*- coding:UTF-8  -*-
'''
Created on 2014-2-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common
from common import BeautifulSoup
import os
import time


class Fkoji(common.Robot):

    def __init__(self):
        super(Fkoji, self).__init__()

        self.user_id_list_file_path = os.getcwd() + "\\fkoji.save"

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

        # 图片下载临时目录
        if self.is_sort == 1:
            self._print_step_msg("创建图片下载目录：" + self.image_temp_path)
            if not common.make_dir(self.image_temp_path, 2):
                self._print_error_msg("创建图片下载目录：" + self.image_temp_path + " 失败，程序结束！")
                common.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            common.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 寻找fkoji.save，如果没有结束进程
        last_image_url = ""
        image_start_index = 0
        user_id_list = {}
        if os.path.exists(self.user_id_list_file_path):
            user_id_list_file = open(self.user_id_list_file_path, "r")
            all_user_list = user_id_list_file.readlines()
            user_id_list_file.close()
            if len(all_user_list) >= 1:
                info = all_user_list[0].split("\t")
                if len(info) >= 2:
                    image_start_index = int(info[0])
                    last_image_url = info[1].replace("\xef\xbb\xbf", "").replace("\n", "").replace(" ", "")

                for user_info in all_user_list[1:]:
                    user_info = user_info.replace(" ", "").replace("\n", "").replace("\r", "")
                    user_info_list = user_info.split("\t")
                    if len(user_info_list) >= 2:
                        user_id_list[user_info_list[0]] = user_info_list[1]

        # 下载
        url = "http://jigadori.fkoji.com/?p=%s"
        page_index = 1
        image_count = 1
        new_last_image_url = ""
        image_url_list = []
        if self.is_sort == 1:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path
        is_over = False

        while 1:
            index_url = url % str(page_index)
            self._trace("网页地址：" + index_url)

            index_page = common.http_request(index_url)
            index_page = BeautifulSoup.BeautifulSoup(index_page)
     
            photo_list = index_page.body.findAll("div", "photo")
            # 已经下载到最后一页
            if not photo_list:
                break
            for photo_info in photo_list:
                if isinstance(photo_info, BeautifulSoup.NavigableString):
                    continue
                tags = photo_info.findAll("span")
                # 找user_id
                for tag in tags:
                    sub_tag = tag.next.next
                    if isinstance(sub_tag, BeautifulSoup.NavigableString):
                        if sub_tag.find("@") == 0:
                            user_id = sub_tag[1:].encode("GBK")
                # 找图片
                tags = photo_info.findAll("img")
                for tag in tags:
                    tag_attr = dict(tag.attrs)
                    if tag_attr.has_key("src") and tag_attr.has_key("alt"):
                        image_url = str(tag_attr["src"]).replace(" ", "").encode("GBK")
                        if new_last_image_url == "":
                            new_last_image_url = image_url
                        # 检查是否已下载到前一次的图片
                        if last_image_url == image_url:
                            is_over = True
                            break
                        self._trace("id: " + user_id + "，地址: " + image_url)
                        if image_url in image_url_list:
                            continue
                        # 文件类型
                        file_type = image_url.split(".")[-1]
                        if file_type.find('/') != -1:
                            file_type = 'jpg'
                        image_file = open(image_path + "\\" + str("%05d" % image_count) + "_" + str(user_id) + "." + file_type, "wb")
                        self._print_step_msg("开始下载第" + str(image_count) + "张图片：" + image_url)
                        img_byte = common.http_request(image_url, None, False)
                        if img_byte:
                            image_file.write(img_byte)
                            self._print_step_msg("下载成功")
                        else:
                            self._print_error_msg("获取图片" + str(image_count) + "信息失败：" + image_url)
                        image_file.close()
                        image_count += 1
                if is_over:
                    break
            if is_over:
                break
            page_index += 1

        self._print_step_msg("下载完毕")

        # 排序复制到保存目录
        if self.is_sort == 1:
            is_check_ok = False
            while not is_check_ok:
                # 等待手动检测所有图片结束
                input_str = raw_input(common.get_time() + " 已经下载完毕，是否下一步操作？ (Y)es or (N)o: ")
                try:
                    input_str = input_str.lower()
                    if input_str in ["y", "yes"]:
                        is_check_ok = True
                    elif input_str in ["n", "no"]:
                        common.process_exit()
                except:
                    pass
            if not common.make_dir(self.image_download_path + "\\all", 1):
                self._print_error_msg("创建目录：" + self.image_download_path + "\\all" + " 失败，程序结束！")
                common.process_exit()

            file_list = common.get_dir_files_name(self.image_temp_path, 'desc')
            for file_name in file_list:
                image_path = self.image_temp_path + "\\" + file_name
                file_name_list = file_name.split(".")
                file_type = file_name_list[-1]
                user_id = "_".join(".".join(file_name_list[:-1]).split("_")[1:])

                # 所有
                image_start_index += 1
                common.copy_files(image_path, self.image_download_path + "\\all\\" + str("%05d" % image_start_index) + "_" + user_id + "." + file_type)

                # 单个
                each_user_path = self.image_download_path + "\\single\\" + user_id
                if not os.path.exists(each_user_path):
                    if not common.make_dir(each_user_path, 1):
                        self._print_error_msg("创建目录：" + each_user_path + " 失败，程序结束！")
                        common.process_exit()
                if user_id_list.has_key(user_id):
                    user_id_list[user_id] = int(user_id_list[user_id]) + 1
                else:
                    user_id_list[user_id] = 1
                common.copy_files(image_path, each_user_path + "\\" + str("%05d" % user_id_list[user_id]) + "." + file_type)

            self._print_step_msg("图片从下载目录移动到保存目录成功")

            # 删除临时文件夹
            common.remove_dir(image_path)
            
        # 保存新的存档文件
        new_save_file_path = os.getcwd() + "\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        self._print_step_msg("保存新存档文件: " + new_save_file_path)
        new_save_file = open(new_save_file_path, "w")
        new_save_file.write(str(image_start_index) + "\t" + new_last_image_url + "\n")
        temp_list = []
        for user_id in sorted(user_id_list.keys()):
            temp_list.append(user_id + "\t" + str(user_id_list[user_id]))
        new_user_id_list_string = "\n".join(temp_list)
        new_save_file.write(new_user_id_list_string)
        new_save_file.close()

        stop_time = time.time()
        self._print_step_msg("成功下载最新图片，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(image_count - 1) + "张")


if __name__ == "__main__":
    Fkoji().main()
