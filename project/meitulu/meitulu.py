# -*- coding:UTF-8  -*-
"""
美图录图片爬虫
https://www.meitulu.com
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re


# 获取指定一页的图集
def get_one_page_album(album_id, page_count):
    if page_count == 1:
        album_pagination_url = "https://www.meitulu.com/item/%s.html" % album_id
    else:
        album_pagination_url = "https://www.meitulu.com/item/%s_%s.html" % (album_id, page_count)
    album_pagination_response = net.http_request(album_pagination_url)
    extra_info = {
        "is_delete": False,  # 是不是已经被删除
        "is_over": False,  # 是不是图集的最后一页
        "album_title": "",  # 页面解析出的图集标题
        "image_url_list": [],  # 页面解析出的所有图片地址列表
    }
    if album_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 判断图集是否已经被删除
        extra_info["is_delete"] = album_pagination_response.data.find("全站内容整理中, 请从首页重新访问!") >= 0
        # 获取图集标题
        extra_info["album_title"] = str(tool.find_sub_string(album_pagination_response.data, "<h1>", "</h1>")).strip()
        # 获取图集图片地址
        image_url_list = re.findall('<img src="([^"]*)"', tool.find_sub_string(album_pagination_response.data, '<div class="content">', "</div>"))
        extra_info["image_url_list"] = map(str, image_url_list)
        # 判断是不是最后一页
        page_count_find = re.findall('">(\d*)</a>', tool.find_sub_string(album_pagination_response.data, '<div id="pages">', "</div>"))
        max_page_count = max(map(int, page_count_find))
        extra_info['is_over'] = page_count >= max_page_count
    album_pagination_response.extra_info = extra_info
    return album_pagination_response


class MeiTuLu(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

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
            log.step("开始解析%s号图集" % album_id)

            page_count = 1
            image_count = 1
            album_title = ""
            album_path = os.path.join(self.image_download_path, str(album_id))
            while True:
                log.step("开始解析%s号图集第%s页" % (album_id, page_count))
                # 获取相册
                try:
                    album_pagination_response = get_one_page_album(album_id, page_count)
                except SystemExit:
                    is_over = True
                    log.step("提前退出")
                    break

                if album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                    log.error("第%s页图集访问失败，原因：%s" % (album_id, robot.get_http_request_failed_reason(album_pagination_response.status)))
                    break

                log.trace("%s号图集第%s页的所有图片：%s" % (album_id, page_count, album_pagination_response.extra_info["image_url_list"]))

                # 过滤标题中不支持的字符
                if page_count == 1:
                    album_title = robot.filter_text(album_pagination_response.extra_info["album_title"])
                    if album_title:
                        album_path = os.path.join(self.image_download_path, "%s %s" % (album_id, album_title))
                    else:
                        album_path = os.path.join(self.image_download_path, str(album_id))
                    if not tool.make_dir(album_path, 0):
                        # 目录出错，把title去掉后再试一次，如果还不行退出
                        log.error("创建图集目录 %s 失败，尝试不使用title" % album_path)
                        album_path = os.path.join(self.image_download_path, album_id)
                        if not tool.make_dir(album_path, 0):
                            log.error("创建图集目录 %s 失败" % album_path)
                            tool.process_exit()

                for image_url in album_pagination_response.extra_info["image_url_list"]:
                    log.step("图集%s 《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_count, image_url))

                    file_type = image_url.split(".")[-1]
                    file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                    try:
                        save_file_return = net.save_net_file(image_url, file_path)
                        if save_file_return["status"] == 1:
                            log.step("图集%s 《%s》 第%s张图片下载成功" % (album_id, album_title, image_count))
                            image_count += 1
                        else:
                             log.error("图集%s 《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_id, album_title, image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                    except SystemExit:
                        log.step("提前退出")
                        tool.remove_dir_or_file(album_path)
                        is_over = True
                        break

                if is_over or album_pagination_response.extra_info["is_over"]:
                    break
                else:
                    page_count += 1

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
    MeiTuLu().main()
