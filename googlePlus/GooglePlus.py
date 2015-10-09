# -*- coding:UTF-8  -*-
'''
Created on 2013-4-8

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common
import os
import re
import time


class GooglePlus(common.Robot):

    def __init__(self):
        super(GooglePlus, self).__init__()

        # 单次获取最新的N张照片,G+ 限制最多1000张
        self.ge_image_url_count = 1000

        common.print_msg("配置文件读取完成")

    def _trace(self, msg):
        common.trace(msg, self.is_trace, self.trace_log_path)

    def _print_error_msg(self, msg):
        common.print_error_msg(msg, self.is_show_error, self.error_log_path)

    def _print_step_msg(self, msg):
        common.print_step_msg(msg, self.is_show_step, self.step_log_path)

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
                if len(user_info) < 10:
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
                # 处理成员队伍信息
                if len(user_id_list[user_id]) < 5:
                    user_id_list[user_id].append("")
        else:
            self._print_error_msg("用户ID存档文件: " + self.user_id_list_file_path + "不存在，程序结束！")
            common.process_exit()
        # 创建临时存档文件
        new_user_id_list_file_path = os.getcwd() + "\\info\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        new_user_id_list_file = open(new_user_id_list_file_path, "w")
        new_user_id_list_file.close()

        total_image_count = 0
        # 循环下载每个id
        for user_id in sorted(user_id_list.keys()):
            user_name = user_id_list[user_id][1]
            self._print_step_msg("ID: " + str(user_id) + ", 名字: " + user_name)

            # 初始化数据
            last_image_url = user_id_list[user_id][3]
            user_id_list[user_id][3] = ''  # 置空，存放此次的最后URL
            image_count = 1
            message_url_list = []
            image_url_list = []
            # 如果有存档记录，则直到找到与前一次一致的地址，否则都算有异常
            if last_image_url.find("picasaweb.google.com/") != -1:
                is_error = True
            else:
                is_error = False

            # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
            if self.is_sort == 1:
                image_path = self.image_temp_path
            else:
                image_path = self.image_download_path + "\\" + user_name
            if not common.make_dir(image_path, 1):
                self._print_error_msg("创建图片下载目录： " + image_path + " 失败，程序结束！")
                common.process_exit()

            # 图片下载
#            photo_album_url = "https://plus.google.com/photos/%s/albums/posts?banner=pwa" % (user_id)
            photo_album_url = 'https://plus.google.com/_/photos/pc/read/'
            now = time.time() * 100
            key = ''
            post_data = 'f.req=[["posts",null,null,"synthetic:posts:%s",3,"%s",null],[%s,1,null],"%s",null,null,null,null,null,null,null,2]&at=AObGSAj1ll9iGT-1d05vTuxV5yygWelh9g:%s&' % (user_id, user_id, self.ge_image_url_count, key, now)
            self._trace("信息首页地址：" + photo_album_url)
            photo_album_page = common.do_get(photo_album_url, post_data)
            if photo_album_page:
                message_index = photo_album_page.find('[["https://picasaweb.google.com/' + user_id)
                is_over = False
                while message_index != -1:
                    message_start = photo_album_page.find("http", message_index)
                    message_stop = photo_album_page.find('"', message_start)
                    message_url = photo_album_page[message_start:message_stop]
                    message_url = message_url.replace('\u003d', '=')
                    # 将第一张image的URL保存到新id list中
                    if user_id_list[user_id][3] == '':
                        # 有可能拿到带authkey的，需要去掉
                        # https://picasaweb.google.com/116300481938868290370/2015092603?authkey\u003dGv1sRgCOGLq-jctf-7Ww#6198800191175756402
                        try:
                            temp = re.findall('(.*)\?.*(#.*)', message_url)
                            user_id_list[user_id][3] = temp[0][0] + temp[0][1]
                        except:
                            user_id_list[user_id][3] = message_url

                    # 检查是否已下载到前一次的图片
                    if last_image_url.find("picasaweb.google.com/") != -1:
                        if message_url == last_image_url:
                            is_error = False
                            break
                    self._trace("message URL:" + message_url)
                    # 判断是否重复
                    if message_url in message_url_list:
                        message_index = photo_album_page.find('[["https://picasaweb.google.com/' + user_id, message_index + 1)
                        continue
                    message_url_list.append(message_url)
                    message_page = common.do_get(message_url)
                    if not message_page:
                        self._print_error_msg("无法获取信息页: " + message_url)
                        message_index = photo_album_page.find('[["https://picasaweb.google.com/' + user_id, message_index + 1)
                        continue
                    flag = message_page.find("<div><a href=")
                    while flag != -1:
                        image_index = message_page.find("<img src=", flag, flag + 200)
                        if image_index == -1:
                            self._print_error_msg("信息页：" + message_url + " 中没有找到标签'<img src='")
                            break
                        image_start = message_page.find("http", image_index)
                        image_stop = message_page.find('"', image_start)
                        image_url = message_page[image_start:image_stop]
                        self._trace("image URL:" + image_url)
                        if image_url in image_url_list:
                            flag = message_page.find("<div><a href=", flag + 1)
                            continue
                        image_url_list.append(image_url)
                        # 重组URL并使用最大分辨率
                        # https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/Ic42/s128/16%252520-%2525201.jpg
                        # ->
                        # https://lh3.googleusercontent.com/-WWXEwS_4RlM/Vae0RRNEY_I/AAAAAAAA2j8/VaALVmc7N64/s0-Ic42/16%252520-%2525201.jpg
                        temp_list = image_url.split("/")
                        temp_list[-2] = "s0"
                        image_url = "/".join(temp_list[:-3]) + '/s0-' + temp_list[-3] + '/' + temp_list[-1]
                        self._print_step_msg("开始下载第" + str(image_count) + "张图片：" + image_url)
                        # 文件类型
                        if image_url.rfind('/') < image_url.rfind('.'):
                            file_type = image_url.split(".")[-1]
                        else:
                            file_type = 'jpg'
                        file_name = image_path + "\\" + str("%04d" % image_count) + "." + file_type

                        if common.save_image(image_url, file_name):
                            self._print_step_msg("下载成功")
                            image_count += 1
                        else:
                            self._print_error_msg("获取第" + str(image_count) + "张图片信息失败：" + str(user_id) + ": " + image_url)

                        # 达到配置文件中的下载数量，结束
                        if last_image_url != '' and self.get_image_count > 0 and image_count > self.get_image_count:
                            is_over = True
                            break
                        flag = message_page.find("<div><a href=", flag + 1)
                    if is_over:
                        break
                    message_index = photo_album_page.find('[["https://picasaweb.google.com/' + user_id, message_index + 1)
            else:
                self._print_error_msg("无法获取相册首页: " + photo_album_url + ' ' + user_name)

            self._print_step_msg(user_name + "下载完毕，总共获得" + str(image_count - 1) + "张图片")
            user_id_list[user_id][2] = str(int(user_id_list[user_id][2]) + image_count - 1)
            total_image_count += image_count - 1

            # 排序
            if self.is_sort == 1:
                image_list = sorted(os.listdir(image_path), reverse=True)
                # 判断排序目标文件夹是否存在
                if len(image_list) >= 1:
                    destination_path = self.image_download_path + "\\" + user_id_list[user_id][4] + "\\" + user_name
                    if not common.make_dir(destination_path, 1):
                        self._print_error_msg("创建图片子目录： " + destination_path + " 失败，程序结束！")
                        common.process_exit()

                    # 倒叙排列
                    count = int(user_id_list[user_id][2]) + 1

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
            new_user_id_list_file = open(new_user_id_list_file_path, "a")
            new_user_id_list_file.write("\t".join(user_id_list[user_id]) + "\n")
            new_user_id_list_file.close()

        stop_time = time.time()
        self._print_step_msg("存档文件中所有用户图片已成功下载，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(total_image_count) + "张")

if __name__ == "__main__":
    GooglePlus().main()
