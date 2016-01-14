# -*- coding:UTF-8  -*-
'''
Created on 2013-5-6

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import common
import os
import re
import shutil
import time

class Shinoda(common.Robot):

    def __init__(self):
        super(Shinoda, self).__init__()

        self.get_image_page_count = 28
        self.user_id_list_file_path = os.getcwd() + "\\shinoda.save"

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

        # 图片下载临时目录
        if self.is_sort == 1:
            self._print_step_msg("创建图片下载目录：" + self.image_temp_path)
            if not common.make_dir(self.image_temp_path, 2):
                self._print_error_msg("创建图片下载目录：" + self.image_temp_path + " 失败，程序结束！")
                common.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            common.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 读取存档文件
        last_blog_id = ""
        image_start_index = 0
        if os.path.exists(self.user_id_list_file_path):
            save_file = open(self.user_id_list_file_path, "r")
            save_info = save_file.read()
            save_file.close()
            save_info = save_info.split("\t")
            if len(save_info) >= 2:
                image_start_index = int(save_info[0])
                last_blog_id = save_info[1]

        # 下载
        page_index = 1
        image_count = 1
        is_over = False
        new_last_blog_id = ''
        host = 'http://blog.mariko-shinoda.net/'
        if self.is_sort == 1:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path
        while not is_over:
            index_url = host + "page%s.html" % (page_index - 1)
            [index_page_return_code, index_page] = common.http_request(index_url)
            self._trace("博客页面地址：" + index_url)

            if index_page_return_code == 1:
                image_name_list = re.findall('data-original="./([^"]*)"', index_page)
                for image_name in image_name_list:
                    blog_id = image_name.split('-')[0]
                    if blog_id == last_blog_id:
                        is_over = True
                        break
                    if new_last_blog_id == '':
                        new_last_blog_id = blog_id
                    image_url = host + image_name
                    # 文件类型
                    file_type = image_url.split(".")[-1].split(':')[0]
                    file_path = image_path + "\\" + str("%05d" % image_count) + "." + file_type
                    self._print_step_msg("开始下载第 " + str(image_count) + "张图片：" + image_url)
                    if common.save_image(image_url, file_path):
                        self._print_step_msg("第" + str(image_count) + "张图片下载成功")
                        image_count += 1
                    else:
                        self._print_step_msg("第" + str(image_count) + "张图片 " + image_url + " 下载失败")
                page_index += 1
                # 达到配置文件中的下载数量，结束
                if self.get_image_page_count != 0 and page_index > self.get_image_page_count:
                    break
            else:
                self._print_error_msg("无法访问博客页面" + index_url)
                is_over = True

        self._print_step_msg("下载完毕")
        
        # 排序复制到保存目录
        if self.is_sort == 1:
            for fileName in sorted(os.listdir(self.image_temp_path), reverse=True):
                image_start_index += 1
                image_path = self.image_temp_path + "\\" + fileName
                file_type = fileName.split(".")[-1]
                common.copy_files(image_path, self.image_download_path + "\\" + str("%05d" % image_start_index) + "." + file_type)
            self._print_step_msg("图片从下载目录移动到保存目录成功")
            # 删除下载临时目录中的图片
            shutil.rmtree(self.image_temp_path, True)
            
        # 保存新的存档文件
        new_save_file_path = os.getcwd() + "\\" + time.strftime("%Y-%m-%d_%H_%M_%S_", time.localtime(time.time())) + os.path.split(self.user_id_list_file_path)[-1]
        self._print_step_msg("保存新存档文件: " + new_save_file_path)
        new_save_file = open(new_save_file_path, "w")
        new_save_file.write(str(image_start_index) + "\t" + new_last_blog_id)
        new_save_file.close()
            
        stop_time = time.time()
        self._print_step_msg("成功下载最新图片，耗时" + str(int(stop_time - start_time)) + "秒，共计图片" + str(image_count - 1) + "张")

if __name__ == "__main__":
    Shinoda().main()
