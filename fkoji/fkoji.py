# -*- coding:UTF-8  -*-
"""
fkoji图片爬虫
@author: hikaru
email: hikaru870806@hotmail.com
如有问题或建议请联系
"""
from common import log, robot, tool
from common import BeautifulSoup
import os
import time

ALL_SIGN = "_____"


class Fkoji(robot.Robot):
    def __init__(self):
        super(Fkoji, self).__init__()

        tool.print_msg("配置文件读取完成")

    def main(self):
        start_time = time.time()

        # 设置代理
        if self.is_proxy == 1 or self.is_proxy == 2:
            tool.set_proxy(self.proxy_ip, self.proxy_port, "http")

        # 图片保存目录
        log.step("创建图片根目录 %s" % self.image_download_path)
        if not tool.make_dir(self.image_download_path, 0):
            log.error("创建图片根目录 %s 失败" % self.image_download_path)
            tool.process_exit()

        # 图片下载临时目录
        if self.is_sort:
            log.step("创建图片下载目录 %s" % self.image_temp_path)
            if not tool.make_dir(self.image_temp_path, 0):
                log.error("创建图片下载目录 %s 失败" % self.image_temp_path)
                tool.process_exit()

        # 寻找fkoji.save
        account_list = {}
        if os.path.exists(self.save_data_path):
            account_list = robot.read_save_data(self.save_data_path, 0, ["", "", ""])

        # 这个key的内容为总数据
        if ALL_SIGN in account_list:
            image_start_index = int(account_list[ALL_SIGN][1])
            last_image_url = account_list[ALL_SIGN][2]
            account_list.pop(ALL_SIGN)
        else:
            last_image_url = ""
            image_start_index = 0

        if self.is_sort:
            image_path = self.image_temp_path
        else:
            image_path = self.image_download_path

        # 下载
        page_index = 1
        image_count = 1
        first_image_url = ""
        unique_list = []
        is_over = False
        while not is_over:
            index_url = "http://jigadori.fkoji.com/?p=%s" % page_index
            index_page_return_code, index_page_response = tool.http_request(index_url)[:2]
            if index_page_return_code != 1:
                log.error("无法访问首页地址 %s" % index_url)
                tool.process_exit()

            index_page = BeautifulSoup.BeautifulSoup(index_page_response)
            photo_list = index_page.body.findAll("div", "photo")
            # 已经下载到最后一页
            if not photo_list:
                break
            for photo_info in photo_list:
                if isinstance(photo_info, BeautifulSoup.NavigableString):
                    continue
                tags = photo_info.findAll("span")
                # 找account_id
                for tag in tags:
                    sub_tag = tag.next.next
                    if isinstance(sub_tag, BeautifulSoup.NavigableString):
                        if sub_tag.find("@") == 0:
                            account_id = sub_tag[1:].encode("GBK")
                # 找图片
                tags = photo_info.findAll("img")
                for tag in tags:
                    tag_attr = dict(tag.attrs)
                    if tag_attr.has_key("src") and tag_attr.has_key("alt"):
                        image_url = str(tag_attr["src"]).replace(" ", "").encode("GBK")

                        # 新增图片导致的重复判断
                        if image_url in unique_list:
                            continue
                        else:
                            unique_list.append(image_url)
                        # 将第一张图片的地址做为新的存档记录
                        if first_image_url == "":
                            first_image_url = image_url
                        # 检查是否已下载到前一次的图片
                        if last_image_url == image_url:
                            is_over = True
                            break

                        # 文件类型
                        file_type = image_url.split(".")[-1]
                        if file_type.find("/") != -1:
                            file_type = "jpg"
                        file_path = os.path.join(image_path, "%05d_%s.%s" % (image_count, account_id, file_type))
                        log.step("开始下载第%s张图片 %s"  % (image_count, image_url))
                        if tool.save_net_file(image_url, file_path):
                            log.step("第%s张图片下载成功" % image_count)
                            image_count += 1
                        else:
                            log.error("第%s张图片 %s，account_id：%s，下载失败" % (image_count, image_url, account_id))
                if is_over:
                    break

            if not is_over:
                page_index += 1

        log.step("下载完毕")

        # 排序复制到保存目录
        if self.is_sort:
            is_check_ok = False
            while not is_check_ok:
                # 等待手动检测所有图片结束
                input_str = raw_input(tool.get_time() + " 已经下载完毕，是否下一步操作？ (Y)es or (N)o: ")
                input_str = input_str.lower()
                if input_str in ["y", "yes"]:
                    is_check_ok = True
                elif input_str in ["n", "no"]:
                    tool.process_exit()

            all_path = os.path.join(self.image_download_path, "all")
            if not tool.make_dir(all_path, 0):
                log.error("创建目录 %s 失败" % all_path)
                tool.process_exit()

            file_list = tool.get_dir_files_name(self.image_temp_path, "desc")
            for file_name in file_list:
                image_path = os.path.join(self.image_temp_path, file_name)
                file_name_list = file_name.split(".")
                file_type = file_name_list[-1]
                account_id = "_".join(".".join(file_name_list[:-1]).split("_")[1:])

                # 所有
                image_start_index += 1
                destination_file_name = "%05d_%s.%s" % (image_start_index, account_id, file_type)
                destination_path = os.path.join(all_path, destination_file_name)
                tool.copy_files(image_path, destination_path)

                # 单个
                each_account_path = os.path.join(self.image_download_path, "single", account_id)
                if not os.path.exists(each_account_path):
                    if not tool.make_dir(each_account_path, 0):
                        log.error("创建目录 %s 失败" % each_account_path)
                        tool.process_exit()
                if account_list.has_key(account_id):
                    account_list[account_id][1] = int(account_list[account_id][1]) + 1
                else:
                    account_list[account_id] = [account_id, 1]
                destination_file_name = "%05d.%s" % (account_list[account_id][1], file_type)
                destination_path = os.path.join(each_account_path, destination_file_name)
                tool.copy_files(image_path, destination_path)

            log.step("图片从下载目录移动到保存目录成功")

            # 删除临时文件夹
            tool.remove_dir(self.image_temp_path)
            
        # 保存新的存档文件
        temp_list = [account_list[key] for key in sorted(account_list.keys())]
        # 把总数据插入列表头
        temp_list.insert(0, [ALL_SIGN, str(image_start_index), first_image_url])
        tool.write_file(tool.list_to_string(temp_list), self.save_data_path, 2)

        duration_time = int(time.time() - start_time)
        log.step("全部下载完毕，耗时%s秒，共计图片%s张" % (duration_time, image_count - 1))


if __name__ == "__main__":
    Fkoji().main()
