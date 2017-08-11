# -*- coding:UTF-8  -*-
"""
nvshens图片爬虫
https://www.nvshens.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re


# 获取图集所有图片
def get_album_photo(album_id):
    page_count = max_page_count = 1
    image_count = 0
    result = {
        "is_delete": False,  # 是不是已经被删除
        "album_title": "",  # 图集标题
        "image_url_list": [],  # 页所有图片地址
    }
    while page_count <= max_page_count:
        album_pagination_url = "https://www.nvshens.com/g/%s/%s.html" % (album_id, page_count)
        album_pagination_response = net.http_request(album_pagination_url)
        if album_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
            raise robot.RobotException("第%s页 " % page_count + robot.get_http_request_failed_reason(album_pagination_response.status))
        # 判断图集是否已经被删除
        if page_count == 1:
            result["is_delete"] = album_pagination_response.data.find("<title>该页面未找到-宅男女神</title>") >= 0
            # 获取图集图片总数
            image_count = tool.find_sub_string(album_pagination_response.data, "<span style='color: #DB0909'>", "张照片</span>")
            if not robot.is_integer(image_count):
                raise robot.RobotException("页面截取图片总数失败\n%s" % album_pagination_response.data)
            image_count = int(image_count)
            if image_count == 0:
                result["is_delete"] = True
            if result["is_delete"]:
                return result
            # 获取图集标题
            result["album_title"] = str(tool.find_sub_string(album_pagination_response.data, '<h1 id="htilte">', "</h1>")).strip()
            if not result["album_title"]:
                raise robot.RobotException("页面截取标题失败\n%s" % album_pagination_response.data)
            # 获取总页数
            pagination_html = tool.find_sub_string(album_pagination_response.data, '<div id="pages">', "</div>")
            if pagination_html:
                page_count_find = re.findall('/g/' + str(album_id) + '/([\d]*).html', pagination_html)
                if len(page_count_find) == 0:
                    raise robot.RobotException("分页信息截取最大页数失败\n%s" % pagination_html)
                max_page_count = max(map(int, page_count_find))
            else:
                max_page_count == 1
        # 获取图集图片地址，两种不同的页面样式
        if album_pagination_response.data.find('<ul id="hgallery">') >= 0:
            image_list_html = tool.find_sub_string(album_pagination_response.data, '<ul id="hgallery">', "</ul>")
            if not image_list_html:
                raise robot.RobotException("页面截取图片列表失败\n%s" % album_pagination_response.data)
            image_url_list = re.findall("<img src='([^']*)'", image_list_html)
        elif album_pagination_response.data.find('<div class="caroufredsel_wrapper">') >= 0:
            image_list_html = tool.find_sub_string(album_pagination_response.data, '<div class="caroufredsel_wrapper">', "</ul>")
            if not image_list_html:
                raise robot.RobotException("页面截取图片列表失败\n%s" % album_pagination_response.data)
            image_url_list = re.findall("src='([^']*)'", image_list_html)
        else:
            raise robot.RobotException("未知的图集样式\n%s" % album_pagination_response.data)
        if len(image_url_list) == 0:
            raise robot.RobotException("第%s页，页面匹配图片地址失败\n%s" % (page_count, album_pagination_response.data))
        result["image_url_list"] += map(str, image_url_list)
        page_count += 1
    # 判断页面上的总数和实际地址数量是否一致
    if image_count != len(result["image_url_list"]):
        raise robot.RobotException("页面截取的图片数量 %s 和显示的总数 %s 不一致" % (image_count, len(result["image_url_list"])))
    return result


# 从专辑首页获取最新的专辑id
def get_newest_album_id():
    index_url = "https://www.nvshens.com/gallery/"
    index_response = net.http_request(index_url)
    max_album_id = None
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        album_id_find = re.findall("<a class='galleryli_link' href='/g/(\d*)/'", index_response.data)
        if len(album_id_find) > 0:
            max_album_id = max(map(int, album_id_find))
    return max_album_id


class Nvshens(robot.Robot):
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
            album_id = 10000

        newest_album_id = get_newest_album_id()
        if newest_album_id is None:
            log.error("最新图集id解析失败")
            tool.process_exit()

        total_image_count = 0
        is_over = False
        while not is_over and album_id <= newest_album_id:
            log.step("开始解析图集%s" % album_id)

            image_count = 1
            # 获取图集
            try:
                album_pagination_response = get_album_photo(album_id)
            except robot.RobotException, e:
                log.error("图集%s解析失败，原因：%s" % (album_id, e.message))
                break
            except SystemExit:
                log.step("提前退出")
                break

            if album_pagination_response["is_delete"]:
                log.step("图集%s不存在，跳过" % album_id)
                break

            log.trace("图集%s解析的所有图片：%s" % (album_id, album_pagination_response["image_url_list"]))

            # 过滤标题中不支持的字符
            album_title = robot.filter_text(album_pagination_response["album_title"])
            if album_title:
                album_path = os.path.join(self.image_download_path, "%s %s" % (album_id, album_title))
            else:
                album_path = os.path.join(self.image_download_path, str(album_id))

            for image_url in album_pagination_response["image_url_list"]:
                log.step("图集%s 《%s》 开始下载第%s张图片 %s" % (album_id, album_title, image_count, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(album_path, "%03d.%s" % (image_count, file_type))
                try:
                    header_list = {"Referer": "https://www.nvshens.com/g/%s/" % album_id}
                    save_file_return = net.save_net_file(image_url, file_path, header_list=header_list)
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

            if not is_over:
                total_image_count += image_count - 1
                album_id += 1

        # 重新保存存档文件
        if total_image_count > 0:
            tool.write_file(str(album_id), self.save_data_path, 2)

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    Nvshens().main()
