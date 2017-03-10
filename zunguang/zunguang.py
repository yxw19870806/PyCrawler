# -*- coding:UTF-8  -*-
"""
尊光图片爬虫
http://zunguang.com/
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os

ERROR_PAGE_COUNT_CHECK = 10


# 根据页面内容获取图片地址列表
def get_album_page(page_count):
    album_page_url = "http://www.zunguang.com/index.php?c=api&yc=blog&ym=getOneBlog"
    post_data = {"bid": page_count}
    album_page_response = net.http_request(album_page_url, method="POST", post_data=post_data, json_decode=True, is_random_ip=False)
    extra_info = {
        "is_error": False,  # 是不是格式不符合
        "is_skip": False,  # 是不是需要跳过（没有内容，不需要下载）
        "title": "",  # 页面解析出的相册标题
        "image_url_list": [],  # 页面解析出的图片地址列表
    }
    if album_page_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        if (
            robot.check_sub_key(("body",), album_page_response.json_data) and
            robot.check_sub_key(("blog",), album_page_response.json_data["body"])
        ):
            if album_page_response.json_data["body"]["blog"] is False:
                extra_info["is_skip"] = True
            elif isinstance(album_page_response.json_data["body"]["blog"], list) and len(album_page_response.json_data["body"]["blog"]) == 1:
                if robot.check_sub_key(("type",), album_page_response.json_data["body"]["blog"][0]):
                    album_type = int(album_page_response.json_data["body"]["blog"][0]["type"])
                    if album_type == 2:  # 歌曲类型的相册
                        extra_info["is_skip"] = True
                    elif album_type == 3:  # 图片类型的相册
                        album_body = album_page_response.json_data["body"]["blog"][0]
                        if robot.check_sub_key(("title", "attr"), album_body) and robot.check_sub_key(("img",), album_body["attr"]):
                            if album_body["title"]:
                                extra_info["title"] = str(album_body["title"].encode("utf-8"))
                            image_url_list = []
                            for image_data in album_body["attr"]["img"]:
                                if robot.check_sub_key(("url",), image_data):
                                    image_url_list.append("http://www.zunguang.com/%s" % str(image_data["url"]))
                                else:
                                    image_url_list = []
                                    break
                            if len(image_url_list) == 0:
                                extra_info["is_error"] = True
                            else:
                                extra_info["image_url_list"] = image_url_list
                    else:  # 其他类型的相册
                        extra_info["is_error"] = True
            else:
                extra_info["is_error"] = True
        else:
            extra_info["is_error"] = True
    album_page_response.extra_info = extra_info
    return album_page_response


class ZunGuang(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

        tool.print_msg("配置文件读取完成")

    def main(self):
        # 解析存档文件，获取上一次的album id
        page_count = 1
        if os.path.exists(self.save_data_path):
            save_file = open(self.save_data_path, "r")
            save_info = save_file.read()
            save_file.close()
            page_count = int(save_info.strip())

        total_image_count = 0
        error_count = 0
        is_over = False
        while not is_over:
            log.step("开始解析第%s页图片" % page_count)

            # 获取相册
            try:
                album_page_response = get_album_page(page_count)
            except SystemExit:
                log.step("提前退出")
                page_count -= error_count - 1
                break

            if album_page_response.status != net.HTTP_RETURN_CODE_SUCCEED:
                log.error("第%s页相册访问失败，原因：%s" % (page_count, robot.get_http_request_failed_reason(album_page_response.status)))
                page_count -= error_count - 1
                break

            if album_page_response.extra_info["is_error"]:
                log.error("第%s页相册解析失败" % page_count)
                page_count -= error_count - 1
                break

            if album_page_response.extra_info["is_skip"]:
                if error_count >= ERROR_PAGE_COUNT_CHECK:
                    log.error("连续%s页相册没有图片，退出程序" % ERROR_PAGE_COUNT_CHECK)
                    page_count -= error_count - 1
                    break
                else:
                    log.error("第%s页相册没有图片，跳过" % page_count)
                    page_count += 1
                    continue

            # 错误数量重置
            error_count = 0

            # 下载目录标题
            title = ""
            if album_page_response.extra_info["title"]:
                # 过滤标题中不支持的字符
                title = robot.filter_text(album_page_response.extra_info["title"])
            if title:
                image_path = os.path.join(self.image_download_path, "%04d %s" % (page_count, title))
            else:
                image_path = os.path.join(self.image_download_path, "%04d" % page_count)
            if not tool.make_dir(image_path, 0):
                # 目录出错，把title去掉后再试一次，如果还不行退出
                log.error("创建第%s页相册目录 %s 失败，尝试不使用title" % (page_count, image_path))
                post_path = os.path.join(image_path, page_count)
                if not tool.make_dir(post_path, 0):
                    log.error("创建第%s页相册目录 %s 失败" % (page_count, image_path))
                    break

            log.step("第%s页相册解析的全部图片：%s" % (page_count, album_page_response.extra_info["image_url_list"]))
            image_count = 1
            for image_url in album_page_response.extra_info["image_url_list"]:
                log.step("开始下载第%s页第%s张图片 %s" % (page_count, image_count, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(image_path, "%03d.%s" % (image_count, file_type))
                try:
                    save_file_return = net.save_net_file(image_url, file_path, need_content_type=True)
                    if save_file_return["status"] == 1:
                        log.step("第%s页第%s张图片下载成功" % (page_count, image_count))
                        image_count += 1
                    else:
                        log.error("第%s页第%s张图片 %s 下载失败，原因：%s" % (page_count, image_count, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))
                except SystemExit:
                    log.step("提前退出")
                    tool.remove_dir(image_path)
                    is_over = True
                    break

            if not is_over:
                total_image_count += image_count - 1
                page_count += 1

        # 重新保存存档文件
        save_data_dir = os.path.dirname(self.save_data_path)
        if not os.path.exists(save_data_dir):
            tool.make_dir(save_data_dir, 0)
        save_file = open(self.save_data_path, "w")
        save_file.write(str(page_count))
        save_file.close()

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    ZunGuang().main()
