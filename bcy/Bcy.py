# -*- coding:UTF-8  -*-
'''
Created on 2015-6-23

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

import copy
import os
import re
import time

from common import common, json


class Bcy(common.Robot):

    def __init__(self):
        super(Bcy, self).__init__()

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
        if self.is_proxy == 1:
            common.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 设置系统cookies
        if not common.set_cookie(self.cookie_path, self.browser_version):
            self._print_error_msg("导入浏览器cookies失败，程序结束！")
            common.process_exit()

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
            common.process_exit()

        # 创建临时存档文件
        new_user_id_list_file_path = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        new_user_id_list_file = open(new_user_id_list_file_path, "w")
        new_user_id_list_file.close()

        # 复制处理存档文件
        new_user_id_list = copy.deepcopy(user_id_list)
        for user_id in new_user_id_list:
            # 如果没有数量，则为0
            if len(new_user_id_list[user_id]) < 2:
                new_user_id_list[user_id].append("0")
            if new_user_id_list[user_id][1] == '':
                new_user_id_list[user_id][1] = 0
            # 处理上一次image URL
            # 需置空存放本次第一张获取的image URL
            if len(new_user_id_list[user_id]) < 3:
                new_user_id_list[user_id].append("")
            else:
                new_user_id_list[user_id][2] = ""

        total_image_count = 0
        # 循环下载每个id
        for user_id in sorted(user_id_list.keys()):
            if len(user_id_list[user_id]) >= 2 and user_id_list[user_id][1] != '':
                cn = user_id_list[user_id][1]
            else:
                cn = user_id
            self._print_step_msg("CN: " + cn)
            cp_id = int(user_id) - 100876
            page_count = 1
            max_page_count = -1
            need_make_download_dir = True
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if len(user_id_list[user_id]) > 3 and user_id_list[user_id][2] != '':
                is_error = True
            else:
                is_error = False
            is_pass = False

            while 1:
                photo_album_url = 'http://bcy.net/coser/ajaxShowMore?type=all&cp_id=%s&p=%s' % (cp_id, page_count)
                photo_album_page = common.do_get(photo_album_url)

                try:
                    photo_album_page = json.read(photo_album_page)
                except:
                    self._print_error_msg("返回信息不是一个JSON数据, user id: " + str(user_id))
                    break

                # 总共多少页
                if max_page_count == -1:
                    try:
                        max_page_data = photo_album_page['data']['page']
                    except:
                        self._print_error_msg("在JSON数据：" + str(photo_album_page) + " 中没有找到'page'字段, user id: " + str(user_id))
                        break
                    if not max_page_data:
                        max_page_count = 1
                    else:
                        page_list = re.findall(u'<a href=\\"\\/coser\\/ajaxShowMore\?type=all&cp_id=' + str(cp_id) + '&p=(\d)', max_page_data)
                        max_page_count = int(max(page_list))

                try:
                    photo_album_page_data = photo_album_page['data']['data']
                except:
                    self._print_error_msg("在JSON数据：" + str(photo_album_page) + " 中没有找到'data'字段, user id: " + str(user_id))
                    break

                for data in photo_album_page_data:
                    try:
                        rp_id = data['rp_id']
                        title = data['title'].encode('utf-8').strip()
                        # 过滤一些无法作为文件夹路径的符号
                        filter_list = [':', '\\', '/', '.', '*', '?', '"', '<', '>', '|']
                        for filter_char in filter_list:
                            title.replace(filter_char, '')
                    except:
                        self._print_error_msg("在JSON数据：" + str(data) + " 中没有找到'ur_id'或'title'字段, user id: " + str(user_id))
                        break

                    if new_user_id_list[user_id][2] == "":
                        new_user_id_list[user_id][2] = rp_id
                    # 检查是否已下载到前一次的图片
                    if len(user_id_list[user_id]) >= 3:
                        if int(rp_id) <= int(user_id_list[user_id][2]):
                            is_error = False
                            is_pass = True
                            break

                    self._print_step_msg("rp: " + rp_id)

                    # CN目录
                    image_path = self.image_download_path + "\\" + cn

                    if need_make_download_dir:
                        if not common.make_dir(image_path, 1):
                            self._print_error_msg("创建CN目录： " + image_path + " 失败，程序结束！")
                            common.process_exit()
                        need_make_download_dir = False

                    # 正片目录
                    if title != '':
                        rp_path = image_path + "\\" + rp_id + ' ' + title
                    else:
                        rp_path = image_path + "\\" + rp_id
                    if not common.make_dir(rp_path, 1):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        self._print_error_msg("创建正片目录： " + rp_path + " 失败，尝试不使用title！")
                        rp_path = image_path + "\\" + rp_id
                        if not common.make_dir(rp_path, 1):
                            self._print_error_msg("创建正片目录： " + rp_path + " 失败，程序结束！")
                            common.process_exit()

                    rp_url = 'http://bcy.net/coser/detail/%s/%s' % (cp_id, rp_id)
                    rp_page = common.do_get(rp_url)
                    if rp_page:
                        image_count = 0
                        image_index = rp_page.find("src='")
                        while image_index != -1:
                            imageStart = rp_page.find("http", image_index)
                            imageStop = rp_page.find("'", imageStart)
                            image_url = rp_page[imageStart:imageStop]
                            # 禁用指定分辨率
                            image_url = "/".join(image_url.split("/")[0:-1])
                            image_count += 1
                            self._print_step_msg("开始下载第" + str(image_count) + "张图片：" + image_url)
                            if image_url.rfind('/') < image_url.rfind('.'):
                                file_type = image_url.split(".")[-1]
                            else:
                                file_type = 'jpg'
                            if common.save_image(image_url, rp_path + "\\" + str("%03d" % image_count) + "." + file_type):
                                self._print_step_msg("下载成功")
                            image_index = rp_page.find("src='", image_index + 1)
                        if image_count == 0:
                            self._print_error_msg(cn + ": " + rp_id + " 没有任何图片")
                        total_image_count += image_count
                if is_pass:
                    break
                if page_count >= max_page_count:
                    break
                page_count += 1

            self._print_step_msg(cn + "下载完毕")

            if is_error:
                self._print_error_msg(user_id + "图片数量异常，请手动检查")

            # 保存最后的信息
            new_user_id_list_file = open(new_user_id_list_file_path, "a")
            new_user_id_list_file.write("\t".join(new_user_id_list[user_id]) + "\n")
            new_user_id_list_file.close()

        stop_time = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(total_image_count) + "张")

if __name__ == "__main__":
    Bcy().main()
