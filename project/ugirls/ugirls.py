# -*- coding:UTF-8  -*-
"""
尤果图集预览图片爬虫
http://www.ugirls.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
import os
import re


# 获取指定页数的图集
def get_album_page(album_id):
    album_url = "http://www.ugirls.com/Content/List/Magazine-%s.html" % album_id
    album_response = net.http_request(album_url)
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "is_delete": False,  # 是不是已经被删除
        "model_name": "",  # 页面解析出的模特名字
        "image_url_list": [],  # 页面解析出的所有图片地址列表
    }
    if album_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if album_response.data.find("该页面不存在,或者已经被删除!") >= 0:
            extra_info["is_delete"] = True
        else:
            model_name_data = tool.find_sub_string(album_response.data, '<div class="ren_head">', "</div>")
            model_name = tool.find_sub_string(model_name_data, 'title="', '"')
            if model_name:
                extra_info["model_name"] = model_name.strip()
            image_info_data = tool.find_sub_string(album_response.data, '<ul id="myGallery">', "</ul>")
            image_url_list = re.findall('<img src="([^"]*)"', image_info_data)
            if len(image_url_list) > 0:
                for image_url in image_url_list:
                    if image_url.find("_magazine_web_m.") >= 0:
                        extra_info["image_url_list"].append(image_url.replace("_magazine_web_m.", "_magazine_web_l."))
                    else:
                        extra_info["is_error"] = True
                        break
            else:
                extra_info["is_error"] = True
    album_response.extra_info = extra_info
    return album_response


# 从图集首页获取最新的图集id
def get_newest_album_id():
    index_url = "http://www.ugirls.com/Content/"
    index_response = net.http_request(index_url)
    max_album_id = None
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        album_list_html = tool.find_sub_string(index_response.data, '<div class="magazine_list_wrap">', '<div class="xfenye">')
        album_id_find = re.findall('href="http://www.ugirls.com/Shop/Detail/Product-(\d*).html" target="_blank"', album_list_html)
        if len(album_id_find) > 0:
            max_album_id = max(map(int, list(set(album_id_find))))
    return max_album_id


class UGirls(robot.Robot):
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

        newest_album_id = get_newest_album_id()

        if newest_album_id is None:
            log.error("最新图集id获取失败")
            tool.process_exit()

        total_image_count = 0
        while album_id <= newest_album_id:
            log.step("开始解析第%s页图集" % album_id)

            # 获取相册
            try:
                album_response = get_album_page(album_id)
            except SystemExit:
                log.step("提前退出")
                break

            if album_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页图集访问失败，原因：%s" % (album_id, robot.get_http_request_failed_reason(album_response.status)))
                break

            if album_response.extra_info["is_error"]:
                log.error("第%s页图集解析失败" % album_id)
                break

            if album_response.extra_info["is_delete"]:
                log.step("第%s页图集已被删除，跳过" % album_id)
                album_id += 1
                continue

            log.trace("第%s页图集解析的所有图片：%s" % (album_id, album_response.extra_info["image_url_list"]))

            album_path = os.path.join(self.image_download_path, "%04d %s" % (album_id, album_response.extra_info["model_name"]))
            if not tool.make_dir(album_path, 0):
                log.error("创建图集目录 %s 失败" % album_path)
                tool.process_exit()

            image_count = 1
            for image_url in album_response.extra_info["image_url_list"]:
                log.step("开始下载第%s页图集的第%s张图片 %s" % (album_id, image_count, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                save_file_return = net.save_net_file(image_url, file_path)
                if save_file_return["status"] == 1:
                    log.step("第%s页图集的第%s张图片下载成功" % (album_id, image_count))
                    image_count += 1
                else:
                     log.error("第%s页图集的第%s张图片 %s 下载失败，原因：%s" % (album_id, image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
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
    UGirls().main()
