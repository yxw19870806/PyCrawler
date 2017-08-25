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


# 获取图集首页
def get_index_page():
    index_url = "https://www.meitulu.com/"
    index_response = net.http_request(index_url)
    result = {
        "max_album_id": None,  # 最新图集id
    }
    if index_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(index_response.status))
    new_album_html = tool.find_sub_string(index_response.data, '<div class="zuixin">最新发布</div>', '<div class="zuixin">名站写真</div>')
    if not new_album_html:
        raise robot.RobotException("页面截取最新发布失败\n%s" % index_response.data)
    album_id_find = re.findall('<a href="https://www.meitulu.com/item/(\d*).html"', new_album_html)
    if len(album_id_find) == 0:
        raise robot.RobotException("最新发布匹配图集id失败\n%s" % new_album_html)
    result["max_album_id"] = max(map(int, album_id_find))
    return result


# 获取指定一页的图集
def get_one_page_album(album_id):
    page_count = max_page_count = 1
    result = {
        "is_delete": False,  # 是不是已经被删除
        "album_title": "",  # 图集标题
        "image_url_list": [],  # 所有图片地址
    }
    while page_count <= max_page_count:
        if page_count == 1:
            album_pagination_url = "https://www.meitulu.com/item/%s.html" % album_id
        else:
            album_pagination_url = "https://www.meitulu.com/item/%s_%s.html" % (album_id, page_count)
        album_pagination_response = net.http_request(album_pagination_url)
        if page_count == 1 and album_pagination_response.status == 404:
            result["is_delete"] = True
            return result
        elif album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException("第%s页 " % page_count + robot.get_http_request_failed_reason(album_pagination_response.status))
        if page_count == 1:
            # 获取图集标题
            result["album_title"] = str(tool.find_sub_string(album_pagination_response.data, "<h1>", "</h1>")).strip()
        # 获取图集图片地址
        image_list_html = tool.find_sub_string(album_pagination_response.data, '<div class="content">', "</div>")
        if not image_list_html:
            raise robot.RobotException("第%s页 页面截取图片列表失败\n%s" % (page_count, album_pagination_response.data))
        image_url_list = re.findall('<img src="([^"]*)"', image_list_html)
        if len(image_url_list) == 0:
            if image_list_html.strip() != "<center></center>":
                raise robot.RobotException("第%s页 图片列表匹配图片地址失败\n%s" % (page_count, album_pagination_response.data))
        else:
            result["image_url_list"] += map(str, image_url_list)
        # 判断是不是最后一页
        page_count_find = re.findall('">(\d*)</a>', tool.find_sub_string(album_pagination_response.data, '<div id="pages">', "</div>"))
        if len(page_count_find) > 0:
            max_page_count = max(map(int, page_count_find))
        else:
            max_page_count = 1
        page_count += 1
    return result


# 对一些异常的图片地址做过滤
def get_image_url(image_url):
    return image_url.replace("/[page]", "/")


class MeiTuLu(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config)

    def main(self):
        # 解析存档文件，获取上一次的album id
        if os.path.exists(self.save_data_path):
            album_id = int(tool.read_file(self.save_data_path))
        else:
            album_id = 1

        # 获取图集首页
        try:
            index_response = get_index_page()
        except robot.RobotException, e:
            log.error("图集首页解析失败，原因：%s" % e.message)
            raise

        log.step("最新图集id：%s" % index_response["max_album_id"])

        total_image_count = 0
        is_over = False
        while not is_over and album_id <= index_response["max_album_id"]:
            log.step("开始解析图集%s" % album_id)

            # 获取相册
            try:
                album_pagination_response = get_one_page_album(album_id)
            except robot.RobotException,e:
                log.error("图集%s解析失败，原因：%s" % (album_id, e.message))
                break
            except SystemExit:
                log.step("提前退出")
                break

            if album_pagination_response["is_delete"]:
                log.step("图集%s不存在，跳过" % album_id)
                album_id += 1
                continue

            log.trace("图集%s解析的所有图片：%s" % (album_id, album_pagination_response["image_url_list"]))

            # 过滤标题中不支持的字符
            album_title = robot.filter_text(album_pagination_response["album_title"])
            if album_title:
                album_path = os.path.join(self.image_download_path, "%04d %s" % (album_id, album_title))
            else:
                album_path = os.path.join(self.image_download_path, "%04d" % album_id)

            image_index = 1
            for image_url in album_pagination_response["image_url_list"]:
                image_url = get_image_url(image_url)
                log.step("图集%s 《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_index, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(album_path, "%03d.%s" % (image_index, file_type))
                try:
                    save_file_return = net.save_net_file(image_url, file_path)
                    if save_file_return["status"] == 1:
                        log.step("图集%s 《%s》 第%s张图片下载成功" % (album_id, album_title, image_index))
                        image_index += 1
                    else:
                         log.error("图集%s 《%s》 第%s张图片 %s 下载失败，原因：%s" % (album_id, album_title, image_index, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                except SystemExit:
                    log.step("提前退出")
                    tool.remove_dir_or_file(album_path)
                    is_over = True
                    break

            if not is_over:
                total_image_count += image_index - 1
                album_id += 1

        # 重新保存存档文件
        tool.write_file(str(album_id), self.save_data_path, 2)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    MeiTuLu().main()
