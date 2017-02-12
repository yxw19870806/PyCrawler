# -*- coding:UTF-8  -*-
"""
尤物看板图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, net, robot, tool
import os
import re


# 获取一页图片信息列表
def get_one_page_image_info_list(page_count):
    index_url = "http://www.dahuadan.com/category/ywkb/page/%s" % page_count
    index_response = net.http_request(index_url)
    if index_response.status == net.HTTP_RETURN_CODE_SUCCEED:
        article_data = tool.find_sub_string(index_response.data, '<section id="primary"', "</section>")
        image_info_list = re.findall('<article id="post-([\d]*)"[\s|\S]*?<img class="aligncenter" src="([^"]*)" />', article_data)
        return {"is_over": False, "image_info_list": image_info_list}
    elif index_response.status == 404:
        return {"is_over": True, "image_info_list": []}
    return None


class Template(robot.Robot):
    def __init__(self):
        sys_config = {
            robot.SYS_DOWNLOAD_IMAGE: True,
            robot.SYS_NOT_CHECK_SAVE_DATA: True,
        }
        robot.Robot.__init__(self, sys_config, use_urllib3=True)

    def main(self):
        save_post_id = 1
        if os.path.exists(self.save_data_path):
            save_file = open(self.save_data_path, "r")
            save_info = save_file.read()
            save_file.close()
            save_post_id = int(save_info.strip())

        # 如果需要重新排序则使用临时文件夹，否则直接下载到目标目录
        tool.make_dir(self.image_download_path, 0)

        page_count = 1
        image_count = 1
        first_post_id = 0
        is_over = False
        while not is_over:
            log.step("开始解析第%s页日志" % page_count)

            image_info = get_one_page_image_info_list(page_count)
            if image_info is None:
                log.error(" 第%s页图片无法解析" % page_count)
                tool.process_exit()

            if image_info["is_over"]:
                break

            for post_id, image_url in image_info["image_info_list"]:
                post_id = int(post_id)
                # 检查是否图片时间小于上次的记录
                if post_id <= save_post_id:
                    is_over = True
                    break

                # 将第一张图片的post id做为新的存档记录
                if first_post_id == 0:
                    first_post_id = post_id

                log.step("开始下载%s的图片 %s" % (post_id, image_url))

                file_type = image_url.split(".")[-1]
                file_path = os.path.join(self.image_download_path, "%04d.%s" % (post_id, file_type))
                save_file_return = net.save_net_file(image_url, file_path)
                if save_file_return["status"] == 1:
                    log.step("%s的图片下载成功" % post_id)
                    image_count += 1
                else:
                    log.error("%s的图片 %s 下载失败，原因：%s" % (post_id, image_url, robot.get_save_net_file_failed_reason(save_file_return["code"])))

            page_count += 1

        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (self.get_run_time(), image_count - 1))

        # 重新保存存档文件
        save_data_dir = os.path.dirname(self.save_data_path)
        if not os.path.exists(save_data_dir):
            tool.make_dir(save_data_dir, 0)
        save_file = open(self.save_data_path, "w")
        save_file.write(str(first_post_id))
        save_file.close()


if __name__ == "__main__":
    Template().main()
