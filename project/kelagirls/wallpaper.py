# -*- coding:UTF-8  -*-
"""
克拉女神壁纸图片爬虫
http://kelagirls.com/bizhi!findForIndexMore.action
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import *
from pyquery import PyQuery as pq
import os
import sys
import traceback


# 获取指定一页的壁纸
def get_one_page_photo(page_count):
    photo_pagination_url = "http://kelagirls.com/bizhi!findForIndexMore.action"
    query_data = {"page": page_count}
    photo_pagination_response = net.http_request(photo_pagination_url, method="GET", fields=query_data)
    result = {
        "image_info_list": [],  # 全部图片地址
        "is_over": [],  # 是不是最后一页壁纸
    }
    if photo_pagination_response.status != net.HTTP_RETURN_CODE_SUCCEED:
        raise robot.RobotException(robot.get_http_request_failed_reason(photo_pagination_response.status))
    photo_list_selector = pq(photo_pagination_response.data.decode("UTF-8")).find(".bizhinmore .bizhi")
    if photo_list_selector.size() == 0:
        raise robot.RobotException("页面匹配图片列失败\n%s" % photo_pagination_response.data)
    for photo_index in range(0, photo_list_selector.size()):
        result_image_info = {
            "image_id": None,  # 图片id
            "image_url": None,  # 图片地址
            "model_name": "",  # 模特名字
        }
        # 获取图片id
        image_id = photo_list_selector.eq(photo_index).find(".bizhibigwrap").attr("id")
        if not image_id:
            raise robot.RobotException("图片列表匹配图片id失败\n%s" % photo_list_selector.eq(photo_index).html().encode("UTF-8"))
        if not (image_id[0:3] == "big" and robot.is_integer(image_id[3:])):
            raise robot.RobotException("图片列表匹配的图片id格式不正确\n%s" % photo_list_selector.eq(photo_index).html().encode("UTF-8"))
        result_image_info["image_id"] = str(image_id[3:])
        # 获取图片地址
        image_path = photo_list_selector.eq(photo_index).find(".bizhibig img").eq(1).attr("src")
        if not image_path:
            raise robot.RobotException("图片列表匹配图片地址失败\n%s" % photo_list_selector.eq(photo_index).html().encode("UTF-8"))
        result_image_info["image_url"] = "http://kelagirls.com/" + str(image_path.encode("UTF-8"))
        # 获取模特名字
        model_name = photo_list_selector.eq(photo_index).find(".bzwdown span").eq(0).text().encode("UTF-8")
        if not model_name:
            raise robot.RobotException("图片列表匹配模特名字失败\n%s" % photo_list_selector.eq(photo_index).html().encode("UTF-8"))
        result_image_info["model_name"] = str(model_name)
        result["image_info_list"].append(result_image_info)
    # 判断是不是最后一页
    pagination_selector = pq(photo_pagination_response.data.decode("UTF-8")).find(".pageBottom div")
    max_page_count = page_count
    for pagination_index in range(0, pagination_selector.size()):
        if robot.is_integer(pagination_selector.eq(pagination_index).text()):
            max_page_count = max(max_page_count, int(pagination_selector.eq(pagination_index).text()))
    result["is_over"] = page_count >= max_page_count
    return result


# 对一些异常的图片地址做过滤
def get_image_url(image_url):
    return image_url.replace("/[page]", "/")


class Wallpaper(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        extra_config = {
            "save_data_path": os.path.join(os.path.dirname(sys._getframe().f_code.co_filename), "info/wallpaper.data")
        }
        robot.Robot.__init__(self, sys_config, extra_config=extra_config)

    def main(self):
        last_image_id = 0
        if os.path.exists(self.save_data_path):
            file_save_info = tool.read_file(self.save_data_path)
            if not robot.is_integer(file_save_info):
                log.error("存档内数据格式不正确")
                tool.process_exit()
            last_image_id = int(file_save_info)
        total_image_count = 0

        try:
            page_count = 1
            image_info_list = []
            is_over = False
            # 获取全部还未下载过需要解析的壁纸
            while not is_over:
                log.step("开始解析第%s页壁纸" % page_count)

                # 获取一页壁纸
                try:
                    photo_pagination_response = get_one_page_photo(page_count)
                except robot.RobotException, e:
                    log.error("第%s页壁纸解析失败，原因：%s" % (page_count, e.message))
                    break
                except SystemExit:
                    log.step("提前退出")
                    image_info_list = []
                    break

                log.trace("第%s页壁纸解析的全部图片：%s" % (page_count, photo_pagination_response["image_info_list"]))

                for image_info in photo_pagination_response["image_info_list"]:
                    image_info_list.append(image_info)

                if not is_over:
                    if photo_pagination_response["is_over"]:
                        is_over = True
                    else:
                        page_count += 1

            log.step("需要下载的全部图片解析完毕，共%s个" % len(image_info_list))

            # 从最早的图片开始下载
            while len(image_info_list) > 0:
                image_info = image_info_list.pop()

                log.step("开始下载第%s张图片 %s" % (image_info["image_id"], image_info["image_url"]))

                file_type = image_info["image_url"].split(".")[-1]
                file_path = os.path.join(self.image_download_path, "%03d %s.%s" % (int(image_info["image_id"]), robot.filter_text(image_info["model_name"]), file_type))
                save_file_return = net.save_net_file(image_info["image_url"], file_path)
                if save_file_return["status"] == 1:
                    log.step("第%s张图片下载成功" % image_info["image_id"])
                else:
                    log.error("第%s张图片 %s 下载失败，原因：%s" % (image_info["image_id"], image_info["image_url"], robot.get_save_net_file_failed_reason(save_file_return["code"])))
                    continue
                # 图片下载完毕
                total_image_count += 1  # 计数累加
                last_image_id = image_info["image_id"]  # 设置存档记录
        except SystemExit, se:
            if se.code == 0:
                log.step("提前退出")
            else:
                log.error("异常退出")
        except Exception, e:
            log.error("未知异常")
            log.error(str(e) + "\n" + str(traceback.format_exc()))

        # 重新保存存档文件
        tool.write_file(str(last_image_id), self.save_data_path, 2)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), total_image_count))


if __name__ == "__main__":
    Wallpaper().main()
