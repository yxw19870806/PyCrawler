# -*- coding:UTF-8  -*-
'''
Created on 2013-5-6

@author: hikaru
QQ: 286484545
email: hikaru870806@hotmail.com
如有问题或建议请联系
'''

from common import log, robot, tool
import os
import re
import shutil
import time


class Shinoda(robot.Robot):
    def __init__(self):
        super(Shinoda, self).__init__()

        tool.print_msg("配置文件读取完成")

    def main(self):
        start_time = time.time()

        # 图片下载临时目录
        if self.is_sort == 1:
            log.step("创建图片下载目录：" + self.image_temp_path)
            if not tool.make_dir(self.image_temp_path, 0):
                log.error("创建图片下载目录：" + self.image_temp_path + " 失败，程序结束！")
                tool.process_exit()

        # 设置代理
        if self.is_proxy == 1:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 读取存档文件
        last_blog_id = ""
        image_start_index = 0
        if os.path.exists(self.save_data_path):
            save_file = open(self.save_data_path, "r")
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
        new_last_blog_id = ""
        host = "http://blog.mariko-shinoda.net/"
        if self.is_sort == 1:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path
        while not is_over:
            index_url = host + "page%s.html" % (page_index - 1)
            [index_page_return_code, index_page] = tool.http_request(index_url)[:2]
            log.step("博客页面地址：" + index_url)

            if index_page_return_code == 1:
                image_name_list = re.findall('data-original="./([^"]*)"', index_page)
                for image_name in image_name_list:
                    blog_id = image_name.split("-")[0]
                    if blog_id == last_blog_id:
                        is_over = True
                        break
                    if new_last_blog_id == "":
                        new_last_blog_id = blog_id
                    image_url = host + image_name
                    # 文件类型
                    file_type = image_url.split(".")[-1].split(":")[0]
                    file_path = os.path.join(image_path, str("%05d" % image_count) + "." + file_type)
                    log.step("开始下载第 " + str(image_count) + "张图片：" + image_url)
                    if tool.save_image(image_url, file_path):
                        log.step("第" + str(image_count) + "张图片下载成功")
                        image_count += 1
                    else:
                        log.step("第" + str(image_count) + "张图片 " + image_url + " 下载失败")
                page_index += 1
            else:
                log.error("无法访问博客页面" + index_url)
                is_over = True

        log.step("下载完毕")
        
        # 排序复制到保存目录
        if self.is_sort == 1:
            if robot.sort_file(self.image_temp_path, self.image_download_path, image_start_index, 5):
                log.step(" 图片从下载目录移动到保存目录成功")
            else:
                log.error(" 创建图片保存目录：" + self.image_download_path + " 失败，程序结束！")
                tool.process_exit()

        # 保存新的存档文件
        new_save_file_path = robot.get_new_save_file_path(self.save_data_path)
        log.step("保存新存档文件: " + new_save_file_path)
        new_save_file = open(new_save_file_path, "w")
        new_save_file.write(str(image_start_index) + "\t" + new_last_blog_id)
        new_save_file.close()
            
        duration_time = int(time.time() - start_time)
        log.step("全部下载完毕，耗时" + str(duration_time) + "秒，共计图片" + str(image_count - 1) + "张")

if __name__ == "__main__":
    Shinoda().main()
