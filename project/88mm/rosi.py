# -*- coding:UTF-8  -*-
"""
88mm ROSI图片爬虫
http://www.88mmw.com/Rosi/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re


# 获取指定一页的图集
def get_one_page_album(page_count):
    album_pagination_url = "http://www.88mmw.com/Rosi/list_1_%s.html" % (page_count)
    album_pagination_response = net.http_request(album_pagination_url)
    extra_info = {
        "is_over": False,  # 是不是最后一页图集
        "album_info_list": [],  # 页面解析出的所有图集信息列表
    }
    if album_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取图集图片地址
        album_info_html = tool.find_sub_string(album_pagination_response.data.decode("GBK").encode("UTF-8"), '<div class="xxx">', "</div>")
        album_info_list = re.findall('<a href="/Rosi/(\d*)/" title="ROSI套图No.(\d*)', album_info_html)
        for page_id, album_id in album_info_list:
            extra_album_info = {
                "page_id": str(page_id),  # 页面解析出的图集地址页面id
                "album_id": str(album_id),  # 页面解析出的图集id
            }
            extra_info["album_info_list"].append(extra_album_info)
        # 判断是不是最后一页
        max_page_find = re.findall("<a href='list_1_(\d)*.html'>末页</a>", album_pagination_response.data.decode("GBK").encode("UTF-8"))
        if len(max_page_find) == 2 and max_page_find[0] == max_page_find[1] and robot.is_integer(max_page_find[0]):
            extra_info['is_over'] = page_count >= int(max_page_find[0])
    album_pagination_response.extra_info = extra_info
    return album_pagination_response


# 获取图集一页的图片
def get_one_page_photo(page_id, page_count):
    if page_count == 1:
        photo_pagination_url = "http://www.88mmw.com/Rosi/%s" % page_id
    else:
        photo_pagination_url = "http://www.88mmw.com/Rosi/%s/index_%s.html" % (page_id, page_count)
    photo_pagination_response = net.http_request(photo_pagination_url)
    extra_info = {
        "is_over": False,  # 是不是图集的最后一页
        "image_url_list": [],  # 页面解析出的所有图片地址列表
    }
    if photo_pagination_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        # 获取图片地址
        image_url_list = re.findall('<img src="([^"]*)"', tool.find_sub_string(photo_pagination_response.data, '<div class="zzz">', "</div>"))
        for image_url in image_url_list:
            extra_info["image_url_list"].append("http://www.88mmw.com" + str(image_url).replace("-lp", ""))
        # 判断是不是最后一页
        max_page_count = tool.find_sub_string(photo_pagination_response.data.decode("GBK").encode("UTF-8"), '<div class="page"><span>共 <strong>', '</strong> 页')
        if robot.is_integer(max_page_count):
            extra_info['is_over'] = page_count >= int(max_page_count)
    photo_pagination_response.extra_info = extra_info
    return photo_pagination_response


class Rosi(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的album id
        if os.path.exists(self.save_data_path):
            last_album_id = int(tool.read_file(self.save_data_path))
        else:
            last_album_id = 0

        total_image_count = 0
        page_count = 1
        is_over = False
        first_album_id = None
        while not is_over:
            log.step("开始解析第%s页图集" % page_count)

            # 获取相册
            try:
                album_pagination_response = get_one_page_album(page_count)
            except SystemExit:
                log.step("提前退出")
                tool.process_exit()

            if album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页图集访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(album_pagination_response.status)))
                break

            log.trace("第%s页获取的所有图集：%s" % (page_count, album_pagination_response.extra_info["album_info_list"]))

            for album_info in album_pagination_response.extra_info["album_info_list"]:
                # 检查是否达到存档记录
                if int(album_info["album_id"]) <= last_album_id:
                    is_over = True
                    break

                # 新的存档记录
                if first_album_id is None:
                    first_album_id = album_info["album_id"]

                album_page_count = 1
                image_count = 1
                album_path = os.path.join(self.image_download_path, album_info["album_id"])
                while True:
                    try:
                        photo_pagination_response = get_one_page_photo(album_info["page_id"], album_page_count)
                    except SystemExit:
                        log.step("提前退出")
                        tool.remove_dir_or_file(album_path)
                        tool.process_exit()

                    if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                        log.error("%s号图集第%s页访问失败，原因：%s" % (album_info["album_id"], album_page_count, robot.get_http_request_failed_reason(photo_pagination_response.status)))
                        break

                    if len(photo_pagination_response.extra_info["image_url_list"]) == 0:
                        log.error("%s号图集第%s页解析图片失败" % (album_info["album_id"], album_page_count))
                        break

                    log.trace("%s号图集第%s页获取的所有图集：%s" % (album_info["album_id"], album_page_count, album_pagination_response.extra_info["album_info_list"]))

                    for image_url in photo_pagination_response.extra_info["image_url_list"]:
                        log.step("%s号图集 开始下载第%s张图片 %s" % (album_info["album_id"], image_count, image_url))

                        file_type = image_url.split(".")[-1]
                        file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                        try:
                            save_file_return = net.save_net_file(image_url, file_path)
                            if save_file_return["status"] == 1:
                                log.step("%s号图集 第%s张图片下载成功" % (album_info["album_id"], image_count))
                                image_count += 1
                            else:
                                 log.error("%s号图集 第%s张图片 %s 下载失败，原因：%s" % (album_info["album_id"], image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                        except SystemExit:
                            log.step("提前退出")
                            tool.remove_dir_or_file(album_path)
                            tool.process_exit()

                    if is_over or photo_pagination_response.extra_info["is_over"]:
                        break
                    else:
                        album_page_count += 1

                if is_over:
                    break
                else:
                    total_image_count += image_count

            if not is_over:
                if album_pagination_response.extra_info["is_over"]:
                    break
                else:
                    page_count += 1

        # 重新保存存档文件
        if first_album_id is not None:
            tool.write_file(str(first_album_id), self.save_data_path, 2)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    Rosi().main()
