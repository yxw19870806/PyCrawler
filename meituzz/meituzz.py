# -*- coding:UTF-8  -*-
"""
美图赚赚图片爬虫
http://meituzz.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
import os
import re


class MeiTuZZ(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

        tool.print_msg("配置文件读取完成")

    def main(self):
        # 解析存档文件，获取上一次的album id
        album_id = 1
        if os.path.exists(self.save_data_path):
            save_file = open(self.save_data_path, "r")
            save_info = save_file.read()
            save_file.close()
            album_id = int(save_info.strip())

        total_image_count = 0
        is_over = False
        while not is_over:
            album_url = "http://meituzz.com/album/browse?albumID=%s" % album_id
            try:
                album_page_return_code, album_page = tool.http_request(album_url)[:2]
            except SystemExit:
                log.step("提前退出")
                break

            if album_page_return_code != 1:
                log.error("第%s页图片获取失败" % album_id)
                break

            total_photo_count_find = re.findall('<span id="photoNumTotal">(\d*)</span>', album_page)
            if len(total_photo_count_find) != 1:
                log.error("第%s页图片数量解析失败" % album_id)
                break

            image_url_list = re.findall('data-src="([^"]*)"', album_page)
            if len(image_url_list) == 0:
                log.error("第%s页图片地址列表解析失败" % album_id)
                break

            if len(image_url_list) != int(total_photo_count_find[0]):
                if album_page.find('<div class="payWindow_content" id="payWindow">') >= 0:
                    log.error("第%s页解析有%s张收费图片" % (album_id, (int(total_photo_count_find[0]) - len(image_url_list))))
                else:
                    log.error("第%s页解析获取的图片数量不符" % album_id)
                    break

            image_path = os.path.join(self.image_download_path, str(album_id))
            if not tool.make_dir(image_path, 0):
                log.error("创建图片下载目录 %s 失败" % image_path)
                break

            image_count = 1
            for image_url in image_url_list:
                log.step("开始下载第%s页第%s张图片 %s" % (album_id, image_count, image_url))

                file_path = os.path.join(image_path, "%04d.jpg" % image_count)
                try:
                    if tool.save_net_file(image_url, file_path, True):
                        log.step("第%s页第%s张图片下载成功" % (album_id, image_count))
                        image_count += 1
                    else:
                        log.error("第%s页第%s张图片 %s 下载失败" % (album_id, image_count, image_url))
                except SystemExit:
                    log.step("提前退出")
                    tool.remove_dir(image_path)
                    is_over = True
                    break

            if not is_over:
                total_image_count += image_count - 1
                album_id += 1

        # 重新保存存档文件
        save_data_dir = os.path.dirname(self.save_data_path)
        if not os.path.exists(save_data_dir):
            tool.make_dir(save_data_dir, 0)
        save_file = open(self.save_data_path, "w")
        save_file.write(str(album_id))
        save_file.close()

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    MeiTuZZ().main()
